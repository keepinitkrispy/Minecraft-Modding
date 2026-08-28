from __future__ import annotations
import json, signal, sys, time, traceback
from .config import Config
from .github_bus import GitHubBus
from .tools import execute

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

def process(bus: GitHubBus, cfg: Config, issue: dict):
    number = issue["number"]
    try:
        cmd = parse_command(issue)
        target = cmd.get("device_id")
        if target not in (None, "*", cfg.device_id):
            return
        bus.labels(number, ["solbridge-command", "solbridge-running"])
        started = time.time()
        output = execute(cfg, str(cmd["tool"]), dict(cmd.get("args") or {}))
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
        except Exception:
            print(json.dumps(result), file=sys.stderr, flush=True)

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
                process(bus, cfg, issue)
        except Exception as e:
            print(f"poll error: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        for _ in range(max(cfg.poll_seconds, 1)):
            if STOP: break
            time.sleep(1)

if __name__ == "__main__":
    main()
