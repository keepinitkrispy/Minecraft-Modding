"""Verify runit restarts the objective worker after a forced process death."""
import json
import os
import signal
import time
from pathlib import Path

state_path = Path.home() / "solbridge-workspace" / "objectives" / "autonomy.json"
before = json.loads(state_path.read_text())
starts = [event for event in before.get("events", []) if event.get("kind") == "worker_started"]
if not starts:
    raise RuntimeError("No objective worker process has started")
old_pid = int(starts[-1]["detail"]["pid"])
cmdline = Path(f"/proc/{old_pid}/cmdline").read_bytes().replace(b"\0", b" ")
if b"objective_loop.py" not in cmdline:
    raise RuntimeError("Worker pid does not belong to the objective loop")
os.kill(old_pid, signal.SIGKILL)
for _ in range(60):
    time.sleep(0.5)
    data = json.loads(state_path.read_text())
    starts = [event for event in data.get("events", []) if event.get("kind") == "worker_started"]
    new_pid = int(starts[-1]["detail"]["pid"]) if starts else None
    if new_pid and new_pid != old_pid:
        try:
            new_cmdline = Path(f"/proc/{new_pid}/cmdline").read_bytes().replace(b"\0", b" ")
        except FileNotFoundError:
            continue
        if b"objective_loop.py" in new_cmdline:
            from importlib.util import module_from_spec, spec_from_file_location
            source = Path.home() / "solbridge-workspace" / "agent" / "objective_loop.py"
            spec = spec_from_file_location("objective_loop", source)
            agent = module_from_spec(spec)
            spec.loader.exec_module(agent)
            agent.update_state(lambda d: (d.update({"restart_verified": True}),
                                          agent.event(d, "worker_restart_verified",
                                                      {"old_pid": old_pid, "new_pid": new_pid})))
            print(json.dumps({"verified": True, "old_pid": old_pid, "new_pid": new_pid}))
            break
else:
    raise RuntimeError("Objective worker did not restart within 30 seconds")
