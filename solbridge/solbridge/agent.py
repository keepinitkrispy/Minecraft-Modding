from __future__ import annotations
import base64, fcntl, json, os, signal, sys, time, traceback
from pathlib import Path
from .config import Config
from .github_bus import GitHubBus
from .tools import execute
from .companion import execute_companion, _get as companion_get
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

OUTCOME_GATE_URL = "https://keepinitkrispy.github.io/Persistent-Fable/"

def _is_outcome_gate_state(state: object) -> bool:
    if not isinstance(state, dict) or state.get("schemaVersion") != 1:
        return False
    objectives = state.get("objectives")
    active_id = state.get("activeId")
    return (
        isinstance(objectives, list)
        and len(objectives) <= 1000
        and isinstance(active_id, str)
        and any(isinstance(item, dict) and item.get("id") == active_id for item in objectives)
    )

def _verify_active_objective_write(cfg: Config, cmd: dict, output: dict) -> dict | None:
    args = cmd.get("args")
    if cmd.get("tool") != "write_text" or not isinstance(args, dict):
        return None
    if args.get("path") != "objectives/active.json":
        return None
    expected_text = args.get("text")
    if not isinstance(expected_text, str):
        raise RuntimeError("active objective write payload is not text")
    readback = execute(cfg, "read_text", {"path": "objectives/active.json"})
    if not isinstance(readback, dict) or readback.get("truncated") or readback.get("text") != expected_text:
        raise RuntimeError("active objective write did not match its phone read-back")
    try:
        state = json.loads(readback["text"])
    except Exception as error:
        raise RuntimeError("phone read-back is not valid JSON") from error
    if not _is_outcome_gate_state(state):
        raise RuntimeError("phone read-back is not a valid active Outcome Gate state")
    output["readback_verified"] = True
    return state

def _outcome_gate_return_link(issue_number: int, cmd: dict, device_id: str, state: dict, result: dict) -> str | None:
    args = cmd.get("args")
    tool_result = result.get("result")
    if (
        cmd.get("tool") != "write_text"
        or not isinstance(args, dict)
        or args.get("path") != "objectives/active.json"
        or not _is_outcome_gate_state(state)
        or result.get("status") != "ok"
        or not isinstance(tool_result, dict)
        or tool_result.get("readback_verified") is not True
    ):
        return None
    receipt = {
        "schema": "outcome-gate-phone-receipt/v1",
        "state": state,
        "status": "ok",
        "device_id": device_id,
        "command_id": result.get("command_id"),
        "issue_number": int(issue_number),
        "tool": "write_text",
        "path": "objectives/active.json",
        "readback_verified": True,
        "bytes": tool_result.get("bytes"),
    }
    raw = json.dumps(receipt, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    encoded = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    if len(encoded) > 12000:
        return None
    return OUTCOME_GATE_URL + "#bridge-state=" + encoded

def _authorized_actor(issue: dict, cfg: Config, bus: GitHubBus, cmd: dict) -> bool:
    actor = str((issue.get("user") or {}).get("login") or "")
    owner = cfg.repo.split("/", 1)[0]
    if actor and actor.lower() == owner.lower():
        return True
    if actor.lower() != "github-actions[bot]":
        return False
    ingress = cmd.get("_ingress")
    if not isinstance(ingress, dict) or ingress.get("type") != "owner-command-file":
        return False
    path = str(ingress.get("path") or "")
    commit_sha = str(ingress.get("commit") or "")
    expected = dict(cmd)
    expected.pop("_ingress", None)
    return bus.verify_owner_command_file(path=path, commit_sha=commit_sha, expected=expected)

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

def _heartbeat() -> bool:
    try:
        result = companion_get("/heartbeat", timeout=3.0)
        return bool(isinstance(result, dict) and result.get("ok"))
    except Exception:
        return False

def _execution_failure(tool: str, output) -> str | None:
    """Return a failure reason when a tool result proves execution failed.

    The agent is the authoritative completion boundary. A command is only
    solbridge-done when its subprocess AND its tool-level result say it worked.
    """
    if not isinstance(output, dict):
        return None

    rc = output.get("returncode")
    if isinstance(rc, int) and not isinstance(rc, bool) and rc != 0:
        return f"{tool} returned nonzero exit status {rc}"

    if tool == "workflow":
        steps = output.get("steps")
        if not isinstance(steps, list):
            return "workflow returned no valid steps list"
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                return f"workflow step {i} returned an invalid result"
            if step.get("status") == "error":
                return f"workflow step {i} ({step.get('tool', 'unknown')}) failed: {step.get('error', 'unknown error')}"
            result = step.get("result")
            if isinstance(result, dict):
                step_rc = result.get("returncode")
                if isinstance(step_rc, int) and not isinstance(step_rc, bool) and step_rc != 0:
                    return f"workflow step {i} ({step.get('tool', 'unknown')}) returned nonzero exit status {step_rc}"
        return None

    if tool == "companion":
        if output.get("ok") is False:
            return f"companion action failed: {output.get('error', 'ok=false')}"
        if output.get("verified") is False:
            return f"companion verification failed: {output.get('failure', output.get('error', 'verified=false'))}"
        for name, value in output.items():
            if isinstance(value, dict) and value.get("ok") is False:
                return f"companion {name} failed: {value.get('error', 'ok=false')}"
        return None

    return None

def process(bus: GitHubBus, cfg: Config, issue: dict) -> bool:
    number = int(issue["number"])
    if number in _processed(cfg):
        try:
            bus.close(number)
        except Exception:
            pass
        return False

    output = None
    cmd = None
    try:
        cmd = parse_command(issue)
        if not _authorized_actor(issue, cfg, bus, cmd):
            raise PermissionError("Command provenance is not authorized")
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
        failure = _execution_failure(tool, output)
        if failure:
            raise RuntimeError(failure)
        verified_gate_state = _verify_active_objective_write(cfg, cmd, output) if isinstance(output, dict) else None
        result = {
            "solbridge": 1,
            "status": "ok",
            "device_id": cfg.device_id,
            "command_id": cmd.get("id"),
            "tool": cmd.get("tool"),
            "elapsed_ms": int((time.time() - started) * 1000),
            "result": output,
        }
        comment = result_block(result)
        return_url = _outcome_gate_return_link(number, cmd, cfg.device_id, verified_gate_state, result) if verified_gate_state else None
        if return_url:
            comment += f"\n\n[Open the saved goal in Outcome Gate]({return_url})"
        bus.comment(number, comment)
        bus.labels(number, ["solbridge-done"])
        bus.close(number)
        _mark_processed(cfg, number)
        return restart
    except Exception as e:
        result = {
            "solbridge": 1,
            "status": "error",
            "device_id": cfg.device_id,
            "command_id": cmd.get("id") if isinstance(cmd, dict) else None,
            "tool": cmd.get("tool") if isinstance(cmd, dict) else None,
            "error": f"{type(e).__name__}: {e}",
            "traceback": traceback.format_exc(limit=8),
        }
        if output is not None:
            result["result"] = output
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
    lock_handle = (cfg.workspace / ".solbridge-agent.lock").open("a+")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("SolBridge duplicate agent exiting", flush=True)
        lock_handle.close()
        return
    bus = GitHubBus(cfg.repo, cfg.token)
    bus.ensure_labels()
    print(f"SolBridge online: {cfg.device_id} -> {cfg.repo}", flush=True)
    while not STOP:
        _heartbeat()
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
