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


def _status(base: Path, mission_id: str | None = None) -> dict:
    pid = _read_pid(base)
    out = {"pid": pid, "alive": _pid_alive(pid)}
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


def execute_autoloop(cfg, args: dict) -> dict:
    _, base = _paths()
    action = str(args.get("action", "status")).strip().lower()
    if action == "status":
        mid = str(args.get("mission_id") or "").strip() or None
        return _status(base, mid)
    if action == "start":
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
        pid = _read_pid(base)
        if _pid_alive(pid):
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.4)
        return {"stopped": not _pid_alive(pid), "pid": pid}
    if action == "mission":
        mid = str(args.get("id") or f"mission-{int(time.time())}")
        goal = str(args.get("goal") or "").strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", mid):
            raise ValueError("invalid mission id")
        if not goal or len(goal) > 3000:
            raise ValueError("goal must be 1-3000 characters")
        if not _pid_alive(_read_pid(base)):
            raise RuntimeError("autoloop daemon is not running")
        mission = {"id": mid, "created_at": time.time(), "goal": goal}
        dst = base / "inbox" / f"{mid}.json"
        dst.write_text(json.dumps(mission, indent=2))
        return {"queued": True, "mission": mission, "path": str(dst)}
    raise ValueError("action must be status, start, stop, or mission")
