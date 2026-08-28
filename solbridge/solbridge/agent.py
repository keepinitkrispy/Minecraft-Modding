from __future__ import annotations
import json, os, signal, sys, time, traceback
from pathlib import Path
from .config import Config
from .github_bus import GitHubBus
from .tools import execute
from .companion import execute_companion
from .autoloop import execute_autoloop

STOP = False

def stop(*_):
    global STOP
    STOP = True

def parse_command(issue: dict) -> dict:
    body = (issue.get("body") or "").strip()
    if body.startswith("```"):
        lines = body.splitlines()
        if lines and lines[0].startswith("```"): lines = lines[1:]
        if lines and lines[-1].startswith("```"): lines = lines[:-1]
        body = "\n".join(lines)
    return json.loads(body)

def result_block(data: dict) -> str:
    return "```json\n" + json.dumps(data, indent=2, ensure_ascii=False)[:60000] + "\n```"

def _authorized_actor(issue: dict, cfg: Config) -> bool:
    actor = str((issue.get("user") or {}).get("login") or "")
    owner = cfg.repo.split("/", 1)[0]
    return bool(actor) and actor.lower() == owner.lower()

def _processed_path(cfg: Config) -> Path:
    return cfg.workspace / ".solbridge_processed_issues.json"

def _processed(cfg: Config) -> set[int]:
    p = _processed_path(cfg)
    try:
        raw = json.loads(p.read_text()) if p.exists() else []
        return {int(x) for x in raw}
    except Exception:
        return set()

def _mark_processed(cfg: Config, number: int) -> None:
    seen = _processed(cfg)
    seen.add(int(number))
    newest = sorted(seen)[-1000:]
    p = _processed_path(cfg)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(newest))
    tmp.replace(p)

def process(bus: GitHubBus, cfg: Config, issue: dict) -> bool:
    number = int(issue["number"])
    if number in _processed(cfg):
        try:
            bus.labels(number, ["solbridge-done"])
            bus.close(number)
        except Exception:
            pass
        return False
    try:
        if not _authorized_actor(issue, cfg):
            raise PermissionError("Command issue author is not the SolBridge bus owner")
        cmd = parse_command(issue)
        target = cmd.get("device_id")
        if target not in (None, "*", cfg.device_id):
            return False
        bus.labels(number, ["solbridge-command", "solbridge-running"])
        started = time.time()
        tool = str(cmd["tool"])
        if tool == "companion":
            output = execute_companion(cfg, dict(cmd.get("args") or {}))
        elif tool == "autoloop":
            output = execute_autoloop(cfg, dict(cmd.get("args") or {}))
        else:
            output = execute(cfg, tool, dict(cmd.get("args") or {}))
        restart = bool(isinstance(output, dict) and output.pop("_restart_agent", False))
        result = {
            "solbridge": 1,
            "status": "ok",
            "device_id": cfg.device_id,
            "command_id": cmd.get("id"),
            "tool": cmd.get("tool"),
            "elapsed_ms": int((time.time() - started) * 1000),
            "result": output,
        }
        bus.comment(number, result_block(result))
        bus.labels(number, ["solbridge-done"])
        bus.close(number)
        _mark_processed(cfg, number)
        return restart
    except Exception as e:
        result = {
            "solbridge": 1,
            "status": "error",
            "device_id": cfg.device_id,
            "error": f"{type(e).__name__}: {e}",
            "traceback": traceback.format_exc(limit=8),
        }
        try:
            bus.comment(number, result_block(result))
            bus.labels(number, ["solbridge-error"])
            bus.close(number)
            _mark_processed(cfg, number)
        except Exception:
            print(json.dumps(result), file=sys.stderr, flush=True)
        return False

def main():
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    cfg = Config.load()
    cfg.workspace.mkdir(parents=True, exist_ok=True)
    bus = GitHubBus(cfg.repo, cfg.token)
    bus.ensure_labels()
    print(f"SolBridge online: {cfg.device_id} -> {cfg.repo}", flush=True)
    while not STOP:
        try:
            for issue in bus.pending():
                if process(bus, cfg, issue):
                    os.execv(sys.executable, [sys.executable, "-m", "solbridge.agent"])
        except Exception as e:
            print(f"poll error: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        for _ in range(max(cfg.poll_seconds, 1)):
            if STOP: break
            time.sleep(1)

if __name__ == "__main__":
    main()
