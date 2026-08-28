from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path


def _paths():
    root = Path.home() / "solbridge-workspace"
    base = root / "autoloop"
    for p in (base, base / "inbox", base / "done", base / "failed", base / "proofs"):
        p.mkdir(parents=True, exist_ok=True)
    return root, base


def _prefix() -> Path:
    return Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr"))


def _pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _read_pid(base: Path) -> int | None:
    try:
        return int((base / "autoloop.pid").read_text().strip())
    except Exception:
        return None


def _sv_status() -> dict:
    prefix = _prefix()
    env = dict(os.environ)
    env["SVDIR"] = str(prefix / "var/service")
    try:
        r = subprocess.run([str(prefix / "bin/sv"), "status", "autoloop"], capture_output=True, text=True, timeout=10, env=env)
        return {"returncode": r.returncode, "text": (r.stdout + r.stderr).strip()[-1000:]}
    except Exception as e:
        return {"returncode": 127, "text": f"{type(e).__name__}: {e}"}


def _status(base: Path, mission_id: str | None = None) -> dict:
    pid = _read_pid(base)
    out = {"pid": pid, "alive": _pid_alive(pid), "supervisor": _sv_status()}
    log = base / "autoloop.log"
    if log.exists():
        out["log_tail"] = "\n".join(log.read_text(errors="ignore").splitlines()[-25:])
    if mission_id:
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", mission_id):
            raise ValueError("invalid mission id")
        proof = base / "proofs" / f"{mission_id}.json"
        out["proof_exists"] = proof.exists()
        if proof.exists():
            out["proof"] = json.loads(proof.read_text())
        out["done"] = (base / "done" / f"{mission_id}.json").exists()
        failed = base / "failed" / f"{mission_id}.json"
        out["failed"] = json.loads(failed.read_text()) if failed.exists() else None
    return out


def _install_supervisor() -> dict:
    prefix = _prefix()
    service_root = prefix / "var/service"
    service = service_root / "autoloop"
    log_dir = service / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    source = Path.home() / ".local/share/solbridge-src/solbridge"
    run_script = f'''#!/data/data/com.termux/files/usr/bin/sh
export PYTHONPATH="{source}${{PYTHONPATH:+:$PYTHONPATH}}"
exec 2>&1
exec {prefix}/bin/python -m solbridge.autoloop_daemon
'''
    log_script = f'''#!/data/data/com.termux/files/usr/bin/sh
exec {prefix}/bin/svlogger {prefix}/var/log/sv/autoloop
'''
    (service / "run").write_text(run_script)
    (log_dir / "run").write_text(log_script)
    os.chmod(service / "run", 0o755)
    os.chmod(log_dir / "run", 0o755)
    (service / "down").unlink(missing_ok=True)

    boot = Path.home() / ".termux/boot/solbridge-start.sh"
    boot.parent.mkdir(parents=True, exist_ok=True)
    boot_script = f'''#!/data/data/com.termux/files/usr/bin/sh
export SVDIR="{prefix}/var/service"
export LOGDIR="{prefix}/var/log"
PIDFILE="{prefix}/var/run/service-daemon.pid"
if [ ! -s "$PIDFILE" ] || ! kill -0 "$(cat "$PIDFILE" 2>/dev/null)" 2>/dev/null; then
  {prefix}/bin/service-daemon start >/dev/null 2>&1 || true
fi
for _ in $(seq 1 30); do
  [ -e "{prefix}/var/service/solbridge/supervise/ok" ] && [ -e "{prefix}/var/service/autoloop/supervise/ok" ] && break
  sleep 0.5
done
{prefix}/bin/sv up solbridge >/dev/null 2>&1 || true
{prefix}/bin/sv up autoloop >/dev/null 2>&1 || true
'''
    boot.write_text(boot_script)
    os.chmod(boot, 0o755)

    env = dict(os.environ)
    env["SVDIR"] = str(service_root)
    env["LOGDIR"] = str(prefix / "var/log")
    pidfile = prefix / "var/run/service-daemon.pid"
    daemon_alive = False
    try:
        daemon_alive = pidfile.exists() and _pid_alive(int(pidfile.read_text().strip()))
    except Exception:
        pass
    if not daemon_alive:
        subprocess.run([str(prefix / "bin/service-daemon"), "start"], capture_output=True, timeout=20, env=env)
    for _ in range(30):
        if (service / "supervise/ok").exists():
            break
        time.sleep(0.25)
    r = subprocess.run([str(prefix / "bin/sv"), "up", "autoloop"], capture_output=True, text=True, timeout=20, env=env)
    for _ in range(40):
        _, base = _paths()
        if _pid_alive(_read_pid(base)):
            break
        time.sleep(0.25)
    return {
        "installed": True,
        "service": str(service),
        "boot": str(boot),
        "sv_up_returncode": r.returncode,
        "sv_up_output": (r.stdout + r.stderr).strip()[-1000:],
        **_status(_paths()[1]),
    }


def _fault_test() -> dict:
    install = _install_supervisor()
    _, base = _paths()
    old_pid = _read_pid(base)
    if not _pid_alive(old_pid):
        raise RuntimeError("autoloop is not alive before fault test")
    os.kill(old_pid, signal.SIGKILL)
    new_pid = None
    for _ in range(80):
        time.sleep(0.25)
        candidate = _read_pid(base)
        if candidate and candidate != old_pid and _pid_alive(candidate):
            new_pid = candidate
            break
    proof = {
        "tested_at": time.time(),
        "old_pid": old_pid,
        "new_pid": new_pid,
        "old_dead": not _pid_alive(old_pid),
        "new_alive": _pid_alive(new_pid),
        "supervisor": _sv_status(),
    }
    proof["verified"] = bool(proof["old_dead"] and proof["new_alive"] and new_pid != old_pid)
    (base / "proofs/process-death-recovery.json").write_text(json.dumps(proof, indent=2))
    return {"install": install, "proof": proof}


def execute_autoloop(cfg, args: dict) -> dict:
    _, base = _paths()
    action = str(args.get("action", "status")).strip().lower()
    if action == "status":
        mid = str(args.get("mission_id") or "").strip() or None
        return _status(base, mid)
    if action == "install_supervisor":
        return _install_supervisor()
    if action == "fault_test":
        return _fault_test()
    if action == "start":
        supervised = _sv_status()
        if supervised.get("returncode") == 0:
            _install_supervisor()
            return {"started": False, "supervised": True, **_status(base)}
        pid = _read_pid(base)
        if _pid_alive(pid):
            return {"started": False, **_status(base)}
        log = (base / "daemon.out").open("ab", buffering=0)
        p = subprocess.Popen(
            [sys.executable, "-m", "solbridge.autoloop_daemon"],
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
        for _ in range(20):
            time.sleep(0.25)
            if _pid_alive(_read_pid(base)):
                break
        return {"started": True, "spawned_pid": p.pid, **_status(base)}
    if action == "stop":
        prefix = _prefix()
        env = dict(os.environ)
        env["SVDIR"] = str(prefix / "var/service")
        if (_prefix() / "var/service/autoloop/supervise/ok").exists():
            subprocess.run([str(prefix / "bin/sv"), "down", "autoloop"], capture_output=True, timeout=20, env=env)
        pid = _read_pid(base)
        if _pid_alive(pid):
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.4)
        return {"stopped": not _pid_alive(pid), "pid": pid, "supervisor": _sv_status()}
    if action == "mission":
        mid = str(args.get("id") or f"mission-{int(time.time())}")
        goal = str(args.get("goal") or "").strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", mid):
            raise ValueError("invalid mission id")
        if not goal or len(goal) > 3000:
            raise ValueError("goal must be 1-3000 characters")
        if not _pid_alive(_read_pid(base)):
            _install_supervisor()
        if not _pid_alive(_read_pid(base)):
            raise RuntimeError("autoloop daemon is not running")
        mission = {"id": mid, "created_at": time.time(), "goal": goal, "attempts": 0}
        dst = base / "inbox" / f"{mid}.json"
        dst.write_text(json.dumps(mission, indent=2))
        return {"queued": True, "mission": mission, "path": str(dst)}
    raise ValueError("action must be status, start, stop, mission, install_supervisor, or fault_test")
