"""Tests for v1.1 upgrades: perimeter engines + self-healing subsystem."""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "blue_team", "waf_engine"))
sys.path.insert(0, os.path.join(ROOT, "blue_team", "ids_engine"))
sys.path.insert(0, os.path.join(ROOT, "blue_team", "firewall"))


# ------------------------- WAF -------------------------
class TestWAF:
    def _waf(self):
        from waf_engine import WafEngine
        return WafEngine()

    def test_sqli_blocked(self):
        r = self._waf().inspect({"uri": "/p", "args": "id=1 OR 1=1--"})
        assert r["verdict"] == "BLOCK" and "T1190" in r["techniques"]

    def test_jndi_blocked(self):
        r = self._waf().inspect({"uri": "/", "headers": "UA: ${jndi:ldap://x/a}"})
        assert r["verdict"] == "BLOCK"

    def test_benign_allowed(self):
        r = self._waf().inspect({"uri": "/home", "args": "page=2",
                                 "headers": "User-Agent: Mozilla/5.0"})
        assert r["verdict"] == "ALLOW" and r["score"] == 0


# ------------------------- IDS/IPS -------------------------
class TestIDS:
    def test_known_bad_ip_drops_in_ips_mode(self):
        from ids_engine import IDSEngine
        f = IDSEngine(mode="ips").inspect(
            {"src_ip": "10.0.0.5", "dst_ip": "185.220.1.9", "dst_port": 443})
        assert any(x.rule == "SIG-BADIP" and x.verdict == "DROP" for x in f)

    def test_port_scan_detected(self):
        from ids_engine import IDSEngine
        eng = IDSEngine(mode="ids", scan_ports_threshold=15)
        out = []
        for p in range(20, 40):
            out = eng.inspect({"src_ip": "10.0.0.66", "dst_ip": "10.0.0.9",
                               "dst_port": p, "ts": time.time()})
        assert any(x.rule == "ANO-PORTSCAN" for x in out)

    def test_benign_no_finding(self):
        from ids_engine import IDSEngine
        f = IDSEngine(mode="ips").inspect(
            {"src_ip": "10.0.0.5", "dst_ip": "10.0.0.6", "dst_port": 443})
        assert f == []


# ------------------------- Firewall -------------------------
class TestFirewall:
    def _policy(self):
        from firewall import FirewallPolicy
        return FirewallPolicy.from_config([
            {"action": "deny", "dir": "out", "dst": "185.220.1.9/32", "note": "C2"},
            {"action": "allow", "dir": "in", "proto": "tcp", "port": 443},
        ], default_action="deny")

    def test_default_deny(self):
        r = self._policy().evaluate(
            {"dir": "in", "proto": "tcp", "src_ip": "1.2.3.4",
             "dst_ip": "10.0.0.9", "dst_port": 22})
        assert r["action"] == "deny" and r["matched"] is False

    def test_explicit_allow(self):
        r = self._policy().evaluate(
            {"dir": "in", "proto": "tcp", "src_ip": "1.2.3.4",
             "dst_ip": "10.0.0.9", "dst_port": 443})
        assert r["action"] == "allow"

    def test_enforce_is_dryrun(self):
        enf = self._policy().enforce_block(mgmt_allow="10.0.0.0/24")
        assert enf["enforced"] is True and enf["dry_run"] is True


# ------------------------- Self-healing -------------------------
class TestSelfHealing:
    def test_reflex_isolates_on_critical(self):
        from self_healing import SelfHealingRuntime
        isolated = []
        rt = SelfHealingRuntime(effectors={"containment": lambda c: isolated.append(c.entity),
                                           "healing": lambda c: None})
        rt.sense("sentry", "crypto_spike", "critical", "vm-1", techniques=["T1486"])
        assert isolated == ["vm-1"]

    def test_low_severity_no_reflex(self):
        from self_healing import SelfHealingRuntime
        isolated = []
        rt = SelfHealingRuntime(effectors={"containment": lambda c: isolated.append(c.entity)})
        rt.sense("ids", "network", "low", "vm-1")
        assert isolated == []

    def test_dead_component_triggers_heal(self):
        from self_healing import SelfHealingRuntime
        healed = []
        rt = SelfHealingRuntime(effectors={"healing": lambda c: healed.append(c.entity),
                                           "containment": lambda c: None,
                                           "failover": lambda c: None})
        rt.health.register("sentry_agent", interval=1.0)
        rt.heartbeat("sentry_agent", cpu_percent=10)
        rt.health.components["sentry_agent"].last_beat -= 10
        rt.tick()
        assert "sentry_agent" in healed

    def test_circuit_breaker_trips_and_recovers(self):
        from self_healing import CircuitBreaker
        cb = CircuitBreaker("x", fail_threshold=3, cooldown_s=0.0)
        for _ in range(3):
            cb.record_failure()
        assert cb.state.value == "open"
        assert cb.allow() is True          # cooldown 0 -> half-open
        cb.record_success()
        assert cb.state.value == "closed"

    def test_health_state_transitions(self):
        from self_healing import HealthMonitor
        hm = HealthMonitor()
        hm.register("c", interval=1.0)
        hm.heartbeat("c", cpu_percent=10)
        assert hm.components["c"].state.value == "healthy"
        hm.sweep(now=time.time() + 5)
        assert hm.components["c"].state.value == "dead"


# ------------------------- Robustness / hardening -------------------------
class TestRobustness:
    """Engines must never crash on malformed / empty / hostile input."""

    def test_waf_handles_empty_and_missing_fields(self):
        from waf_engine import WafEngine
        w = WafEngine()
        for bad in ({}, {"uri": None}, {"args": 12345}, {"headers": {"x": 1}},
                    {"uri": "", "args": "", "body": ""}):
            r = w.inspect(bad)
            assert r["verdict"] in ("ALLOW", "BLOCK")  # returns, never raises

    def test_ids_handles_missing_fields(self):
        from ids_engine import IDSEngine
        eng = IDSEngine(mode="ips")
        for bad in ({}, {"src_ip": None}, {"dst_port": "notaport"}, {"event": "auth_fail"}):
            out = eng.inspect(bad)
            assert isinstance(out, list)  # never raises

    def test_firewall_handles_bad_cidr_and_ports(self):
        from firewall import FirewallPolicy
        pol = FirewallPolicy.from_config([
            {"action": "allow", "dir": "in", "src": "not-a-cidr", "port": "bad"},
        ], default_action="deny")
        r = pol.evaluate({"dir": "in", "src_ip": "1.2.3.4", "dst_port": 443})
        assert r["action"] in ("allow", "deny")  # bad rule simply doesn't match

    def test_nervous_system_faulty_subscriber_does_not_kill_bus(self):
        from self_healing import NervousSystem, AfferentSignal, Severity, SignalKind
        ns = NervousSystem()
        ns.subscribe(SignalKind.AFFERENT, lambda s: 1 / 0)  # explodes
        ok = []
        ns.subscribe(SignalKind.AFFERENT, lambda s: ok.append(True))  # must still run
        ns.sense(AfferentSignal("t", "x", Severity.LOW, entity="e"))
        assert ok == [True]  # bus survived the faulty subscriber

    def test_healing_never_loops_forever(self):
        from self_healing import SelfHealingRuntime
        rt = SelfHealingRuntime(effectors={"healing": lambda c: None,
                                           "containment": lambda c: None,
                                           "failover": lambda c: None})
        rt.health.register("control_center", interval=1.0)
        rt.heartbeat("control_center", cpu_percent=10)
        rt.health.components["control_center"].last_beat -= 100
        for _ in range(50):          # hammer the loop
            rt.tick()
        # must have escalated to a human rather than thrashing infinitely
        assert len(rt.healer.escalations) >= 1
