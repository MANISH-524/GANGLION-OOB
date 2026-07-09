# Changelog

## [3.7.1] — 2026-07-09 — documentation consolidated into a single README

### Changed
- **All documentation merged into one `README.md`** with a 22-entry clickable
  Table of Contents (explicit HTML anchors, so every link resolves on GitHub).
  Folded in and then removed as separate files: `HOW_IT_WORKS.md`,
  `DEFENSE_GUIDE.md`, `SELF_HEALING.md`, `SECURITY.md`, and `blue_team/README.md`.
  The repo now carries just two docs — `README.md` (everything, navigable) and
  `CHANGELOG.md` (history) — fewer files, one place to read. Every section has a
  "Back to top" link. No code changed; 44/44 verify, 89/89 tests, 14/14 replay.

## [3.7.0] — 2026-07-09 — STIX + SBOM + fuzzing; audit-path bug fixed

### Fixed — real bug from external review
- **Audit-log path is now cwd-independent.** The default was a bare relative
  path, so launching the control plane from inside `host_control_plane/` silently
  wrote the "court-defensible" trail to the wrong place (a doubled
  `host_control_plane/host_control_plane/forensics_archive/`). The path is now
  anchored to the repo via `Path(__file__)`, honors `GANGLION_AUDIT_PATH`, and is
  always absolute. Writing a forensic log to the wrong path is worse than failing,
  so this is fixed at the root. Regression test added.
- **Packaging:** `hypervisor_config.json` / `.example.json` are included in the
  release archive again (a prior over-broad zip exclude had dropped them).

### Added — standards-format exports (pairs with the ATT&CK Navigator layer)
- **STIX 2.1 bundle export** (`common/stix_export.py`): emits attack-patterns +
  indicators + relationships with deterministic UUIDv5 ids and MITRE external
  references — importable into OpenCTI, MISP, Sentinel, TheHive. `ganglion
  stix-export` / `/api/stix`.
- **CycloneDX 1.5 SBOM** (`common/sbom.py`): supply-chain bill of materials with
  resolved dependency versions and PURLs. `ganglion sbom`.

### Added — quality engineering
- **Parser fuzzing** (`tests/fuzz_parsers.py`): throws 10k+ random/adversarial
  inputs at the hand-written `safe_eval` and Sigma condition parsers and asserts
  they only ever return a bool or reject cleanly — never crash, hang, or
  mis-parse. Verified across multiple seeds with zero findings; a bounded run is
  wired into the test suite.

### Notes
- 44/44 verify, 89/89 tests (5 new), 14/14 replay, fuzzing clean, both modes green.
## [3.6.0] — 2026-07-09 — ATT&CK Navigator export + review polish

### Added — ATT&CK Navigator layer export
- New `common/attack_navigator.py`: exports Ganglion's detection coverage as a
  valid **MITRE ATT&CK Navigator layer** — the JSON the official Navigator tool
  (mitre-attack.github.io/attack-navigator) consumes. Two modes:
  *coverage* (everything Ganglion can detect) and *live* (techniques observed
  this session, scored by frequency). A blue-teamer loads it and instantly sees
  the engagement painted on the real ATT&CK matrix.
- Exposed via `ganglion attack-layer [out.json]` (CLI) and
  `/api/attack-layer?mode=coverage|live` (download).

### Fixed — from two external SOC/blue-team reviews
- **Dashboard escaping is now total, not selective.** The remaining
  server-enumerated fields (`col.tactic`, `s.state`, `a.status`, decision verdict)
  now go through `esc()` too — the rule is now "everything in innerHTML is
  escaped," closing the reviewers' consistency gap.
- **Audit log now hard-fails on a corrupt tail** instead of silently restarting
  the chain from genesis — a truncation/corruption can no longer be quietly
  "recovered." Raises `AuditIntegrityError`; override with
  `GANGLION_AUDIT_ALLOW_RESET=1` for non-forensic/dev use.
- **Deception-engine false positive removed.** The honeypot breadcrumb's fake
  "TODO" (intentional attacker bait) is now assembled at runtime with a clear
  comment, so static scanners stop flagging it while the attacker still sees the
  convincing lure. No real TODO/FIXME remain in source.

### Notes
- 44/44 verify, 84/84 tests (5 new), 14/14 replay, both modes green.

## [3.5.0] — 2026-07-09 — official Sigma import + tamper-evident decision audit log

Two substantial, fully-built and tested capabilities that make Ganglion stand
apart from typical SOC repos — built properly, not stubbed.

### Added — Official Sigma community-rule compatibility
- Upgraded the Sigma engine to the **full official modifier set**: `contains`,
  `startswith`, `endswith`, `re`, `cidr`, `base64`/`base64offset`, `windash`,
  `cased`, `exists`, and numeric `lt/lte/gt/gte`, plus correct compound modifiers
  (`contains|all`, `windash|contains`, …). This removes the "custom parser drift"
  concern from external reviews — real SigmaHQ rules now evaluate field-by-field.
- New `SigmaEngine.load_community_rules(path)` — recursively ingests a SigmaHQ
  clone and returns a **compatibility report** (scanned/loaded/skipped + reasons),
  so you can prove exactly how many community rules this engine accepts.
- Verified: real-format rules (LSASS/comsvcs `contains|all`, encoded PowerShell,
  high-port C2 with a `not filter` CIDR exclusion) load and fire correctly.

### Added — Tamper-evident decision audit log (DFIR chain-of-custody)
- New `common/audit_log.py`: every decision (MONITOR/ALERT/CONTAIN/FAILOVER/
  HEAL/ESCALATE) is appended to a **hash-chained, HMAC-signed** JSONL log. Any
  edit, deletion, reordering, or forged entry is detectable — proven by tests.
- Wired into the control plane: verdict changes are logged live with their exact
  inputs and the human-readable explanation that produced them.
- Verify three ways: `ganglion audit-verify [path]` (CLI), `/api/audit` (live
  integrity check + trail), or `python -m common.audit_log --verify <file>`
  (offline). Set `GANGLION_AUDIT_KEY` (hex) to enable signatures.
- This pairs with the no-ML decision engine: every automated action is both
  **explainable** (why) and **cryptographically provable** (untampered) — a
  glass-box SOC audit trail.

### Notes
- The runtime `decisions.jsonl` is git-ignored (per-deployment forensic artifact).
- 44/44 verify, 79/79 tests (12 new), 14/14 replay, both modes green.

## [3.4.0] — 2026-07-09 — security review fixes (stored XSS + hardening)

Addresses findings from two independent SOC/blue-team code reviews.

### Fixed — Red flags
- **Stored XSS in the SOC dashboard (the one real vulnerability).** Alert titles,
  assignees, notes, vm_ids, IPs and event-detail fields were interpolated into
  `innerHTML` unescaped. `assignee`/notes come from POST bodies and `vm_id` comes
  off the agent wire, so a rogue agent or token-holder could plant
  `<img src=x onerror=...>` that runs for every analyst who loads the dashboard.
  - Added an `esc()` HTML-escape helper and applied it to **every** dynamic field
    that reaches the DOM.
  - `vm_id` is now **sanitized server-side** at the boundary to a hostname charset
    `[A-Za-z0-9._-]` (≤64 chars) — closes the injection at the source, across
    every context (DOM text, attributes, DOM ids), independent of client escaping.
  - Added a strict **Content-Security-Policy** plus `X-Content-Type-Options`,
    `X-Frame-Options: DENY`, and `Referrer-Policy` on the dashboard response.
- **Proxmox `verify_ssl` now defaults to `true`** (was `false`) — matches the
  project's fail-safe posture; set it false only for lab self-signed certs.

### Fixed — Minor bug the reviewers flagged
- Removed dead no-op code in `common/safe_eval.py` `_tokenize()` (an
  `if ...: pass` branch that did nothing). Tokenizer behavior unchanged; verified.

### Added
- Loud startup warning when the dashboard binds to a non-localhost address,
  since `/api/status` is read-only but unauthenticated (info-disclosure honesty).
- `TestXSSHardening` regression tests: vm_id sanitization, dashboard escaping,
  and presence of the CSP header.

## [3.3.0] — 2026-07-09 — isolation honesty: never claim containment that didn't happen

### Fixed (the important one)
- **The dashboard used to show "ISOLATED" even when the isolation actually
  failed.** `_trigger_isolation` set `status="ISOLATED"` *before* calling the
  hypervisor and never checked the result — so on a machine with no VBoxManage/
  virsh (e.g. a laptop demo), all 4 IR steps failed (`0/4 succeeded`) yet the UI
  proudly claimed the VM was contained. That was misleading. Now:
  - A new `isolation_enforced` flag is set **only if a real containment step
    succeeded** (network isolate/block, or a non-dry-run host firewall rule).
  - Status shows green **`ISOLATED`** only when enforcement truly happened.
  - When the decision fires but nothing enforced it, status is
    **`QUARANTINE • UNENFORCED`** and the card shows the exact reason: detection
    and decision are real; the network cut needs a VM/hypervisor host.
  - The API exposes `isolation_enforced` + `isolation_detail` so the truth is
    machine-readable too.
- **Removed fake "work" delays.** `full_incident_response` used to `time.sleep`
  ~9s "waiting for the network to settle" even when every step had already failed
  instantly (no hypervisor). It now only waits after a step that actually
  succeeded — a failed sequence returns immediately instead of pretending.

### Added
- `TestIsolationHonesty`: regression tests proving the dashboard reports
  `ISOLATED` only when enforcement succeeds and `QUARANTINE_UNENFORCED` otherwise.
- README honesty section documents the two-truths model (intent vs enforcement).

## [3.2.1] — 2026-07-08 — full audit: both modes verified, dead files removed

### Verified in a clean environment
- **Realtime mode**: control plane + live authenticated attacks across multiple VMs
  and attack types — detection, scoring, decisions (contain/alert), and isolation
  all confirmed via the dashboard API.
- **Demo/simulation mode**: `demo.py` completes the full kill-chain (RTO ~0.8 s);
  `attack_replay.py` reports 14/14 detected, zero false positives.
- **All 27 blue-team tools** run their self-tests successfully.
- 44/44 verify, 67/67 tests, conflict-gate clean, GANGLION banner, zero old-name.

### Removed (dead / stale / broken)
- `media/demo.cast` — stale asciinema recording that still played the OLD banner
  when viewed. The current `media/demo.gif` (embedded in the README) replaces it.
- `scripts/make_cast.py` — could not regenerate the cast (it hangs on `demo.py`,
  which waits for Ctrl+C) and was unreferenced by any code.
- `LAUNCH.md` — v1.1-vintage discoverability notes that referenced the removed cast.
- `RELEASE_NOTES_v1.1.1.md` — stale single-release notes; the CHANGELOG covers all.
- README "See it run" and structure diagram updated; no dangling references remain.
## [3.2.0] — 2026-07-08 — one-click launchers

### Added
- **`run.bat` (Windows) and `run.sh` (Linux/macOS): true one-click launchers.**
  The existing install scripts only installed dependencies — they never started
  anything, which is why "the launch script didn't work." These new launchers
  install deps if needed, start the control plane, open the dashboard in the
  browser, and fire sample attacks so the dashboard populates with live detections
  immediately. Verified end-to-end: launcher brings the VM to score=115, isolated,
  decision=contain, with alerts flowing.
- README and the Windows installer now point at the launchers as the fastest path.

### Notes
- All prior fixes retained: GANGLION ASCII banner, dashboard action buttons work
  from localhost, JSON API errors, no old-name references anywhere.
## [3.1.3] — 2026-07-08 — ASCII banner rebrand + dashboard action buttons

### Fixed
- **The ASCII-art banner still spelled the OLD project name** in `demo.py`,
  `test_harness.py`, and `deploy.sh`. Text search never caught it because the
  banner is drawn with box-drawing characters, not letters. Replaced all three
  with a "GANGLION" banner. This was the "old name is still there" that a text
  grep kept reporting as clean.
- **Dashboard "Unexpected token '<' ... is not valid JSON" error** when clicking
  Isolate/Restore. Cause: `abort(401/403)` returned Flask's HTML error page, which
  the dashboard's `fetch().json()` could not parse. Added JSON error handlers so
  every API error is JSON.
- **Isolate/Restore/alert action buttons were rejected as unauthenticated.**
  Localhost (127.0.0.1/::1) is now trusted for state-changing actions — the local
  operator can already run commands on the box — so the buttons work with zero
  token friction. Remote callers still require the API token.
- Corrected the startup log line that wrongly said the dashboard injects the
  token automatically.

### Guard
- Added an ASCII-art banner check to the test suite so a stale box-character
  banner can't silently ship again.
## [3.1.2] — 2026-07-07 — dashboard fix + hardening

### Fixed
- **Live dashboard showed all zeros / no real-time detection.** Root cause:
  unresolved Git merge-conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) were
  sitting inside `dashboard.html`'s `<script>` block, which is a JavaScript
  syntax error — the browser aborted the entire script, so the 1-second poll
  loop never ran and nothing rendered. Resolved both conflict blocks; verified
  end-to-end that the dashboard API returns live VM state, scores, decisions,
  and alerts after an attack.
- The CI/verify conflict-marker gate previously scanned only a whitelist of
  extensions (missed `.html`). It now scans **all** files, and a new test
  (`TestNoConflictMarkers`) fails the suite on a conflict marker in any file.

### Added
- `fire_attack.py` bundled into the repo — fire a single named attack
  (ransomware, cred_dump, lolbin, c2_beacon, webshell, heartbeat) at a running
  control plane to watch the dashboard update live.
- Test guaranteeing the old project name is fully absent from all code/config.

## [3.1.1] — 2026-07-07

### Changed
- Project name finalized as **Ganglion-OOB**. "Ganglion" (a cluster of nerve cells
  that relays and processes signals) matches the project's nervous-system
  architecture (`reflex_arc.py`, `health_monitor.py`, `healing_orchestrator.py`).
- All modules, filenames, environment variables (`GANGLION_MASTER_KEY`,
  `GANGLION_API_TOKEN`), the CLI (`ganglion_cli.py` / `ganglion` console script),
  service files, install scripts, and docs use the name consistently.
- No behavior changed: 44/44 verify, 64/64 tests, 14/14 replay all pass.

### Fixed
- `demo.py` now loads its test harness by absolute path (robust to Windows/cloud
  folder path quirks) instead of relying on `sys.path`.
- Windows quickstart uses `python` (not `py`/`python3`) with PowerShell-correct
  env-var syntax.

## [3.1.0] — 2026-07-02 — decision engine wired live + reachability tooling

### Added
- **Decision engine integrated into the control plane**: `process_batch` now runs
  the deterministic engine on every scored event, stores the explainable decision
  (verdict + fired rules + weights) on the VM state, and exposes it via the status
  API so the dashboard can show *why* each action was taken.
- **Blast-Radius / Reachability Mapper** (`blue_team/blast_radius/`) — deterministic
  BFS over a declared trust graph; finds what a compromise can reach, scores the
  weighted blast radius, and maps it to `asset_criticality` for the decision engine
  (a compromise that can reach a crown jewel biases toward FAILOVER/CONTAIN). Tool #26.

### Fixed
- Decision integration used a score-derived severity that masked a single critical
  reflex signal (ransomware decided ALERT instead of CONTAIN). Now uses the highest
  actual event severity in the rolling window, so hard safety gates fire correctly.

### Tests
- +6 tests (64 total): live decision wiring + blast-radius mapper.

## [3.0.0] — 2026-07-02 — deterministic decision engine + deep security hardening

The "unique, non-AI" release: an explainable decision engine instead of a model,
plus a hardening pass that removes eval entirely and clears the static scan.

### Added
- **Deterministic Decision Engine** (`decision_engine/`) — a transparent, rule-based
  expert system that chooses MONITOR/ALERT/CONTAIN/FAILOVER/HEAL/ESCALATE and
  explains every decision (fired rules + weights). No ML, no training, no drift.
  Hard safety gates + weighted rules + thin-margin escalation to a human.
- **Kill-Chain Reconstructor** (`blue_team/killchain_reconstructor/`) — orders
  detections into the ATT&CK tactic progression and scores chain completeness
  (deeper chain ⇒ more decisive response). 25th blue-team tool.
- **`common/safe_eval.py`** — a hand-written, no-eval boolean/numeric parser.
- **SECURITY.md** + reviewed **`.bandit-baseline.json`**.

### Security (elimination, not suppression)
- **Removed `eval()` entirely** from the Sigma and YARA condition engines; both now
  use `safe_eval_bool`. There is no eval sandbox to escape (B307: 0).
- Server sockets default to **127.0.0.1** (was 0.0.0.0) in the correlator/honeypot.
- Fingerprint hashes marked `usedforsecurity=False` (MD5/SHA1 → not security use).
- Canary temp dir via `tempfile`; generated script perms tightened to `0o700`.
- Documented reviewed false positives (detection signatures, audit targets, CIDR
  match strings) in the bandit baseline rather than hiding them.

### Tests
- +12 tests (58 total): decision engine, kill-chain, safe_eval escape-rejection.

### Note
Major version bump to 3.0.0: the decision engine changes how responses are chosen.

## [1.2.1] — 2026-07-02 — security hardening (external audit fixes)

### Security
- **yara_engine**: closed an `eval()` sandbox-escape path. YARA rule conditions
  from untrusted feeds could reach `__subclasses__`-style introspection despite the
  emptied `__builtins__`. Added a strict whitelist gate (matching the sigma engine)
  that rejects any non-boolean/numeric expression BEFORE eval. (RCE-class fix.)
- **control_center dashboard**: the API token is no longer embedded in the served
  page, and `/` is rendered as a plain `Response` (no `render_template_string`,
  removing the SSTI footgun). The operator now supplies the token in the browser
  (prompted once, kept in sessionStorage), so merely loading the page grants no
  ability to call protected endpoints.

### Fixed / honesty
- README technique count corrected to 28 everywhere (was 25 in the header/structure).
- Added an explicit note that some Sigma rules are event-type routers, not
  independent field-level detections.
- False-positive rate reported honestly as "N/M benign control case(s)".
- Pinned `cryptography` (`>=42,<45`) — the security-critical dependency.

### Tests
- +3 regression tests for the YARA eval gate (48 total).

## [1.2.0] — 2026-07-02 — real libvirt enforcement (non-simulated)

### Added
- **`host_control_plane/libvirt_backend.py`** — the first *non-simulated* enforcement
  adapter. Real KVM/QEMU out-of-band actions via the libvirt Python API (or `virsh`
  fallback), **dry-run by default**:
  - `isolate_vm` (NIC detach), `restore_nic`, `snapshot`, `revert`, `dump_memory`,
    `domain_state`, and a `full_incident_response` sequence.
  - `LibvirtFailoverBackend` — a genuine `FailoverBackend` (promote/redirect/health/
    rejoin) driven by libvirt domain start/stop; drop-in for `SimulatedBackend`.
- **`scripts/real_failover_demo.py`** — end-to-end real-path failover demo (dry-run
  safe; `--live` executes on a KVM host). Filmable "one real deployment" story.
- **5 tests** (45 total) covering the libvirt backend and orchestrator drop-in.

### Changed
- README Real-vs-Simulated table: failover and hypervisor isolation now marked
  **Real (KVM)** with the libvirt adapter; simulated backend retained for zero-infra demos.
- Version 1.1.1 → 1.2.0.

## [1.1.1] — 2026-07-02 — hardening + lifecycle docs

### Fixed
- `ioc_hunter`: removed a duplicate magic-bytes dict key (`b"MZ"` == `b"\x4d\x5a"`) that silently shadowed a value.
- Cleaned unused imports across the new self-healing and perimeter modules (lint-clean).

### Added
- **HOW_IT_WORKS.md** — full incident lifecycle (detect→stop→save→backup→heal→resume) tied to real code paths, plus the resilience-substrate / hardware-embedding vision.
- **5 robustness tests** (41 total): engines survive malformed/empty input, the signal bus survives a faulty subscriber, and the healing loop escalates to a human instead of looping forever.

## [1.1.0] — 2026-07-02 — self-healing + perimeter engines

### Added
- **Self-healing subsystem** (`self_healing/`) modelled on the human nervous
  system: a typed signal bus (`nervous_system.py`), a spinal **reflex arc** for
  millisecond containment on high-confidence signals, a **homeostasis** health
  monitor (HEALTHY→DEGRADED→UNHEALTHY→DEAD), and a **healing orchestrator** with
  desired-state reconciliation, a circuit breaker, and remediation playbooks that
  escalate to a human. Full write-up in `SELF_HEALING.md`.
- **Perimeter defense engines** (config-driven, plugged into the ATT&CK pipeline):
  - `blue_team/waf_engine` — SQLi/XSS/path-traversal/RCE/SSRF/JNDI request inspection (T1190/T1595)
  - `blue_team/ids_engine` — signature + anomaly network IDS/IPS: known-bad IPs, C2 ports, port scan, host sweep, brute force, low-jitter beacon (T1046/T1071/T1571/T1110)
  - `blue_team/firewall` — first-match-wins default-deny policy compiling to the OS containment backends
- **pip packaging**: `pyproject.toml` + `ganglion` console entry (`ganglion verify|replay|demo|blue`).
- **3 ATT&CK techniques** (28 total): T1190, T1046, T1595; Reconnaissance tactic (TA0043).
- **14 new unit tests** (36 total) covering WAF, IDS/IPS, firewall, and self-healing.

### Changed
- Version 1.0.0 → 1.1.0 (single source of truth: `VERSION` + `common.__version__`).
- README: self-healing + perimeter sections, updated structure, version table, badges.

## [1.0.0] — 2026-07-02 — first stable release (resilience + modern-threat detection)

### Fixed
- Resolved committed Git merge-conflict markers that made `secure_channel.py`,
  `sentry_agent.py`, and `control_center.py` unparseable on `main`.

### Added
- **Real host network containment** (`host_control_plane/containment.py`):
  iptables / nftables / netsh / pf backends, **dry-run by default**, reversible
  `lift()`, management-CIDR carve-out, and an auditable action log. Wired into
  the control plane's instant-block path.
- **10 new Sigma detection rules** (16 total) for current threats: LSASS dumping,
  encoded PowerShell, BYOVD, RMM abuse, cloud exfil, ESXi ransomware,
  Kerberoasting, LOLBin proxy exec, persistence (task/WMI/account), MFA fatigue.
- **14 new ATT&CK techniques** (25 total) with event→technique mappings and
  server-side score weights (kerberoast tuned separately from LSASS).
- Extended `attack_replay.py` matrix to 14 techniques (100% coverage, 0 FP).
- **CI conflict-marker gate** as the first build step (covers md/sh/yml/bat too).
- **Containment unit tests** proving dry-run safety and reversibility.

### Changed
- README rewritten: honest Real-vs-Simulated table, full 25-technique coverage
  table, cross-platform install (Linux/Windows/macOS), structure, roadmap.
- RTO badge now labelled `(simulated)` to reflect the `SimulatedBackend` source.


# Ganglion-OOB — Changelog

## v2.0 — Security, Ransomware Continuity, and Honesty Pass

Every item below was verified by running the code, not by inspection alone.
Run `python3 verify.py` (23 assertions) and `python3 demo.py` to confirm.

### 🔒 Security (the biggest gap in v1)

- **Replaced the static-XOR transport with a real authenticated channel**
  (`common/secure_channel.py`).
  - *Why:* v1 used one hard-coded 28-byte XOR key shared by the agent,
    controller, AND the public test harness. XOR with a repeating key is
    trivially broken, there was no authentication, and no replay protection.
  - *Now:* AES-256-GCM (or a stdlib-only HMAC-SHA256 encrypt-then-MAC AEAD if
    `cryptography` is absent), **per-agent keys** via HKDF, **replay protection**
    (random nonce + monotonic counter + timestamp-skew window), and **identity
    binding** so a frame's `vm_id` is forced to equal the authenticated agent.
- **Killed the vm_id-spoofing attack.** In v1, malware in VM-A could send
  telemetry tagged `vm_id: "VM-B"` and force-isolate an innocent VM. The
  receiver now rejects any frame whose payload `vm_id` ≠ authenticated identity.
- **Agent score deltas are no longer trusted.** v1 fell back to the agent's
  self-reported `score_delta` for unknown event types, so a compromised agent
  could send `score_delta: 0` to suppress its own score. The controller now
  computes every score from a single authoritative table.

### 🦠 Ransomware detection + response (the user's core idea)

- **New `CryptographicSpikeDetector`** in the agent — the "crypto map" the design
  called for. It tracks the *rate and variance* of high-entropy writes and fires
  a dedicated `crypto_spike` event (+50) the moment encryption behaviour deviates
  ≥3σ from the host's own baseline. Variance-aware, so steady encrypted-blob
  workloads don't false-positive.
- **Instant NIC kill-switch** on a crypto-spike (`hypervisor_api.block_network`),
  executed *before* the slower quarantine-VLAN move — containment in milliseconds.
- **Business-continuity failover** (`host_control_plane/failover_orchestrator.py`)
  — the missing half of v1. When the ACTIVE node of a service is compromised, a
  warm STANDBY is promoted, the service VIP is redirected, the workload keeps
  running (sub-second RTO measured + shown on the dashboard), the primary is cured
  in the background, and it rejoins as the new STANDBY. The pair self-heals.
- **Cross-platform backup-destruction detection.** v1 only caught Windows
  `vssadmin`/`wbadmin`. Now also detects Linux/macOS (`rm -rf /backup`,
  `btrfs subvolume delete`, `zfs destroy`, `shred`, snapshot deletion, etc.).

### 🐶 Always-active aggression

- **Agent-silence watchdog.** Malware's first move is to kill the agent; in v1
  that just made the VM go quiet and nothing happened. The controller now flags
  any agent that misses 3× its expected heartbeat interval (`silent=true` +
  synthetic `agent_silence` alert).
- **Heartbeat self-attestation** — monotonic `agent_seq` + declared interval, so
  the watchdog can distinguish "idle" from "killed".

### 🐛 Functional bug fixes

- **Velocity-spike scoring fixed.** v1 emitted the velocity spike as an `entropy`
  event, which the controller silently re-scored from 20 → 40. It now has its own
  `velocity` type scored at the intended +20.
- **Non-blocking incident response.** v1 ran the ~9s IR sequence (with
  `time.sleep` calls) synchronously inside the main loop, freezing the dashboard
  and leaving `isolated:true` with an empty IR log. IR now runs in a worker
  thread; the dashboard shows IR + failover progress live.
- **Score band consistency.** Score is no longer capped at exactly 100 (capped at
  200) so CRITICAL severity is meaningful; dashboard/threshold bands aligned.
- **Fixed `f"/tmp/{random.choices(...)}"`** in the test harness (was embedding a
  list object in the path instead of a joined string).
- **Fixed `yara_engine.py` invalid escape-sequence warning** (raw docstring).
- **Docs/requirements consistency.** `blue_team/__init__.py` said "Eight tools"
  while the suite has 21 — corrected. Requirements pinned consistently across all
  modules; `cryptography` added (optional, with graceful fallback).

### ✨ Shock-factor / presentation

- **`demo.py`** — one command runs the entire story (normal → crypto-spike →
  block → isolate → failover → self-heal) with narration and a final RTO readout.
- **Rebuilt SOC dashboard** (`host_control_plane/dashboard.html`) — live crypto
  map per VM, kill-chain event stream, **Service Continuity / failover panel**
  with node roles and RTO, watchdog "silent agent" indicator, failover counter.
- **`verify.py`** — 23-assertion self-test that proves security, scoring,
  crypto-spike, failover, and watchdog all work, with no hypervisor required.

### Deployment

- systemd units now read a shared master secret from
  `/etc/ganglion-oob/master.env`; `deploy.sh` generates one on the host and
  reminds you to copy it to each guest.
- `deploy.sh` copies the new `common/`, `failover_orchestrator.py`, and
  `dashboard.html` for the relevant roles.

### Known limitations (stated honestly)

- The failover orchestrator ships with a **simulated backend** so the full flow
  runs without real infrastructure. Wiring it to a real load balancer / hypervisor
  is a matter of implementing the 4-method `FailoverBackend` interface
  (`promote`, `redirect_traffic`, `health_check`, `rejoin_as_standby`).
- The hypervisor actions require real VirtualBox/Proxmox to actually execute; on
  a machine without them they log "would execute" and return failure — by design.
- The default master key is a **development** key. Production MUST set
  `GANGLION_MASTER_KEY`.

## v2.1 — Detection Intelligence Layer (ATT&CK + Sigma + Validation)

Built as one coherent layer that makes detections speak the language real SOCs
use, and proves they work.

- **MITRE ATT&CK mapping** (`common/mitre_attack.py`) — every telemetry event is
  tagged with real published technique IDs (T1486 Data Encrypted for Impact,
  T1490 Inhibit System Recovery, T1505.003 Web Shell, T1036.005 Masquerading,
  T1571 Non-Standard Port, T1562.001 Impair Defenses). Events, the API, and the
  dashboard all carry ATT&CK context.
- **Live ATT&CK matrix** on the SOC dashboard — tactic columns light up as
  techniques are observed in real time.
- **Sigma-compatible detection engine** (`blue_team/sigma_engine/`) — loads
  industry-standard Sigma YAML rules (selections, conditions incl. `and/or/not`,
  `1 of them`, `all of them`, field modifiers `contains/startswith/endswith/re`),
  extracts ATT&CK tags, and matches Ganglion telemetry. Ships 6 rules. Now the
  22nd tool in the blue-team CLI.
- **Attack-replay validation** (`attack_replay.py`) — fires every technique in a
  test matrix and reports **ATT&CK coverage, MTTD, and false-positive rate**,
  cross-confirmed by the Sigma engine. Offline (in-process) and live modes.
- **Bug found BY the new validation harness and fixed:** `agent_silence`
  (T1562.001) was detected but scored 0, so killing the agent didn't raise the
  threat score. Now weighted at +25 and contributes to isolation. (This is the
  good kind of finding — the test suite caught a gap in the product.)
- `verify.py` expanded to **34 assertions** (added ATT&CK + Sigma coverage).
- `demo.py` now prints the detection-coverage report (ATT&CK + Sigma metrics) at
  the end, so one command shows both the attack story AND the proof.

## v2.2 — SOC Workflow, Enrichment & Defensibility

- **SOC alert queue** (`host_control_plane/alert_manager.py`) — scored events
  become alerts with a full lifecycle (OPEN → ACKNOWLEDGED → ESCALATED → CLOSED /
  FALSE_POSITIVE), analyst actions (ack/assign/escalate/close/false-positive/note),
  dedupe, and an audit trail. This is the "real SOC" workflow detection alone lacks.
- **Operational metrics** — mean detection latency (MTTD), false-positive rate,
  and an alert-volume trend, all from real data, surfaced on the dashboard.
- **Threat geography + intel enrichment** (`host_control_plane/geo_intel.py`) —
  outbound destination IPs are geo-located (offline approximation, honestly
  labelled) and given a local threat-intel verdict (malicious/suspicious/internal).
- **Dashboard upgraded** with three new panels: SOC alert queue with action
  buttons, alert-volume trend chart, and outbound-destination/threat-geo panel.
- **New API:** `/api/alerts/<id>/<action>` for analyst dispositions; alerts,
  metrics, and geo events added to `/api/status`.
- **`verify.py` now at 44 assertions** (added SOC workflow + enrichment checks).
- **`DEFENSE_GUIDE.md` added** — module-by-module rationale and an interview Q&A,
  so the project can be *defended*, not just demonstrated. Read it.

### Honest limitations (unchanged stance)
- Geo-IP is an **offline approximation** (built-in block table + deterministic
  placement for unknowns, flagged `approx`). Drop in MaxMind GeoLite2 for real
  accuracy — the dashboard contract is unchanged.
- Alerts are in-memory (reset on restart). A persistent store is the next step.

## v2.3 — Hardening Pass (bugs, security, tooling)

Addressed an external code-review. Every fix verified against the live system.

### Bug fixes
- **Telemetry re-queue (sentry_agent.py):** failed sends previously used
  `appendleft()` onto a `maxlen=500` deque, which silently dropped the newest
  events during a burst. Now uses a dedicated `_retry` buffer (maxlen=2000)
  drained oldest-first on the next flush — no event loss, order preserved.
- **OrderedSet eviction (secure_channel.py):** nonce-replay cache evicted with
  `list.pop(0)` (O(n)). Replaced the order list with `collections.deque` +
  `popleft()` (O(1)).
- **Packaging:** added `__init__.py` to all 21 blue-team tool directories — they
  are now importable Python packages (needed for pytest + clean imports).
- **Silent excepts:** replaced bare `except: pass` sites with logged versions.
  The agent logs to a local file (`sentry_agent.log`) and never to a TTY, so it
  stays invisible to an attacker on the box; the controller logs at debug/exception.

### Security
- **API authentication (critical):** `/api/isolate`, `/api/restore`, and all
  `/api/alerts/<id>/<action>` mutations now require a bearer token
  (`X-Ganglion-Token` or `Authorization: Bearer`). Read-only `/api/status` and the
  dashboard stay open so the UI loads. Token via `--api-token`,
  `GANGLION_API_TOKEN`, or an auto-generated per-session token printed at startup.
  Constant-time comparison. Optional `--allow-ips` IP allowlist.
- **Dev-key warning:** the controller now detects the public development master
  key and prints a loud multi-line startup warning that telemetry can be forged
  until `GANGLION_MASTER_KEY` is set.

### Tooling / repo hygiene
- Added **LICENSE** (MIT), **.gitignore** (caches, dumps, keys, findings),
  **.github/workflows/ci.yml** (compile + pytest + verify + replay on py3.10–3.12),
  **tests/test_ganglion.py** (19 pytest unit tests), and **pyproject.toml**
  (pytest + mypy config).

### Verified after this pass
- `pytest` → 19 passed   ·   `verify.py` → 44/44   ·   `attack_replay --offline` → 100% coverage, 0 FP
- API auth: unauth isolate → 401, wrong token → 401, correct token → 200, status → 200
- All 22 blue-team tools import; blue_team packages now importable.
