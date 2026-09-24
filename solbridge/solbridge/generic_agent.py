"""Generic persistent execution loop for the SolBridge mobile chat harness.

The standing chat agent treats an idle user message as a new task. While a task
is open, later messages refine that same task. Each cycle plans one observable
action, executes it, checks evidence, and continues. Repeated failure triggers
ontological abstraction and a materially different route.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path.home() / "solbridge-workspace"
MODEL = ROOT / "models" / "qwen3-1.7b-q4_k_m.gguf"
WORK = ROOT / "agent-work"
TOOLS = (
    "capability_scan", "reason", "shell", "web_get", "open_url",
    "launch_package", "adb_shell", "write_workspace", "run_workspace",
)


def _event(data: dict, kind: str, detail: dict) -> None:
    data.setdefault("events", []).append({"at": time.time(), "kind": kind, "detail": detail})
    data["events"] = data["events"][-300:]


def _chat(data: dict, role: str, text: str) -> None:
    data.setdefault("chat", []).append({"role": role, "text": str(text)[:1500], "at": time.time()})
    data["chat"] = data["chat"][-120:]


def active_goal(data: dict) -> str:
    if data.get("mode") == "chat_agent":
        return str(data.get("active_task") or "").strip()
    return str(data.get("statement") or "").strip()


def submit_message(data: dict, text: str) -> None:
    text = str(text).strip()
    if data.get("mode") == "chat_agent" and data.get("status") in ("IDLE", "PASS", "DONE"):
        data["active_task"] = text
        data["last_task"] = text
        data["status"] = "OPEN"
        data["blocker"] = "Task accepted; no action has been attempted yet."
        data["nextAction"] = "Reason, act, observe, verify, then continue without another prompt."
        data["generic"] = {"cycle": 0, "evidence": [], "attempts": [], "fail_streak": 0}
        data["abstraction_stack"] = []
        _chat(data, "user", text)
        _event(data, "task_started", {"task": text[:500]})
        return
    _chat(data, "user", text)
    _event(data, "user_note", {"text": text})
    data.setdefault("generic", {})["latest_user_note"] = text


def _extract_json(text: str) -> dict:
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if not match:
        raise ValueError("model returned no JSON object")
    return json.loads(match.group(0))


def _model(prompt: str, tokens=300, temp=0.2, timeout=110) -> str:
    if not MODEL.exists() or not shutil.which("llama-cli"):
        raise RuntimeError("local model unavailable")
    cmd = [
        shutil.which("llama-cli"), "-m", str(MODEL), "-p", prompt + " /no_think",
        "-n", str(tokens), "-c", "2048", "--temp", str(temp),
        "--no-display-prompt", "--simple-io", "--single-turn",
    ]
    out = subprocess.run(
        cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=timeout
    )
    if out.returncode:
        raise RuntimeError(f"local model exit {out.returncode}: {out.stderr[-300:]}")
    return re.sub(r"<think>[\s\S]*?</think>", "", out.stdout).strip()


def _model_json(prompt: str, tokens=320, temp=0.2) -> dict:
    return _extract_json(_model(prompt, tokens=tokens, temp=temp))


def _run(argv, timeout=35, cwd=None) -> dict:
    started = time.monotonic()
    try:
        done = subprocess.run(
            argv,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=timeout,
        )
        return {
            "ok": done.returncode == 0,
            "returncode": done.returncode,
            "stdout": done.stdout[-7000:],
            "stderr": done.stderr[-2500:],
            "elapsed": round(time.monotonic() - started, 2),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {str(exc)[:500]}",
            "elapsed": round(time.monotonic() - started, 2),
        }


def capability_snapshot() -> dict:
    bins = (
        "python", "git", "gh", "curl", "adb", "am", "termux-open-url",
        "termux-clipboard-get", "termux-clipboard-set", "llama-cli", "cloudflared",
    )
    result = {"ok": True, "binaries": {name: bool(shutil.which(name)) for name in bins}}
    if shutil.which("adb"):
        result["adb"] = _run(["adb", "devices", "-l"], timeout=12)
    gemini = Path.home() / "gemini"
    result["gemini_repo"] = gemini.is_dir()
    if gemini.is_dir() and shutil.which("git"):
        result["gemini_head"] = _run(
            ["git", "-C", str(gemini), "rev-parse", "--short", "HEAD"], timeout=12
        )
        result["gemini_status"] = _run(
            ["git", "-C", str(gemini), "status", "--short"], timeout=12
        )
    return result


def _safe_rel(path: str) -> Path:
    rel = Path(path)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("workspace path must be relative")
    WORK.mkdir(parents=True, exist_ok=True)
    root = WORK.resolve()
    target = (WORK / rel).resolve()
    if target != root and root not in target.parents:
        raise ValueError("workspace path escapes root")
    return target


def _safe_shell_argv(command: str) -> list[str]:
    if any(x in command for x in ("\n", "\r", ";", "&&", "||", "|", ">", "<", "$(")):
        raise ValueError("shell metacharacters are not accepted")
    argv = shlex.split(command)
    if not argv:
        raise ValueError("empty command")
    exe = Path(argv[0]).name
    allowed = {
        "pwd", "ls", "find", "cat", "head", "tail", "grep", "rg", "du", "df", "ps",
        "which", "git", "gh", "python", "python3", "getprop", "settings", "dumpsys",
        "pm", "cmd", "adb",
    }
    if exe not in allowed:
        raise ValueError("command executable is not registered")
    padded = " " + " ".join(argv).lower() + " "
    denied = (
        " rm ", " rmdir ", " git push ", " git reset ", " git clean ", " git checkout ",
        " git switch ", " gh auth token ", " gh secret ", " gh issue create ",
        " gh pr create ", " gh api --method ", " pm uninstall ", " reboot ", " shutdown ",
        " poweroff ", " mkfs ", " dd ",
    )
    if any(token in padded for token in denied):
        raise ValueError("command is outside autonomous non-destructive execution")
    if exe in ("python", "python3"):
        if len(argv) < 2 or argv[1] in ("-c", "-m"):
            raise ValueError("python must run a workspace file")
        argv[1] = str(_safe_rel(argv[1]))
    return argv


def plan(data: dict, abstract=False) -> dict:
    goal = active_goal(data)
    g = data.setdefault("generic", {})
    evidence = g.get("evidence", [])[-6:]
    attempts = g.get("attempts", [])[-10:]
    chat_tail = [
        {"role": x.get("role"), "text": x.get("text", "")[:500]}
        for x in data.get("chat", [])[-8:]
    ]
    mode = (
        "The last route is blocked or repeating. Perform ONTOLOGICAL abstraction, not analogy: "
        "rewrite the blocker as entities, relations, constraints, controls, invariants, failure "
        "state and required transition; map one structurally similar foreign domain back into a "
        "materially different executable route. "
        if abstract
        else "Choose the single highest-value next action. "
    )
    prompt = (
        "You are the planner inside Ryan's persistent Pixel execution agent. Preserve the literal "
        "task and all later corrections. Do not stop at advice when an available action can advance "
        "it. Do not claim completion without observed evidence. Operate only with available authority "
        "on Ryan's device/accounts and avoid destructive or irreversible operations. "
        + mode
        + 'Return ONLY JSON: {"reply":"brief conversational update or empty",'
          '"blocker":"current concrete blocker","why":"why this action advances the task",'
          '"action":{"tool":"one registered tool","args":{}},'
          '"ontology":{"entities":"","relations":"","constraints":"","controls":"",'
          '"invariants":"","failure":"","transition":""},'
          '"foreign":{"domain":"","mechanism":"","mapping":"","weak_point":""}}. '
          "ontology/foreign may be empty unless abstraction was requested. "
          "Tools: capability_scan {}; reason {prompt}; shell {command}; web_get {url}; "
          "open_url {url}; launch_package {package}; adb_shell {command}; "
          "write_workspace {path,text}; run_workspace {path}. "
          "shell is argv-style and rejects shell metacharacters/destructive operations. "
          "write/run_workspace can engineer and test a new local capability when primitives are insufficient. "
        + f"TASK={goal[:1200]} "
        + f"CHAT={json.dumps(chat_tail, ensure_ascii=False)[-3500:]} "
        + f"BLOCKER={str(data.get('blocker',''))[:700]} "
        + f"RECENT_EVIDENCE={json.dumps(evidence, ensure_ascii=False)[-4500:]} "
        + f"ATTEMPTS={json.dumps(attempts, ensure_ascii=False)[-2200:]}"
    )
    obj = _model_json(prompt, tokens=380, temp=0.3 if abstract else 0.18)
    action = obj.get("action") if isinstance(obj.get("action"), dict) else {}
    tool = str(action.get("tool", "")).strip()
    if tool not in TOOLS:
        raise ValueError("planner returned an unregistered tool")
    args = action.get("args") if isinstance(action.get("args"), dict) else {}
    return {
        "reply": str(obj.get("reply", ""))[:700],
        "blocker": str(obj.get("blocker", ""))[:700],
        "why": str(obj.get("why", ""))[:700],
        "action": {"tool": tool, "args": args},
        "ontology": obj.get("ontology") if isinstance(obj.get("ontology"), dict) else {},
        "foreign": obj.get("foreign") if isinstance(obj.get("foreign"), dict) else {},
    }


def execute(action: dict, goal: str) -> dict:
    tool = action["tool"]
    args = action.get("args") or {}

    if tool == "capability_scan":
        return capability_snapshot()

    if tool == "reason":
        prompt = str(args.get("prompt") or goal)[:5000]
        try:
            answer = _model(
                "Answer this task directly and concretely using only known context. TASK=" + prompt,
                tokens=460,
                temp=0.25,
            )
            return {"ok": True, "text": answer[:7000]}
        except Exception as exc:
            return {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:500]}"}

    if tool == "shell":
        try:
            argv = _safe_shell_argv(str(args.get("command", ""))[:1200])
            return _run(argv, timeout=50, cwd=WORK)
        except Exception as exc:
            return {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:500]}"}

    if tool == "web_get":
        url = str(args.get("url", ""))[:1800]
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("https", "http") or not parsed.hostname:
            return {"ok": False, "error": "web_get requires an absolute http(s) URL"}
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SolBridge-Agent/2"})
            with urllib.request.urlopen(req, timeout=25) as response:
                body = response.read(250000).decode("utf-8", "replace")
                return {
                    "ok": 200 <= response.status < 400,
                    "status": response.status,
                    "url": response.geturl(),
                    "text": body[:12000],
                }
        except Exception as exc:
            return {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:500]}"}

    if tool == "open_url":
        url = str(args.get("url", ""))[:1800]
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("https", "http") or not parsed.hostname:
            return {"ok": False, "error": "open_url requires http(s)"}
        if shutil.which("termux-open-url"):
            return _run(["termux-open-url", url], timeout=15)
        if shutil.which("am"):
            return _run(
                ["am", "start", "-a", "android.intent.action.VIEW", "-d", url], timeout=20
            )
        return {"ok": False, "error": "no URL launcher available"}

    if tool == "launch_package":
        package = str(args.get("package", ""))
        if not re.fullmatch(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+", package):
            return {"ok": False, "error": "invalid package"}
        if shutil.which("monkey"):
            return _run(["monkey", "-p", package, "1"], timeout=20)
        if shutil.which("am"):
            return _run(
                [
                    "am", "start", "-a", "android.intent.action.MAIN",
                    "-c", "android.intent.category.LAUNCHER", "-p", package,
                ],
                timeout=20,
            )
        return {"ok": False, "error": "no package launcher available"}

    if tool == "adb_shell":
        if not shutil.which("adb"):
            return {"ok": False, "error": "adb unavailable"}
        command = str(args.get("command", ""))[:1200]
        try:
            argv = _safe_shell_argv("adb " + command)
            return _run(argv, timeout=35)
        except Exception as exc:
            return {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:500]}"}

    if tool == "write_workspace":
        try:
            target = _safe_rel(str(args.get("path", ""))[:300])
            text = str(args.get("text", ""))[:20000]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
            return {"ok": True, "path": str(target), "bytes": len(text.encode())}
        except Exception as exc:
            return {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:500]}"}

    if tool == "run_workspace":
        try:
            target = _safe_rel(str(args.get("path", ""))[:300])
            if target.suffix != ".py" or not target.exists():
                return {"ok": False, "error": "run_workspace requires an existing .py file"}
            return _run([shutil.which("python") or "python", str(target)], timeout=75, cwd=WORK)
        except Exception as exc:
            return {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:500]}"}

    return {"ok": False, "error": "unknown generic tool"}


def verify(data: dict) -> dict:
    goal = active_goal(data)
    evidence = data.setdefault("generic", {}).get("evidence", [])[-8:]
    if not evidence:
        return {"complete": False, "missing": "No observed evidence yet.", "reason": ""}
    prompt = (
        "Act only as a completion verifier. Decide whether OBSERVED evidence is sufficient to establish "
        "the user's literal task is complete. A zero exit code is not enough unless its output proves the "
        "requested state. Do not assume unobserved consequences. Return ONLY JSON "
        '{"complete":false,"reason":"what evidence establishes","missing":"specific remaining gap"}. '
        + f"TASK={goal[:1400]} EVIDENCE={json.dumps(evidence, ensure_ascii=False)[-8000:]}"
    )
    try:
        obj = _model_json(prompt, tokens=230, temp=0.05)
        return {
            "complete": obj.get("complete") is True,
            "reason": str(obj.get("reason", ""))[:900],
            "missing": str(obj.get("missing", ""))[:900],
        }
    except Exception as exc:
        return {
            "complete": False,
            "reason": "",
            "missing": f"verification failed: {type(exc).__name__}: {str(exc)[:300]}",
        }


def completion_reply(data: dict, verification: dict) -> str:
    goal = active_goal(data)
    evidence = data.setdefault("generic", {}).get("evidence", [])[-5:]
    prompt = (
        "Give Ryan the result of this completed task in direct casual prose. Lead with the result, "
        "include only material evidence, and do not describe hidden reasoning. "
        + "TASK=" + goal[:1200]
        + " VERIFIED=" + json.dumps(verification, ensure_ascii=False)
        + " EVIDENCE=" + json.dumps(evidence, ensure_ascii=False)[-6000:]
    )
    try:
        return _model(prompt, tokens=280, temp=0.2)[:1400]
    except Exception:
        return str(verification.get("reason") or "Completed and verified.")[:1400]


def cycle_inplace(data: dict) -> dict:
    if data.get("mode") == "chat_agent" and data.get("status") == "IDLE":
        return {"status": "IDLE"}

    goal = active_goal(data)
    if not goal:
        if data.get("mode") == "chat_agent":
            data["status"] = "IDLE"
            return {"status": "IDLE"}
        data["status"] = "OPEN"
        data["blocker"] = "No active task text."
        return {"status": "OPEN", "transition": "await_task"}

    g = data.setdefault(
        "generic", {"cycle": 0, "evidence": [], "attempts": [], "fail_streak": 0}
    )
    g["cycle"] = int(g.get("cycle", 0)) + 1
    abstract = int(g.get("fail_streak", 0)) >= 2

    try:
        chosen = plan(data, abstract=abstract)
    except Exception as exc:
        data["blocker"] = f"Planner failed: {type(exc).__name__}: {str(exc)[:320]}"
        data["nextAction"] = (
            "Retry planning; if the same failure repeats, capability-scan and derive a different route."
        )
        g["fail_streak"] = int(g.get("fail_streak", 0)) + 1
        _event(data, "generic_planner_error", {"error": data["blocker"], "cycle": g["cycle"]})
        return {"status": "OPEN", "transition": "planner_retry"}

    signature = hashlib.sha256(
        json.dumps(chosen["action"], sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:16]
    recent = [x.get("signature") for x in g.get("attempts", [])[-4:]]

    if signature in recent and not abstract:
        try:
            chosen = plan(data, abstract=True)
            signature = hashlib.sha256(
                json.dumps(chosen["action"], sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest()[:16]
            abstract = True
        except Exception:
            pass

    if chosen.get("reply"):
        _chat(data, "assistant", chosen["reply"])

    if abstract:
        frame = {
            "kind": "generic_abstraction",
            "depth": len(data.setdefault("abstraction_stack", [])),
            "blocker": chosen.get("blocker") or data.get("blocker"),
            "ontology": chosen.get("ontology", {}),
            "foreign": chosen.get("foreign", {}),
            "action": chosen["action"],
            "at": time.time(),
        }
        data["abstraction_stack"].append(frame)
        data["abstraction_stack"] = data["abstraction_stack"][-20:]
        _event(data, "generic_ontological_abstraction", frame)

    result = execute(chosen["action"], goal)
    attempt = {
        "at": time.time(),
        "cycle": g["cycle"],
        "signature": signature,
        "why": chosen.get("why"),
        "action": chosen["action"],
        "result": result,
    }
    g.setdefault("attempts", []).append(attempt)
    g["attempts"] = g["attempts"][-40:]
    g.setdefault("evidence", []).append(
        {"action": chosen["action"], "observation": result, "at": time.time()}
    )
    g["evidence"] = g["evidence"][-30:]
    _event(data, "generic_action_executed", attempt)

    if result.get("ok"):
        g["fail_streak"] = 0
    else:
        g["fail_streak"] = int(g.get("fail_streak", 0)) + 1

    verdict = verify(data)
    g["last_verification"] = verdict
    _event(data, "generic_verification", verdict)

    if verdict.get("complete") is True and result.get("ok"):
        reply = completion_reply(data, verdict)
        _chat(data, "assistant", reply)
        _event(data, "task_verified_complete", {"goal": goal[:800], "verification": verdict})
        data["last_completed_task"] = goal
        data["last_completion"] = verdict
        data["status"] = "IDLE" if data.get("mode") == "chat_agent" else "PASS"
        data["blocker"] = ""
        data["nextAction"] = (
            "Waiting for your next message." if data.get("mode") == "chat_agent" else "Complete."
        )
        if data.get("mode") == "chat_agent":
            data["active_task"] = ""
        return {"status": data["status"], "transition": "verified_complete"}

    data["status"] = "OPEN"
    data["blocker"] = (
        verdict.get("missing") or chosen.get("blocker") or "Objective remains unverified."
    )
    data["nextAction"] = (
        "Continue automatically from the remaining gap. Reuse verified procedures when applicable; "
        "after repeated failure, abstract the blocker and test a materially different route."
    )
    return {
        "status": "OPEN",
        "transition": "continue",
        "action": chosen["action"]["tool"],
        "action_ok": bool(result.get("ok")),
        "abstracted": abstract,
    }
