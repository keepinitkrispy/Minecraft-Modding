import importlib.util
import json
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

module_path = Path(__file__).with_name("objective_loop.py")
if not module_path.exists():
    module_path = Path(__file__).parents[1] / "solbridge" / "objective_loop.py"
spec = importlib.util.spec_from_file_location("objective_loop", module_path)
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
    agent.SECRET = agent.ROOT / "agent" / "session_secret"
    agent.SECRET.parent.mkdir(parents=True)
    agent.SECRET.write_text("private-pairing-secret")
    server = ThreadingHTTPServer(("127.0.0.1", 0), agent.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    assert urllib.request.urlopen(base + "/health").status == 200
    try:
        urllib.request.urlopen(base + "/api/state")
    except urllib.error.HTTPError as exc:
        assert exc.code == 404
    else:
        raise AssertionError("Unauthenticated state must not be exposed")
    request = urllib.request.Request(
        base + "/api/message", data=json.dumps({"message": "Keep solving the original goal"}).encode(),
        headers={"Cookie": "og_session=private-pairing-secret", "Content-Type": "application/json"},
    )
    assert urllib.request.urlopen(request).status == 202
    assert agent.read_state()["chat"][-1]["text"] == "Keep solving the original goal"
    server.shutdown()
print("Two-route cycle, frozen objective and false PASS guard: PASS")
