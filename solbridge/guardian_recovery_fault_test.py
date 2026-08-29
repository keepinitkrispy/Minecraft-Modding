from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HOME = Path.home()
PREFIX = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr"))
TOKEN_FILE = HOME / ".config/solbridge/companion.token"
LOG = HOME / "solbridge-workspace/guardian-recovery-fault.log"
DEFAULT_CONFIG = HOME / "solbridge-workspace/guardian-recovery-fault.json"


def run(cmd, timeout=30):
    p = subprocess.run([str(x) for x in cmd], capture_output=True, text=True, timeout=timeout)
    return {
        "cmd": [str(x) for x in cmd],
        "returncode": p.returncode,
        "stdout": p.stdout[-5000:],
        "stderr": p.stderr[-5000:],
    }


def companion(path, timeout=5):
    token = TOKEN_FILE.read_text().strip()
    req = urllib.request.Request(
        "http://127.0.0.1:8765" + path,
        headers={"X-SolBridge-Token": token, "User-Agent": "SolBridge-Guardian-Fault-Test"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def service_status():
    env = os.environ.copy()
    env["SVDIR"] = str(PREFIX / "var/service")
    p = subprocess.run(
        [str(PREFIX / "bin/sv"), "status", "solbridge"],
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
    )
    text = (p.stdout + p.stderr).strip()
    return {"returncode": p.returncode, "text": text, "running": text.startswith("run:")}


def service_down():
    env = os.environ.copy()
    env["SVDIR"] = str(PREFIX / "var/service")
    p = subprocess.run(
        [str(PREFIX / "bin/sv"), "down", "solbridge"],
        capture_output=True,
        text=True,
        timeout=20,
        env=env,
    )
    return {"returncode": p.returncode, "text": (p.stdout + p.stderr).strip()}


def post_ledger(repo: str, issue: int, payload: dict):
    body = "```json\n" + json.dumps(payload, indent=2, ensure_ascii=False)[:50000] + "\n```"
    p = subprocess.run(
        ["gh", "api", "--method", "POST", f"repos/{repo}/issues/{issue}/comments", "-f", f"body={body}"],
        capture_output=True,
        text=True,
        timeout=45,
    )
    return {"returncode": p.returncode, "stdout": p.stdout[-3000:], "stderr": p.stderr[-3000:]}


def worker(config_path: Path):
    cfg = json.loads(config_path.read_text())
    repo = str(cfg["repo"])
    ledger_issue = int(cfg["ledger_issue"])
    result = {
        "test": "native-guardian-recovery-fault-injection",
        "started_at": time.time(),
        "repo": repo,
        "ledger_issue": ledger_issue,
        "verified": False,
    }
    try:
        time.sleep(float(cfg.get("settle_seconds", 8)))
        before_service = service_status()
        before_health = companion("/health")
        result["before"] = {"service": before_service, "health": before_health}
        if not before_service["running"]:
            raise RuntimeError("precondition failed: SolBridge was not running before fault injection")
        before_attempt = int(before_health.get("guardian_last_attempt_ms") or 0)

        result["fault"] = service_down()
        time.sleep(2)
        observed_down = service_status()
        result["observed_down"] = observed_down
        if observed_down["running"]:
            raise RuntimeError("fault injection failed: SolBridge did not remain down")

        deadline = time.time() + float(cfg.get("recovery_timeout_seconds", 150))
        samples = []
        recovered = False
        guardian_advanced = False
        heartbeat_resumed = False
        final_health = None
        final_service = None
        while time.time() < deadline:
            try:
                h = companion("/health")
            except Exception as e:
                h = {"error": f"{type(e).__name__}: {e}"}
            s = service_status()
            attempt = int(h.get("guardian_last_attempt_ms") or 0) if isinstance(h, dict) else 0
            guardian_advanced = guardian_advanced or attempt > before_attempt
            heartbeat_age = int(h.get("heartbeat_age_ms") or 10**9) if isinstance(h, dict) else 10**9
            if len(samples) < 40:
                samples.append({
                    "t": round(time.time() - result["started_at"], 2),
                    "service": s,
                    "guardian_attempt_ms": attempt,
                    "guardian_dispatch": h.get("guardian_dispatch") if isinstance(h, dict) else None,
                    "guardian_error": h.get("guardian_error") if isinstance(h, dict) else None,
                    "heartbeat_age_ms": heartbeat_age,
                })
            if s["running"] and guardian_advanced:
                recovered = True
                # Give the restarted agent enough time for one poll-loop heartbeat.
                for _ in range(20):
                    time.sleep(1)
                    h2 = companion("/health")
                    age2 = int(h2.get("heartbeat_age_ms") or 10**9)
                    if age2 < 30_000:
                        heartbeat_resumed = True
                        final_health = h2
                        break
                final_service = service_status()
                if heartbeat_resumed:
                    break
            time.sleep(3)

        if final_service is None:
            final_service = service_status()
        if final_health is None:
            try:
                final_health = companion("/health")
            except Exception as e:
                final_health = {"error": f"{type(e).__name__}: {e}"}
        result["samples"] = samples
        result["final"] = {"service": final_service, "health": final_health}
        result["checks"] = {
            "was_running_before": bool(before_service["running"]),
            "observed_down": not bool(observed_down["running"]),
            "guardian_attempt_advanced": bool(guardian_advanced),
            "service_recovered": bool(recovered and final_service["running"]),
            "heartbeat_resumed": bool(heartbeat_resumed),
        }
        result["verified"] = all(result["checks"].values())
        if not result["verified"]:
            result["failure"] = "one or more recovery proof checks failed"
    except Exception as e:
        result["failure"] = f"{type(e).__name__}: {e}"
    result["finished_at"] = time.time()
    try:
        result["ledger_post"] = post_ledger(repo, ledger_issue, result)
    except Exception as e:
        result["ledger_post"] = {"error": f"{type(e).__name__}: {e}"}
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("verified") else 2


def launch(config_path: Path):
    if not config_path.exists():
        raise RuntimeError(f"fault-test config missing: {config_path}")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    log_handle = LOG.open("ab", buffering=0)
    p = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "--worker", str(config_path)],
        stdin=subprocess.DEVNULL,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        close_fds=True,
    )
    print(json.dumps({
        "queued": True,
        "worker_pid": p.pid,
        "config": str(config_path),
        "log": str(LOG),
        "note": "Detached worker will stop SolBridge after this command returns, then independently record recovery proof to GitHub.",
    }, indent=2))
    return 0


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--worker":
        raise SystemExit(worker(Path(sys.argv[2])))
    config = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONFIG
    raise SystemExit(launch(config))


if __name__ == "__main__":
    main()
