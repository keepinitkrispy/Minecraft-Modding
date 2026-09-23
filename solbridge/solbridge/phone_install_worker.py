"""Install restartable Pixel agent and tunnel services without editing Termux configuration."""
import os
import subprocess
import time
from pathlib import Path

root = Path.home() / "solbridge-workspace" / "agent"
prefix = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr"))
service_root = prefix / "var" / "service"
env = dict(os.environ, SVDIR=str(service_root), LOGDIR=str(prefix / "var/log"))
for name, source in (("outcome-agent", "objective_loop.py"), ("outcome-tunnel", "phone_tunnel.py")):
    service = service_root / name
    logs = service / "log"
    logs.mkdir(parents=True, exist_ok=True)
    run = service / "run"
    output = root / (name + ".log")
    run.write_text(f"#!{prefix}/bin/sh\nexec >>{output} 2>&1\nexec {prefix}/bin/python {root / source}\n")
    log = logs / "run"
    log.write_text(f"#!{prefix}/bin/sh\nexec {prefix}/bin/svlogger {prefix}/var/log/sv/{name}\n")
    run.chmod(0o700)
    log.chmod(0o700)
    (service / "down").unlink(missing_ok=True)
    for _ in range(40):
        if (service / "supervise" / "ok").exists():
            break
        time.sleep(0.25)
    result = subprocess.run([str(prefix / "bin/sv"), "up", name], capture_output=True, text=True, env=env, timeout=20)
    print(name, "up code", result.returncode, (result.stdout + result.stderr)[-220:])
for name in ("outcome-agent", "outcome-tunnel"):
    if name == "outcome-agent":
        subprocess.run([str(prefix / "bin/sv"), "restart", name], capture_output=True, text=True, env=env, timeout=30)
    result = subprocess.run([str(prefix / "bin/sv"), "status", name], capture_output=True, text=True, env=env, timeout=20)
    print(name, "status", result.returncode, (result.stdout + result.stderr)[-350:])
