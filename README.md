<div align="center">

<br/>

# 🛡️ VANGUARD‑OOB

### Out‑of‑Band Cyber Resilience — ransomware can't kill what it can't reach.

**An automation‑first SOC + Blue‑Team platform that detects modern attacks in milliseconds, contains the infected machine at the network layer, and fails the workload over to a warm standby — so the business keeps running while humans do the decisive work.**

**Version 1.1.1** · Released 2026‑07‑02 · Status: stable · Python 3.10+ · Linux / Windows / macOS

[![Version](https://img.shields.io/badge/version-1.1.1-2ea043?style=flat-square)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Channel](https://img.shields.io/badge/Channel-AES--256--GCM-00b4d8?style=flat-square&logo=letsencrypt&logoColor=white)](common/secure_channel.py)
[![MITRE ATT&CK](https://img.shields.io/badge/MITRE-28%20techniques%20mapped-ff6b35?style=flat-square)](common/mitre_attack.py)
[![Sigma](https://img.shields.io/badge/Sigma-16%20rules-9d6cff?style=flat-square)](blue_team/sigma_engine/rules/)
[![Perimeter](https://img.shields.io/badge/IDS%2FIPS%2FWAF%2FFW-built--in-ff6b35?style=flat-square)](blue_team/)
[![Self-Healing](https://img.shields.io/badge/Self--Healing-nervous%20system-9d6cff?style=flat-square)](SELF_HEALING.md)
[![Verify](https://img.shields.io/badge/verify.py-44%2F44-22c55e?style=flat-square)](verify.py)
[![Tests](https://img.shields.io/badge/pytest-41%20passing-22c55e?style=flat-square&logo=pytest&logoColor=white)](tests/)
[![Replay](https://img.shields.io/badge/attack__replay-14%2F14%20·%200%20FP-22c55e?style=flat-square)](attack_replay.py)
[![RTO](https://img.shields.io/badge/Failover%20RTO-~0.8s%20(simulated)-00c8e8?style=flat-square)](host_control_plane/failover_orchestrator.py)
[![Platform](https://img.shields.io/badge/Linux%20·%20Windows%20·%20macOS-0078d4?style=flat-square)](#-installation--running-linux-windows-macos)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

</div>

```bash
git clone https://github.com/MANISH-524/VANGUARD.git && cd VANGUARD
pip install -r requirements.txt
python3 demo.py        # watch a full ransomware kill-chain get defeated end-to-end
```

> [!IMPORTANT]
> **One command tells the whole story.** `python3 demo.py` runs a live kill‑chain — **crypto‑spike → instant network block → isolation → failover to a warm standby → self‑heal** — then prints the measured recovery time and the MITRE ATT&CK coverage report. No hypervisor, no cloud, no setup.

## ▶️ See it run

A full recording of `demo.py` — the ransomware kill‑chain defeated end‑to‑end in ~0.8 s — is in [`media/demo.cast`](media/demo.cast) (asciinema v2).

```bash
# play it in your terminal:
asciinema play media/demo.cast

# or turn it into a GIF for the README / a post:
agg media/demo.cast media/demo.gif        # https://github.com/asciinema/agg
```

> Maintainer: upload the cast to <https://asciinema.org> and drop the embed/GIF here — a 15‑second "it actually works" clip is the single biggest driver of stars.

---

## 🧭 Philosophy — save 90% by giving up 10%

> *"You can't save 100%. Chasing 100% is exactly how organisations lose almost everything. A 10–20% hit while the business stays online beats a 100% outage every single time."*

In cybersecurity **no code, no AI, no WAF, and no IDS/IPS replaces humans** — attacks are run by humans, and stopping them takes humans too. Vanguard‑OOB is built to **work with the team, not instead of it**: it detects, contains, buys time, and hands analysts a clean, ATT&CK‑mapped picture so they make the call. Automation does the millisecond reflexes; people do the judgement.

---

## ⚖️ Real vs Simulated (read this first — full honesty)

This repo is a **working reference implementation**. Detection logic, the authenticated channel, scoring, correlation, the SOC workflow, and the blue‑team tooling are **real and runnable today**. The parts that touch physical infrastructure ship as **clearly‑labelled adapters** you point at your own environment.

| Capability | Status | Notes |
|---|---|---|
| Authenticated telemetry (AES‑256‑GCM, replay + spoof protection) | ✅ **Real** | `common/secure_channel.py`, proven by `verify.py` |
| Detection engine (Sigma + scoring + ATT&CK mapping) | ✅ **Real** | 16 rules, 25 techniques, `verify.py` + `attack_replay.py` |
| SOC alert workflow (queue, lifecycle, MTTD/FP metrics) | ✅ **Real** | `blue_team/alert_correlator/` |
| Host network containment (iptables/nftables/netsh/pf) | ✅ **Real, dry‑run by default** | `host_control_plane/containment.py` — pass `--live` to apply |
| 21‑tool blue‑team suite | ✅ **Real** (depth varies — see suite table) | some tools are focused, a few marked *experimental* |
| Hypervisor isolation / snapshot rollback | 🔌 **Adapter** | `hypervisor_api.py` wraps VBoxManage + Proxmox API — wire to your host |
| Warm‑standby failover + RTO number | 🧪 **Simulated backend** | `SimulatedBackend` models realistic latency; swap for a real adapter. The `~0.8s` RTO is the simulated timeline, **not** a production benchmark |
| Guest emitters for every technique | 🚧 **Partial** | agent emits FS/proc/socket/crypto today; LSASS, PowerShell, driver‑load, cloud, etc. are validated as **detection content** and are on the emitter roadmap |

> The design deliberately separates *detection content* (real, portable, standards‑based) from *infrastructure actuators* (adapters you own). That is why one real containment path ships enabled (network) and the heavier ones ship as adapters.

---

## 🧠 Why out‑of‑band

Every security tool that runs **inside** the OS shares one fatal flaw: malware with admin rights can switch it off. Ransomware's playbook is exactly that — *kill the agent, delete the backups, encrypt everything.* And even when an infected box **is** isolated, the workload stops, so the business eats the full outage anyway.

<table>
<tr>
<td width="50%" valign="top">

#### ❌ Traditional in‑host EDR
- Runs **inside** the VM → killable by privileged malware
- Detects ransomware *after* encryption is underway
- Isolates the victim → **workload stops, business halts**
- Alerts in a vendor format nobody else speaks
- "Trust me, it works" — no proof

</td>
<td width="50%" valign="top">

#### ✅ Vanguard‑OOB
- Control plane runs **outside** the VM → malware can't reach it
- **Crypto‑spike detector** catches mass‑encryption as it starts
- Isolates **and fails over** → **workload keeps running**
- Every alert mapped to **MITRE ATT&CK** + **Sigma**
- **Proven** — 44 checks, 14/14 replay, measured MTTD, 0 FP

</td>
</tr>
</table>

> [!NOTE]
> To defeat Vanguard‑OOB an attacker must escape the VM all the way to the hypervisor — a far higher bar than killing an in‑OS agent. And killing the agent isn't a blind spot: silence past the heartbeat window is itself a detection (**T1562.001 – Impair Defenses**).

---

## 🏗️ Architecture — three separated trust planes

```
                            ┌───────────────────────────────────────────────┐
   GUEST VM (untrusted)     │             HOST CONTROL PLANE                 │
 ┌──────────────────────┐   │  ┌─────────────────────────────────────────┐  │
 │  Sentry Agent         │──┼─▶│  SecureReceiver → Correlation / Scoring   │  │
 │  (sender-only,        │AES│  │  Sigma engine · ATT&CK map · SOC queue    │  │
 │   zero listen ports)  │GCM│  └───────────────────┬─────────────────────┘  │
 └──────────────────────┘   │                       │ threat score ≥ threshold │
   authenticated,           │                       ▼                          │
   replay-protected         │  ┌─────────────────────────────────────────┐    │
                            │  │  RESPONSE                                 │    │
                            │  │  • host containment (iptables/nftables/   │    │
                            │  │    netsh/pf)  ← real, dry-run by default   │    │
                            │  │  • hypervisor isolate/dump/rollback        │    │
                            │  │    (VBox/Proxmox adapter)                  │    │
                            │  │  • warm-standby failover (RTO timeline)    │    │
                            │  └─────────────────────────────────────────┘    │
                            └───────────────────────────────────────────────┘
                                            │
                ┌───────────────────────────┴───────────────────────────┐
                ▼                                                         ▼
        WARM STANDBY (promoted → ACTIVE)                   INFECTED VM (cured → rejoins as standby)
```

- **Guest VM** runs `guest_production_vm/sentry_agent.py` — a *sender‑only* telemetry daemon with **zero listening ports**. It watches files, processes, and sockets and streams authenticated events out.
- **Host Control Plane** runs `host_control_plane/control_center.py` — receives authenticated telemetry, scores threats **server‑side (agent‑claimed scores are never trusted)**, matches Sigma rules, drives the SOC queue, and triggers response.
- **Response actuators** — network containment (real), hypervisor IR (adapter), failover (simulated backend + real orchestration logic).

---

## 🦠 The ransomware kill‑chain (what `demo.py` shows)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. BLOCK     host NIC drop in milliseconds (cut C2/exfil)    │
│ 2. ISOLATE   move VM to quarantine VLAN (hypervisor adapter) │
│ 3. DUMP      capture RAM → forensics_archive/                │
│ 4. FAILOVER  promote warm STANDBY → ACTIVE, redirect VIP     │
│              ►►►  WORKLOAD KEEPS RUNNING  (RTO ~0.8s sim)    │
│ 5. RESTORE   rollback infected disk to a clean golden image  │
│ 6. REJOIN    cured VM returns as the new STANDBY (self-heal) │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 What it detects (25 ATT&CK techniques · 16 Sigma rules)

Aligned to the techniques dominating 2024–2026 incidents: identity/credential theft, fileless execution, RMM abuse, BYOVD, hypervisor ransomware, and double‑extortion exfil.

| ATT&CK | Technique | Tactic | Vanguard signal |
|---|---|---|---|
| T1486 | Data Encrypted for Impact | Impact | crypto‑spike ≥3σ over baseline |
| T1486 | ESXi/hypervisor datastore encryption | Impact | mass `.vmdk/.vmx` write |
| T1490 | Inhibit System Recovery | Impact | `vssadmin`/backup destruction |
| T1496 | Resource Hijacking | Impact | abnormal crypto/CPU |
| T1003.001 | LSASS Credential Dumping | Credential Access | LSASS memory access |
| T1558.003 | Kerberoasting | Credential Access | SPN TGS request burst |
| T1621 | MFA Fatigue / Push Bombing | Credential Access | repeated push approvals |
| T1110 | Brute Force | Credential Access | auth failure spray |
| T1059.001 | Encoded / Obfuscated PowerShell | Execution | `-enc`, download‑cradle |
| T1027 | Obfuscated Files or Information | Defense Evasion | base64/compressed payload |
| T1059 | Command & Scripting Interpreter | Execution | shell spawn |
| T1218 | LOLBin Proxy Execution | Defense Evasion | rundll32/mshta/regsvr32 |
| T1562.001 | Impair Defenses / agent kill | Defense Evasion | heartbeat silence |
| T1036.005 | Masquerading exec path | Defense Evasion | exec from `/tmp`, temp |
| T1068 | BYOVD kernel driver load | Privilege Escalation | known‑vulnerable driver |
| T1505.003 | Web Shell | Persistence | web server spawns shell |
| T1053 | Scheduled Task/Job | Persistence | cron/schtasks add |
| T1546.003 | WMI Event Subscription | Persistence | fileless WMI consumer |
| T1136 | Create Account | Persistence | new privileged account |
| T1219 | Remote Access Software (RMM) | C2 | AnyDesk/ScreenConnect/etc. |
| T1071 / T1571 | C2 app‑layer / non‑standard port | C2 | unexpected outbound |
| T1560 | Archive Collected Data | Collection | rar/7z staging |
| T1567.002 | Exfil to Cloud Storage | Exfiltration | rclone/MEGA/S3 bulk out |
| T1078.004 | Valid Cloud Accounts | Defense Evasion | impossible travel / anomalous logon |
| T1021 | Remote Services (lateral) | Lateral Movement | RDP/SSH/SMB spread |

---

## 🧠 Self-healing — the nervous-system model

Vanguard's detect→respond→recover loop is modelled on the **human nervous system**, because biology already solves resilience: sense damage, react at the reflex level *before* the brain, escalate to the brain for judgement, and continuously restore toward a healthy baseline (homeostasis). Full write‑up in **[SELF_HEALING.md](SELF_HEALING.md)**. For the complete incident lifecycle (detect→stop→save→backup→heal→resume) tied to the actual code paths, see **[HOW_IT_WORKS.md](HOW_IT_WORKS.md)**.

| Biology | Vanguard |
|---|---|
| Sensory receptors | `sentry_agent`, `ids_engine`, `waf_engine`, blue‑team tools |
| Afferent nerves | authenticated telemetry (`secure_channel`) |
| **Spinal reflex arc** | `self_healing/reflex_arc.py` — millisecond containment on certainties |
| Brain / CNS | `control_center` + `self_healing/nervous_system.py` (typed signal bus) |
| Effectors | containment · firewall · failover · healing |
| **Homeostasis** | `self_healing/health_monitor.py` (HEALTHY→DEGRADED→UNHEALTHY→DEAD) |
| **Healing / repair** | `self_healing/healing_orchestrator.py` (reconcile + circuit breaker + playbooks) |

Self‑healing algorithms: **desired‑state reconciliation** (idempotent control loop), **circuit breaker** (trip‑open→half‑open→closed to stop cascades), and **remediation playbooks** with exponential backoff + jitter that **escalate to a human** instead of looping forever — the 90/10 philosophy in code.

```bash
PYTHONPATH=. python3 -m self_healing.runtime   # full loop, dry-run safe
```

---

## 🧱 Perimeter defense (IDS / IPS / WAF / Firewall — built‑in)

Configuration‑driven engines that plug into the same scoring + ATT&CK + response pipeline. Firewall/WAF behaviour is *configuration for your environment*; the detection logic and enforcement wiring are Vanguard's own.

| Engine | Detects | ATT&CK | Enforcement |
|---|---|---|---|
| **WAF** (`waf_engine`) | SQLi, XSS, path traversal, RCE, SSRF, JNDI/Log4Shell, scanners | T1190 / T1595 | BLOCK verdict (additive anomaly score) |
| **IDS/IPS** (`ids_engine`) | known‑bad IPs, C2 ports, port scan, host sweep, brute force, low‑jitter beacon | T1046 / T1071 / T1571 / T1110 | inline ALLOW/DROP/RESET |
| **Firewall** (`firewall`) | first‑match‑wins, default‑deny policy | — | compiles to real OS backends (iptables/nftables/netsh/pf), dry‑run default |

```bash
python3 blue_team/vanguard.py run waf_engine --test
python3 blue_team/vanguard.py run ids_engine --test
python3 blue_team/vanguard.py run firewall  --test
```

---

## 🛡️ What it prevents / does

- **Instant network containment** — on a high‑confidence signal (crypto‑spike, LSASS dump, ESXi encryption) the control plane hard‑blocks the host at the firewall layer (`iptables`/`nftables`/`netsh`/`pf`) to cut C2 and exfil, **before** full isolation. Dry‑run by default; keeps a management CIDR reachable so you never lock yourself out; every rule is reversible via `lift()`.
- **Business‑continuity failover** — promotes a warm standby so the workload survives the incident, then cures and rejoins the infected node as the new standby (self‑heal).
- **Tamper‑evident telemetry** — AES‑256‑GCM authenticated frames, per‑agent HKDF keys, replay window, and identity binding: forged, replayed, or spoofed frames are rejected.
- **Server‑side scoring** — the control plane computes every threat score itself; a compromised agent cannot talk its way to a low score.
- **Full SOC workflow** — alert queue with Open → Ack → Escalate → Close/False‑Positive, assignments, notes, and live MTTD / FP‑rate / volume metrics.

---

## ⚙️ Installation & running (Linux, Windows, macOS)

**Requirements:** Python 3.10+ and pip. Everything runs in dry‑run/simulated mode with no special privileges — perfect for demos, labs, and CI.

### Linux / macOS
```bash
git clone https://github.com/MANISH-524/VANGUARD.git && cd VANGUARD
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python3 demo.py            # full attack→defense story
python3 verify.py          # 44 correctness checks
python3 attack_replay.py   # ATT&CK coverage + MTTD + FP-rate
pytest -q                  # unit tests
```
Optional real network containment (needs root; **preview the commands first**):
```bash
python3 host_control_plane/containment.py                 # dry-run, prints exact rules
sudo python3 host_control_plane/containment.py --live --mgmt-allow 10.0.0.0/24
sudo python3 host_control_plane/containment.py --lift     # remove the rules
```
Convenience installer + systemd units:
```bash
./install_linux_mac.sh
# services: guest_production_vm/vanguard-sentry.service, host_control_plane/vanguard-control.service
```

### Windows (PowerShell)
```powershell
git clone https://github.com/MANISH-524/VANGUARD.git; cd VANGUARD
py -3 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

py demo.py
py verify.py
py attack_replay.py
pytest -q
```
Real containment on Windows uses `netsh advfirewall` (Run as Administrator, preview first):
```powershell
py host_control_plane\containment.py --force netsh            # dry-run
py host_control_plane\containment.py --force netsh --live     # applies block rules
```
Or use `install_windows.bat`.

### Production hardening (before any real deployment)
```bash
export VANGUARD_MASTER_KEY=$(python3 -c "import os;print(os.urandom(32).hex())")   # never ship the dev key
export VANGUARD_API_TOKEN=$(python3 -c "import secrets;print(secrets.token_urlsafe(24))")
python3 host_control_plane/control_center.py --api-token "$VANGUARD_API_TOKEN" --allow-ips 10.0.0.0/24
```

---

## 🧰 Blue‑Team suite (24 tools, one CLI)

Run any tool via `python3 blue_team/vanguard.py <tool>`. Depth is honest: focused tools do one job well; a few are marked *experimental*.

`threat_intel` · `threat_hunter` · `ioc_hunter` · `yara_engine` · `sigma_engine` · `log_analyzer` · `packet_inspector` · `dns_analyzer` · `network_mapper` · `memory_forensics` · `file_integrity` · `behavioral_engine` (UEBA) · `credential_monitor` · `lateral_movement_detector` · `config_auditor` · `vuln_scanner` · `deception_engine` · `honeypot_manager` · `alert_correlator` · `timeline_builder` · `reporting_engine` · `soc_dashboard` · `waf_engine` · `ids_engine` · `firewall`

---

## 📁 Repository structure

```
VANGUARD/
├── demo.py                         # one-command end-to-end story
├── verify.py                       # 44 correctness assertions
├── attack_replay.py                # ATT&CK coverage + MTTD + FP-rate
├── common/
│   ├── secure_channel.py           # AES-256-GCM authenticated telemetry (real)
│   └── mitre_attack.py             # 25-technique catalog + event→technique map
├── guest_production_vm/
│   ├── sentry_agent.py             # sender-only guest telemetry daemon
│   └── vanguard-sentry.service     # systemd unit
├── host_control_plane/
│   ├── control_center.py           # receiver, scoring, correlation, SOC, response
│   ├── containment.py              # REAL host network containment (dry-run default)
│   ├── hypervisor_api.py           # VBox/Proxmox isolation + IR adapter
│   ├── failover_orchestrator.py    # warm-standby failover (pluggable backend)
│   ├── alert_manager.py · geo_intel.py · dashboard.html
│   └── vanguard-control.service    # systemd unit
├── blue_team/                      # 24-tool suite + Sigma engine + rules/
│   ├── sigma_engine/rules/*.yml    # 16 detection rules
│   ├── waf_engine/                 # web app firewall (SQLi/XSS/RCE/SSRF/JNDI)
│   ├── ids_engine/                 # network IDS/IPS (scan/beacon/brute/known-bad)
│   └── firewall/                   # config-driven policy → OS enforcement
├── self_healing/                   # nervous-system model (see SELF_HEALING.md)
│   ├── nervous_system.py           # typed signal bus (afferent/reflex/efferent)
│   ├── reflex_arc.py               # spinal-level fast containment
│   ├── health_monitor.py           # homeostasis / vitals / watchdog
│   ├── healing_orchestrator.py     # reconcile + circuit breaker + playbooks
│   └── runtime.py                  # wires the whole loop together
├── tests/                          # pytest suite (36 tests)
├── HOW_IT_WORKS.md                 # full lifecycle: detect→stop→save→heal→resume
├── LAUNCH.md                       # discoverability + launch kit
├── media/demo.cast                 # asciinema recording of demo.py
├── DEFENSE_GUIDE.md                # defend every module out loud
├── SELF_HEALING.md                 # nervous-system self-healing framework
├── VERSION · pyproject.toml        # single-source version + packaging
└── .github/workflows/ci.yml        # conflict gate + compile + verify + replay + pytest
```

---

## 🗺️ Roadmap

- **Guest emitters** for LSASS, PowerShell, driver‑load, RMM, cloud‑auth, WMI persistence (detection content already validated).
- **Real failover adapter** (Keepalived/HAProxy or cloud LB) behind the existing `FailoverBackend` interface.
- **Sigma community‑rule ingestion** so analysts drop in the public rule corpus unchanged.
- **Sigma temporal/aggregation** support (count‑by, near) for correlation rules.
- **Stateful UEBA baselines** persisted across restarts.

---

## 🔒 Design principles

- **Standards for detection, proprietary for logic.** Sigma / YARA / ATT&CK are standards, not tools to hide — being compatible lets the whole SOC ecosystem plug in. The *value* is in Vanguard's correlation, scoring, out‑of‑band placement, and failover orchestration.
- **Never roll your own crypto.** The channel uses the vetted `cryptography` library's AES‑GCM.
- **Fail safe.** Containment is dry‑run by default and reversible; the control plane warns loudly if the public dev key or no API token is in use.

---

## 🏷️ Versioning

**Current release: `v1.1.0`** (2026‑07‑02) — adds the biologically‑inspired **self‑healing** subsystem and the built‑in **IDS/IPS/WAF/Firewall** perimeter engines. 44/44 correctness checks, 36 unit tests, 14/14 ATT&CK replay with 0 false positives, 16 Sigma rules across 28 techniques.

The version is defined once in [`VERSION`](VERSION) and exposed as `common.__version__`:
```python
import common
print(common.__version__)   # 1.1.0
```
Vanguard‑OOB follows [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`. See [CHANGELOG.md](CHANGELOG.md) for the full history.

| Version | Date | Highlights |
|---|---|---|
| **1.1.0** | 2026‑07‑02 | Self‑healing nervous‑system subsystem; IDS/IPS/WAF/Firewall engines; pip packaging (`vanguard` CLI); 28 techniques; 36 tests |
| **1.0.0** | 2026‑07‑02 | Merge conflicts resolved; real cross‑platform containment; 16 Sigma rules / 25 ATT&CK techniques; CI conflict gate; honest Real‑vs‑Simulated docs |

---

## 📜 License

MIT — see [LICENSE](LICENSE).

<div align="center">
<sub>Built to work <b>with</b> the team, not instead of it. Detect fast, contain faster, keep the business alive, let humans decide.</sub>
</div>
