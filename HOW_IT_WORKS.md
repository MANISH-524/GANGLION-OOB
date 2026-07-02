# ⚙️ How Vanguard-OOB Works — the full lifecycle

This document traces one incident end-to-end through the **actual code paths**, so
anyone can follow exactly how the system **detects → stops → saves → backs up →
heals → resumes with the same strength**. It also explains the design vision: a
resilience *substrate* that workloads (and AI systems) run on and depend on.

---

## 0. The one-sentence model

> A sender-only sensor inside the workload streams **authenticated** telemetry to
> an **out-of-band** brain the malware can't reach; the brain **scores** the threat
> itself, fires an **instant reflex** to cut the danger, runs **incident response +
> backup**, **fails the workload over** to a warm standby so the business never
> stops, then **heals** the infected node and returns it to duty at full strength.

Nothing the workload does can disable the brain, because the brain lives outside
the workload's trust boundary. That is the whole idea.

---

## 1. The pipeline at a glance

```
 SENSE ─▶ AUTHENTICATE ─▶ SCORE ─▶ REFLEX(stop) ─▶ IR+BACKUP(save) ─▶ FAILOVER(keep running)
   │           │            │          │                │                     │
 sentry    secure_       control_   reflex_arc /     hypervisor_api      failover_
 _agent    channel       center     instant_block    (isolate/dump/      orchestrator
 ids/waf   (AES-GCM)     (server-    + containment    restore)            (promote standby)
                          side)       .py                                        │
                                                                                 ▼
                                                              HEAL ─▶ REJOIN(same strength)
                                                       healing_orchestrator / restore_snapshot
```

Each stage below names the file and function that does the work.

---

## 2. DETECT — how it senses

**Sensors (afferent receptors).** Three independent sources feed the brain:

| Sensor | File | Watches for |
|---|---|---|
| Guest agent | `guest_production_vm/sentry_agent.py` | file entropy/velocity (ransomware), suspicious process exec, shadow-copy deletion, unexpected sockets |
| Network IDS/IPS | `blue_team/ids_engine/ids_engine.py` | known-bad IPs, C2 ports, port scans, host sweeps, brute force, low-jitter beacons |
| Web WAF | `blue_team/waf_engine/waf_engine.py` | SQLi, XSS, path traversal, RCE, SSRF, JNDI/Log4Shell, scanners |

The guest agent is **sender-only with zero listening ports** — it can talk out
but nothing can talk in, which shrinks its own attack surface to almost nothing.

**Why detection is trustworthy.** Every event is mapped to **MITRE ATT&CK**
(`common/mitre_attack.py → map_event_to_techniques`) and matched against
**Sigma rules** (`blue_team/sigma_engine/`). Two independent opinions (behavioral
score + signature rule) must line up before a high-confidence verdict.

---

## 3. AUTHENTICATE — why the telemetry can't be forged

Telemetry travels over `common/secure_channel.py`:

- **AES-256-GCM** authenticated encryption — a forged or tampered frame fails the
  authentication tag and is dropped.
- **Per-agent HKDF-derived keys** — one compromised agent key can't impersonate another.
- **Replay window + monotonic sequence** — a captured frame replayed later is rejected
  (the `OrderedSet`/`deque` replay cache in `secure_channel.py`).
- **Identity binding** — the frame's claimed source must match its key.

Result: the brain trusts *what it receives* because the channel proves origin and
integrity. (`verify.py` asserts all of this — tamper, replay, and spoof are tested.)

---

## 4. SCORE — the brain decides, not the agent

In `host_control_plane/control_center.py`:

- `_resolve_delta(event_type, details)` assigns the **authoritative** score for
  each event. **The agent's own claimed score is never trusted** — a compromised
  agent cannot talk its way to "harmless."
- Scores accumulate per-VM in a rolling time window (`recalculate_score`), so a
  slow, multi-step attack still crosses the threshold as evidence stacks up.
- Two thresholds drive action:
  - `INSTANT_BLOCK_TYPES` — unambiguous signals (mass encryption, LSASS dump,
    ESXi encryption) that skip the queue entirely.
  - `ISOLATION_THRESHOLD` — the cumulative score that triggers full response.

---

## 5. STOP — the reflex (millisecond containment)

Two things happen *fast*, before deliberation finishes:

1. **Spinal reflex** (`self_healing/reflex_arc.py`): a high-confidence afferent
   signal is turned straight into an `EfferentCommand` to isolate — no waiting for
   the full correlation pass, exactly like pulling your hand off a stove.
2. **Instant block** (`control_center._instant_block`): fires two containment
   actions in parallel:
   - **Hypervisor NIC block** (`hypervisor_api.block_network`) — cuts the VM's
     virtual NIC at the host layer.
   - **Host network containment** (`host_control_plane/containment.py`) — drops
     traffic with iptables/nftables/netsh/pf, **keeping a management CIDR reachable**
     so responders aren't locked out, and **fully reversible** via `lift()`.

This is what cuts C2 and exfil in milliseconds — the "STOP" that buys time for
everything else.

---

## 6. SAVE + BACKUP — preserve evidence and a clean image

`hypervisor_api.full_incident_response(vm_id)` runs the out-of-band IR sequence:

| Step | Method | Purpose |
|---|---|---|
| Isolate | `isolate_vm` | move VM to a quarantine VLAN |
| **Save (memory)** | `dump_memory` | capture live RAM to `forensics_archive/` for analysis before it's lost |
| **Backup (clean image)** | golden-snapshot reference | the known-good baseline to restore from |
| Restore | `restore_snapshot` | roll the infected disk back to the clean golden image |

Because this runs at the hypervisor layer, **malware inside the VM cannot stop the
memory dump or the rollback** — it has no reach there.

---

## 7. KEEP RUNNING — failover so the business never stops

This is the "save 90% by giving up 10%" core. `failover_orchestrator.py`:

- `handle_compromise(vm_id)` **promotes a warm standby to ACTIVE** and redirects
  the service VIP to it. The workload keeps serving while the infected node is
  being cured.
- The pluggable `FailoverBackend` interface means you wire this to real infra
  (Keepalived/HAProxy, a cloud LB, etc.); the shipped `SimulatedBackend` models
  realistic per-step latency (the `~0.8s` RTO is the **simulated** timeline).

So instead of "isolate the victim and eat a full outage," the service degrades by
a fraction and stays online.

---

## 8. HEAL — recover to the same strength (self-healing)

`self_healing/healing_orchestrator.py` runs a homeostatic control loop
(`reconcile()`), the biological "restore toward a healthy baseline":

1. **Desired-state reconciliation** — compare each component's actual health
   (`health_monitor.py`) to its desired state; emit the corrective action. Idempotent.
2. **Circuit breaker** — a component that keeps failing is tripped OPEN to stop a
   cascade, then HALF-OPEN to probe recovery, then CLOSED once healthy.
3. **Remediation playbooks** — `symptom → cure` (restart service, re-key channel,
   drain queue, promote standby, restore snapshot) with exponential backoff + jitter.
4. **Human escalation** — if healing hits its attempt cap, it **escalates to a person**
   instead of thrashing (the 90/10 philosophy in code).

The cured node then **rejoins as the new standby** — the pair is whole again,
at **full strength**, ready for the next event. The cycle is symmetric: whoever was
standby is now active, whoever was infected is now the clean standby.

---

## 9. AGAIN, WITH THE SAME STRENGTH — why it's stable over time

- **No degradation after an incident**: the infected node is restored from the
  golden image, not patched in place, so it returns byte-for-byte clean.
- **Symmetric roles**: active/standby simply swap; capacity is preserved.
- **Homeostasis keeps components in range** (HEALTHY→DEGRADED→UNHEALTHY→DEAD), so
  the platform self-corrects drift instead of accumulating it.
- **One typed signal bus** (`self_healing/nervous_system.py`) means every part
  communicates through auditable messages — the system stays observable and
  predictable no matter how many sensors/effectors you add.

---

## 10. The vision — a resilience *substrate* (the "harness / transformer" idea)

The goal is not "another EDR." It's a **foundation layer that workloads run on and
depend on for survival** — the way modern AI stacks depend on a few load-bearing
primitives. A workload (including an AI service) sits *inside* the protected VM;
Vanguard is the out-of-band nervous system that keeps it alive:

```
        ┌─────────────────────────────────────────────┐
        │              PROTECTED WORKLOAD              │   ← app / AI service / DB
        │   (runs normally, unaware of the harness)    │
        └───────────────────┬─────────────────────────┘
                            │ authenticated telemetry (afferent)
        ┌───────────────────▼─────────────────────────┐
        │            VANGUARD-OOB SUBSTRATE            │   ← the "harness"
        │  sense → score → reflex → save → failover →  │
        │  heal → rejoin   (out-of-band, tamper-proof) │
        └─────────────────────────────────────────────┘
```

### Toward hardware embedding (roadmap)
The design is deliberately friendly to a **hardware/firmware split** so the brain
can be *hardcoded and physically isolated* from the workload:

- Run the control plane on a **separate SoC / management coprocessor / SmartNIC /
  BMC**, not the same CPU as the workload — so even a full host compromise can't
  reach it.
- Burn the agent's identity key into a **TPM / secure element**, so keys can't be
  extracted by software.
- Implement containment on the **NIC/switch** (SmartNIC or an out-of-band port),
  so the network cut happens in silicon, independent of the host OS.
- Keep detection content (Sigma/ATT&CK) in software (updatable), keep the trust
  root and enforcement in hardware (immutable). *Standards for detection,
  hardware for the trust boundary.*

That combination — updatable brains, immutable trust root — is the unique,
defensible position this prototype is aiming at.

---

## 11. Prove it yourself

```bash
python3 demo.py            # the whole lifecycle, narrated
python3 verify.py          # 44 correctness assertions (crypto, replay, scoring, ...)
python3 attack_replay.py   # ATT&CK coverage + MTTD + false-positive rate
pytest -q                  # 41 unit tests incl. hardening/robustness
PYTHONPATH=. python3 -m self_healing.runtime   # the self-healing loop, dry-run
```

Every number in the README is produced by one of these — run them and watch.
