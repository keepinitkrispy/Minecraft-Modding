import importlib.util
import json
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("objective_loop", Path(__file__).with_name("objective_loop.py"))
agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)

example = {
    "reply": "Testing two ways around the transport blocker.",
    "abstraction": "Transport is a reachability variable.",
    "blocker_variable": "remote reachability",
    "routes": [
        {"domain": "network", "mechanism": "HTTPS", "mapping": "mobile site access", "test": "GET page", "probe": "site"},
        {"domain": "process control", "mechanism": "supervisor", "mapping": "worker persistence", "test": "check service", "probe": "phone"},
    ],
}
plan = agent.extract_plan(json.dumps(example))
assert len(plan["routes"]) == 2
assert {r["probe"] for r in plan["routes"]} == {"site", "phone"}
bad = dict(example, routes=[example["routes"][0], example["routes"][0]])
try:
    agent.extract_plan(json.dumps(bad))
except ValueError:
    pass
else:
    raise AssertionError("Repeated routes must be rejected")

with tempfile.TemporaryDirectory() as tmp:
    agent.ROOT = Path(tmp)
    agent.STATE = agent.ROOT / "objectives" / "autonomy.json"
    agent.STATE.parent.mkdir()
    frozen = {"id": "external-autonomy-harness", "statement": "Ship external agent",
              "target": {"value": "Both devices verified"}, "status": "OPEN",
              "blocker": "No transport", "generations": [], "events": []}
    agent.STATE.write_text(json.dumps(frozen))
    agent.reason = lambda _data: plan
    agent.probe = lambda name: {"ok": name == "site", "status": 200 if name == "site" else 503}
    result = agent.cycle()
    after = agent.read_state()
    assert result["status"] == "OPEN"
    assert after["statement"] == frozen["statement"] and after["target"] == frozen["target"]
    assert after["generations"][0]["blocker_before"] == "No transport"
    assert len(after["generations"][0]["tested"]) == 2
    assert after["status"] != "PASS"
print("Two-route cycle, frozen objective and false PASS guard: PASS")
