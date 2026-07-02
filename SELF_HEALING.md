# 🧠 Self-Healing Architecture — the nervous-system model

Vanguard-OOB models its detect → respond → recover loop on the **human nervous
system**, because biology already solves the exact problem a resilient SOC
faces: *sense damage, react instantly at the reflex level, escalate to the brain
for judgement, and continuously restore the body toward a healthy baseline.*

> Humans heal and cure automatically; for software systems this is harder, so
> making it explicit — as a designed framework with clear communication between
> the codes — is what makes the platform **stable, accurate, and workable**.

---

## 1. Biology → Vanguard mapping

| Biological structure | Function | Vanguard component |
|---|---|---|
| Sensory receptors (nociceptors) | sense damage/stimuli | Sensors: `sentry_agent`, `ids_engine`, `waf_engine`, blue-team tools |
| Afferent nerves | carry signals inward | `common/secure_channel.py` (authenticated telemetry) |
| **Spinal reflex arc** | instant local response, no brain wait | `self_healing/reflex_arc.py` |
| Brain / CNS | deliberate correlation + decision | `host_control_plane/control_center.py` + `self_healing/nervous_system.py` |
| Efferent nerves | carry commands outward | `EfferentCommand` on the bus |
| Effectors (muscles) | perform the action | `containment.py`, `firewall`, `failover_orchestrator.py`, healing |
| **Homeostasis** | keep vitals in a healthy range | `self_healing/health_monitor.py` |
| **Healing / regeneration** | repair damage | `self_healing/healing_orchestrator.py` |
| Immune memory | remember past threats | persisted IOCs / baselines |

---

## 2. Communication between the codes — one typed signal bus

Every module talks through **one auditable publish/subscribe bus**
(`NervousSystem`) using three typed signals, instead of ad-hoc calls. That single
design choice is what makes the whole system observable and testable.

```
 SENSORS                    NERVOUS SYSTEM BUS                  EFFECTORS
 ┌────────────┐   afferent   ┌──────────────────────┐  efferent  ┌───────────┐
 │ sentry     │─────────────▶│                      │───────────▶│containment│
 │ ids_engine │─────────────▶│   ReflexArc (fast)   │───────────▶│ firewall  │
 │ waf_engine │─────────────▶│         │            │───────────▶│ failover  │
 │ blue-team  │─────────────▶│         ▼            │───────────▶│ healing   │
 └────────────┘              │  CNS / HealingOrch.  │            └───────────┘
        ▲                    │  (deliberate)        │                 │
        │      health        └──────────┬───────────┘                 │
        │  ┌──────────────┐             │ reconcile()                 │
        └──│ HealthMonitor│◀────────────┘  homeostasis loop           │
           │ (homeostasis)│◀──────────────────────────────────────────┘
           └──────────────┘         vitals / heartbeats
```

**Signal types** (`self_healing/nervous_system.py`):
- `AfferentSignal` — something was **sensed** (detection/telemetry).
- `ReflexSignal` — a **fast local** decision fired before the CNS deliberates.
- `EfferentCommand` — a **deliberate command** to an effector.

---

## 3. The two response paths (fast reflex vs deliberate CNS)

### Reflex arc — millisecond protection (`reflex_arc.py`)
A tiny set of **unambiguous, high-confidence** signals bypass full correlation
and trigger protection immediately — just like pulling your hand off a hot stove
before your brain registers pain. Reflexes never fire on low-confidence signals.

| Trigger | Reflex action | Why it's reflex-worthy |
|---|---|---|
| `crypto_spike` (T1486) | isolate host | mass encryption leaves no doubt |
| `cred_dump` (T1003.001) | isolate host | LSASS theft precedes ransomware |
| `ransomware_esxi` (T1486) | isolate host | one host encrypts many VMs |
| `agent_silence` (T1562.001) | probe + restart sensor | a blind sensor must be healed fast |

### CNS — deliberate judgement (`control_center` + `healing_orchestrator`)
Lower-confidence signals accumulate a **server-side score**; when they cross the
isolation threshold the CNS runs full incident response + failover. This is the
slow, correct path — and where a **human analyst** stays in the loop.

---

## 4. Self-healing algorithms (homeostasis + repair)

The `HealingOrchestrator` runs a **control loop** (`reconcile()`), the same shape
as biological homeostasis and modern reconcilers:

1. **Desired-state reconciliation** — compare each component's *actual* health to
   its *desired* state; emit the corrective action. Idempotent, safe every tick.
2. **Circuit breaker** — a component that keeps failing is tripped **OPEN** so its
   failures stop cascading; after a cool-down it goes **HALF-OPEN** to probe, then
   **CLOSED** once healthy. (Prevents a healing storm.)
3. **Remediation playbooks** — `symptom → ordered cure steps`, with **exponential
   backoff + jitter** and a hard attempt cap that **escalates to a human** rather
   than looping forever (this is the 90/10 philosophy in code).
4. **Graceful degradation** — `HealthMonitor` distinguishes HEALTHY → DEGRADED →
   UNHEALTHY → DEAD, so a component can keep serving in a degraded mode instead of
   dying outright.

### Health states (`health_monitor.py`)
| State | Meaning | Typical trigger |
|---|---|---|
| HEALTHY | vitals in range, heartbeats on time | normal |
| DEGRADED | alive but a vital is out of range (CPU/mem/queue/error-rate) or 1 missed beat | overload |
| UNHEALTHY | multiple missed heartbeats | stall / partial failure |
| DEAD | prolonged silence | crash / tamper |

### Example remediation playbooks
| Symptom | Cure steps |
|---|---|
| `control_center:dead` | restart service → promote standby (failover) |
| `sentry_agent:dead` | restart sensor |
| `secure_channel:degraded` | re-key channel |
| `queue:degraded` | drain queue |

---

## 5. Why this makes the platform better

- **Stable** — one bus + a homeostatic loop means failures are contained and
  corrected instead of cascading.
- **Accurate** — reflexes handle only certainties; everything else gets deliberate,
  score-based judgement (low false-positive pressure).
- **Workable** — every signal and action is typed and audited, so an analyst can
  read exactly what the system sensed, reflexed, commanded, and healed.
- **Human-in-the-loop by design** — when automated healing hits its limit, it
  escalates to a person rather than thrashing.

---

## 6. Run it

```bash
# full self-healing loop (dry-run, safe):
PYTHONPATH=. python3 -m self_healing.runtime

# individual pieces:
PYTHONPATH=. python3 -m self_healing.reflex_arc
PYTHONPATH=. python3 -m self_healing.healing_orchestrator
PYTHONPATH=. python3 -m self_healing.health_monitor
```

Everything is stdlib-only and side-effect-free (dry-run) by default.
