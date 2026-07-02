# Vanguard-OOB v1.1.1

**Out-of-band, self-healing SOC + Blue-Team resilience — ransomware can't kill what it can't reach.**

## Highlights
- 🧠 **Self-healing subsystem** modelled on the human nervous system (reflex arc → brain → homeostasis → healing).
- 🧱 **Built-in perimeter engines**: IDS/IPS, WAF, and a config-driven Firewall that compiles to real OS backends.
- 🛡️ **28 MITRE ATT&CK techniques**, **16 Sigma rules**, real cross-platform network containment (dry-run by default).
- ✅ **Proven**: 44/44 correctness checks · 41 unit tests · 14/14 ATT&CK replay · 0 false positives.
- 📄 Full docs: `HOW_IT_WORKS.md`, `SELF_HEALING.md`, honest Real-vs-Simulated table.

## Run it
```bash
pip install -r requirements.txt
python3 demo.py        # full attack→defense story (~15s)
python3 verify.py      # 44 checks
pytest -q              # 41 tests
```

See `CHANGELOG.md` for the complete history.
