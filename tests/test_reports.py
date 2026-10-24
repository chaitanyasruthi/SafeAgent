"""Validates the graded report files. Missing/incomplete reports FAIL on purpose:
nothing is auto-marked true. Run: pytest tests/test_reports.py"""
import json, math, re
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"^sbx-[a-z0-9]{8,}$")
CAPS = {"persistence", "snapshots", "celestofs", "browser", "published_ports",
        "network_policy", "safety_hooks", "host_mounts", "coding_agent_preset", "agentor_durable"}


def load(rel):
    p = ROOT / rel
    assert p.is_file(), f"{rel} is missing"
    return json.loads(p.read_text(encoding="utf-8"))


def jsonl(rel):
    p = ROOT / rel
    assert p.is_file(), f"{rel} is missing"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def test_env_example_and_no_env():
    text = (ROOT / ".env.example").read_text()
    for k in ["CELESTO_PROVIDER", "CELESTO_API_KEY", "LLM_API_KEY", "LLM_MODEL", "DATABASE_URL", "API_PORT"]:
        assert re.search(rf"^{k}=", text, re.M), k
    assert not (ROOT / ".env").exists(), ".env must not be in the submission"


def test_compose():
    t = (ROOT / "docker-compose.yml").read_text()
    for s in ["api:", "ledger:", "pg_isready", "/health", "./seeds", "start_period", "interval", "timeout", "retries"]:
        assert s in t, s


def test_problem():
    d = load("reports/problem.json")
    assert len(d["who"]) >= 40 and len(d["agent_work"]) >= 40 and len(d["proof_output"]) >= 20
    assert d["idea_source"] in {"idea_bank", "original"}


def test_commands_log():
    rows = jsonl("logs/commands.jsonl")
    assert rows
    for r in rows:
        assert r["ts"] and NAME.match(r["sandbox_name"]) and r["command"].strip()
        assert r["decision"] in {"allow", "block"} and r["execution_target"] == "celesto_sandbox"


def test_capabilities():
    caps = load("reports/capabilities.json")["capabilities"]
    assert len(caps) >= 2
    ids = [c["id"] for c in caps]
    assert len(set(ids)) == len(ids) and set(ids) <= CAPS
    for c in caps:
        assert len(c["why"]) >= 80 and (ROOT / c["evidence_path"]).is_file()


def test_lifecycle():
    d = load("reports/lifecycle.json")
    assert all(d[k] is True for k in ["cleanup_on_success", "cleanup_on_failure", "cleanup_on_interrupt"])
    names = d["sandbox_names"]
    assert names and len(set(names)) == len(names) and all(NAME.match(n) for n in names)
    seen = {r["sandbox_name"] for r in jsonl("logs/commands.jsonl")}
    seen |= {r["sandbox_name"] for r in load("reports/reliability.json")["runs"]}
    assert set(names) <= seen


def test_reliability():
    d = load("reports/reliability.json")
    runs, n = d["runs"], len(d["runs"])
    assert n >= 20 and d["run_count"] == n
    names = [r["sandbox_name"] for r in runs]
    assert len(set(names)) == n and all(NAME.match(x) for x in names)
    for r in runs:
        assert r["fresh"] is True and isinstance(r["success"], bool)
        for k in ["wall_clock_s", "boot_to_ready_s", "cost_usd"]:
            assert r[k] >= 0
    assert abs(d["success_rate"] - sum(r["success"] for r in runs) / n) <= 0.001

    def med(v):
        v = sorted(v); m = len(v)
        return v[m // 2] if m % 2 else (v[m // 2 - 1] + v[m // 2]) / 2
    w = sorted(r["wall_clock_s"] for r in runs)
    assert abs(d["median_wall_clock_s"] - med(w)) <= 0.001
    assert abs(d["p90_wall_clock_s"] - w[math.ceil(0.9 * n) - 1]) <= 0.001
    assert abs(d["median_boot_to_ready_s"] - med([r["boot_to_ready_s"] for r in runs])) <= 0.001
    assert abs(d["total_cost_usd"] - sum(r["cost_usd"] for r in runs)) <= 0.01
    assert d["postmortem_path"] == "reports/postmortem.md"
    assert len((ROOT / "reports/postmortem.md").read_text(encoding="utf-8")) >= 200


def test_containment():
    d = load("reports/containment.json")
    assert d["attack"] in {"prompt_injection_exfil", "destructive_command", "suspicious_package"}
    assert d["blocked"] is True and d["host_untouched"] is True
    assert d["evidence_paths"] and all((ROOT / p).is_file() for p in d["evidence_paths"])


def test_failure_policy():
    d = load("reports/failure_policy.json")
    assert d["failed_step"] == 7 and d["total_steps"] == 10
    assert d["policy"] in {"resume", "rollback", "fresh"} and len(d["rationale"]) >= 200
    assert d["trace_path"] == "reports/failure_trace.jsonl"
    assert any(e.get("event") == "policy_applied" and e.get("policy") == d["policy"]
               for e in jsonl(d["trace_path"]))


def test_concurrency():
    d = load("reports/concurrency.json")
    jobs = d["jobs"]
    assert len(jobs) >= 5
    names = [j["sandbox_name"] for j in jobs]
    assert len(set(names)) == len(names) and all(NAME.match(x) for x in names)
    assert all(isinstance(j["started_at"], str) and j["started_at"] for j in jobs)
    assert len(d["breakage_notes"]) >= 40


def test_readme_phrases():
    t = (ROOT / "README.md").read_text(encoding="utf-8")
    for p in ["Problem statement", "How I used Celesto", "Eval report", "Containment test",
              "State and failure design", "Setup"]:
        assert p in t, p
