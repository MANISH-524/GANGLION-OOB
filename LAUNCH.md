# 🚀 Launch & Discoverability Kit

Everything here targets the one weak spot: **nobody knows the repo exists yet.**
Code quality doesn't create stars — visibility + a 15-second "it works" moment does.
Work top to bottom.

---

## 1. GitHub repo settings (5 minutes, do first)

**About → Description** (paste):
> Out-of-band, self-healing SOC + Blue-Team platform. Detects modern attacks in ms, contains at the network layer, and fails the workload over to a warm standby — so the business keeps running. MITRE ATT&CK + Sigma. Ransomware can't kill what it can't reach.

**About → Topics** (add all — this is how GitHub search finds you):
```
cybersecurity  blue-team  soc  incident-response  ransomware
mitre-attack  sigma  ids  ips  waf  self-healing  edr
threat-detection  security-tools  python  dfir  detection-engineering
```

**About → Website:** link the asciinema recording once uploaded.

**Enable:** Issues, Discussions. **Add:** a `LICENSE` (MIT — already present), and pin the repo on your profile.

---

## 2. Cut a real Release (signals maturity)

```bash
git tag -a v1.1.1 -m "Vanguard-OOB v1.1.1 — self-healing + IDS/IPS/WAF/FW + hardening"
git push origin v1.1.1
```
Then GitHub → Releases → Draft new release → pick the tag → paste the top of
`CHANGELOG.md`. A tagged release with notes reads as "maintained," not "abandoned."

---

## 3. Record the money shot (highest leverage of all)

```bash
pip install asciinema
asciinema rec media/demo.cast -c "python3 demo.py"    # or reuse the shipped cast
asciinema upload media/demo.cast                      # gives you a shareable link
# GIF for the README top + social posts:
agg media/demo.cast media/demo.gif
```
Put the GIF at the very top of the README. People decide in ~10 seconds.

---

## 4. Turn on branch protection (stops the old conflict bug returning)

Settings → Branches → Add rule for `main`:
- ✅ Require a pull request before merging
- ✅ Require status checks to pass (select the CI workflow)
- ✅ Require branches to be up to date

This is what prevents a broken/conflict push to `main` ever again.

---

## 5. Launch posts (paste, adjust, ship)

Post the **GIF first** in every one. Best days: Tue–Thu, morning US time.

### Hacker News (Show HN)
> **Show HN: Vanguard-OOB — an out-of-band, self-healing SOC that fails your workload over instead of just isolating it**
>
> I built a blue-team/SOC prototype around one idea: security agents that run *inside* a VM can be killed by privileged malware, and even when you isolate an infected box the workload still goes down. So Vanguard runs the control plane out-of-band (the malware can't reach it), detects ransomware as it starts, contains at the network layer in milliseconds, and **fails the workload over to a warm standby** so the business keeps running — then heals the infected node and rejoins it.
>
> It's modelled on the human nervous system: reflex arc for instant response, a "brain" for deliberate scoring, and a homeostatic healing loop. Detection speaks MITRE ATT&CK + Sigma. Everything is runnable and tested (44 checks, 41 unit tests, 14/14 ATT&CK replay, 0 FP) — `python3 demo.py` shows the whole thing in ~15s. Honest about what's real vs simulated.
>
> Repo: <link>  ·  Feedback very welcome, especially on the failover-over-isolation tradeoff.

### r/netsec / r/blueteamsec
> **Vanguard-OOB: out-of-band ransomware containment + business-continuity failover (MITRE ATT&CK + Sigma, fully runnable)**
>
> [same body as above, slightly shorter]. Would love blue-teamers to poke holes in the threat model — particularly the reflex-vs-deliberate split and the self-healing escalation-to-human logic.

### LinkedIn / X
> Most security tools run *inside* the box malware is attacking — so malware just turns them off. And isolating an infected machine still takes the workload down.
>
> I built Vanguard-OOB around a different bet: run the brain **out-of-band**, detect ransomware as it starts, cut the network in milliseconds, and **fail the workload over to a standby so the business never stops** — then heal the infected node. Modelled on the nervous system: reflex → brain → homeostasis.
>
> 15-second demo + full write-up 👇  [GIF]  <link>
>
> #cybersecurity #blueteam #ransomware #SOC #incidentresponse

---

## 6. Where else to list it
- Add to `awesome-security`, `awesome-incident-response`, `awesome-threat-detection` (open a PR).
- Submit to the Sigma community if you contribute rules upstream.
- If you write the nervous-system model up as a blog post, cross-post to dev.to / Medium and link back.

---

## 7. Honest expectation-setting
- A good launch post with a working GIF → **50–300 stars** is realistic.
- The thing that pushes past that is **one real deployment story** (non-simulated failover on real infra) or the **hardware prototype**. That's the unique angle — lead with it once you have it.
- Reply to every comment/issue fast in the first 48h; early engagement is what sustains momentum.
