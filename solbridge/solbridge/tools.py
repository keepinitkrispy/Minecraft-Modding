from __future__ import annotations
import base64, hashlib, json, os, re, shutil, subprocess, time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from .config import Config

class ToolError(RuntimeError): pass

def run(cmd: list[str] | str, *, timeout=30, shell=False, cwd=None, input_text: str | None = None):
    try:
        p = subprocess.run(
            cmd,
            shell=shell,
            cwd=cwd,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {"returncode": p.returncode, "stdout": p.stdout[-20000:], "stderr": p.stderr[-20000:]}
    except subprocess.TimeoutExpired as e:
        return {
            "returncode": 124,
            "stdout": (e.stdout or "")[-20000:] if isinstance(e.stdout, str) else "",
            "stderr": ((e.stderr or "") if isinstance(e.stderr, str) else "")[-20000:] + "\nTIMEOUT",
        }

def run_json(cmd: list[str], *, timeout=30, cwd=None):
    r = run(cmd, timeout=timeout, cwd=cwd)
    if r["returncode"] != 0:
        return r
    try:
        r["json"] = json.loads(r["stdout"])
    except Exception:
        pass
    return r

def safe_path(cfg: Config, user_path: str) -> Path:
    cfg.workspace.mkdir(parents=True, exist_ok=True)
    base = cfg.workspace.resolve()
    p = (base / user_path).resolve() if not Path(user_path).is_absolute() else Path(user_path).resolve()
    if p != base and base not in p.parents:
        raise ToolError("Path escapes configured workspace")
    return p

def _require(command: str) -> None:
    if not shutil.which(command):
        raise ToolError(f"{command} is unavailable")

def _git_head(cfg: Config) -> str | None:
    if not (cfg.source_dir / ".git").exists():
        return None
    r = run(["git", "rev-parse", "--short=12", "HEAD"], cwd=cfg.source_dir)
    return r["stdout"].strip() if r["returncode"] == 0 else None

def health(cfg: Config, args: dict) -> dict:
    return {
        "ok": True,
        "device_id": cfg.device_id,
        "workspace": str(cfg.workspace),
        "source_dir": str(cfg.source_dir),
        "source_head": _git_head(cfg),
        "allow_shell": cfg.allow_shell,
        "time": int(time.time()),
        "python": shutil.which("python") or shutil.which("python3"),
        "termux_api": bool(shutil.which("termux-battery-status")),
        "rish": bool(shutil.which("rish")),
    }

CAPABILITY_COMMANDS = [
    "termux-battery-status", "termux-wifi-connectioninfo", "termux-location",
    "termux-sensor", "termux-camera-info", "termux-camera-photo",
    "termux-clipboard-get", "termux-clipboard-set", "termux-notification",
    "termux-notification-list", "termux-vibrate", "termux-tts-speak",
    "termux-speech-to-text", "termux-contact-list", "termux-call-log",
    "termux-telephony-deviceinfo", "termux-telephony-cellinfo", "termux-sms-list",
    "termux-sms-send", "termux-torch", "termux-volume", "termux-media-player",
    "termux-microphone-record", "termux-fingerprint", "termux-nfc",
    "termux-wallpaper", "termux-open-url", "am", "pm", "logcat", "getprop",
    "dumpsys", "ps", "ip", "pkg", "curl", "adb", "git", "python", "gh", "rish",
]

def capabilities(cfg: Config, args: dict) -> dict:
    return {
        "device_id": cfg.device_id,
        "source_head": _git_head(cfg),
        "available": {name: bool(shutil.which(name)) for name in CAPABILITY_COMMANDS},
        "tools": sorted(TOOLS.keys()),
        "shell_enabled": cfg.allow_shell,
    }

def _probe(name: str, cmd: list[str], timeout: int = 15) -> dict:
    if not shutil.which(cmd[0]):
        return {"status": "unavailable"}
    r = run(cmd, timeout=timeout)
    text = (r["stderr"] + "\n" + r["stdout"]).lower()
    if r["returncode"] == 0:
        return {"status": "ok", "returncode": 0}
    if r["returncode"] == 124:
        return {"status": "timeout", "returncode": 124}
    denied_tokens = ("permission", "denied", "not allowed", "securityexception")
    return {
        "status": "denied" if any(t in text for t in denied_tokens) else "error",
        "returncode": r["returncode"],
        "detail": (r["stderr"] or r["stdout"])[-500:],
    }

def permission_probe(cfg: Config, args: dict) -> dict:
    probes = {
        "battery": ["termux-battery-status"],
        "wifi": ["termux-wifi-connectioninfo"],
        "camera_info": ["termux-camera-info"],
        "sensors": ["termux-sensor", "-l"],
        "location": ["termux-location", "-p", "network", "-r", "once"],
        "volume": ["termux-volume"],
    }
    result = {name: _probe(name, cmd, 20 if name == "location" else 10) for name, cmd in probes.items()}
    result["sensitive_not_probed"] = [
        "contacts", "call_log", "sms", "clipboard", "microphone", "camera_photo",
        "notification_contents", "telephony_identity",
    ]
    return {"device_id": cfg.device_id, "probes": result}

def device_snapshot(cfg: Config, args: dict) -> dict:
    out: dict[str, Any] = {
        "device_id": cfg.device_id,
        "source_head": _git_head(cfg),
        "uname": run(["uname", "-a"]),
        "disk": run(["df", "-h", str(cfg.workspace)]),
        "load": run(["uptime"]),
    }
    if shutil.which("termux-battery-status"):
        out["battery"] = run_json(["termux-battery-status"])
    if shutil.which("termux-wifi-connectioninfo"):
        out["wifi"] = run_json(["termux-wifi-connectioninfo"])
    if shutil.which("getprop"):
        props = {}
        for key in (
            "ro.build.version.release", "ro.build.version.security_patch",
            "ro.product.model", "ro.product.manufacturer", "ro.product.cpu.abi",
        ):
            r = run(["getprop", key])
            props[key] = r["stdout"].strip()
        out["android"] = props
    return out

def system_inspect(cfg: Config, args: dict) -> dict:
    mode = str(args.get("mode", "summary"))
    if mode == "summary":
        return {
            "processes": run(["ps", "-A", "-o", "PID,PPID,NAME"], timeout=20),
            "network": run(["ip", "-brief", "addr"], timeout=20),
            "routes": run(["ip", "route"], timeout=20),
            "memory": run(["cat", "/proc/meminfo"], timeout=20),
        }
    if mode == "logs":
        n = max(20, min(int(args.get("lines", 200)), 1000))
        return {"logcat": run(["logcat", "-d", "-t", str(n)], timeout=30)}
    if mode == "packages":
        scope = str(args.get("scope", "user"))
        cmd = ["pm", "list", "packages"]
        if scope == "user":
            cmd.append("-3")
        elif scope == "system":
            cmd.append("-s")
        elif scope != "all":
            raise ToolError("scope must be user, system, or all")
        return {"packages": run(cmd, timeout=30)}
    raise ToolError("mode must be summary, logs, or packages")

def package_info(cfg: Config, args: dict) -> dict:
    package = str(args.get("package", "")).strip()
    if not re.fullmatch(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+", package):
        raise ToolError("invalid package name")
    return {
        "path": run(["pm", "path", package], timeout=20),
        "dump": run(["dumpsys", "package", package], timeout=30),
    }

def list_files(cfg: Config, args: dict) -> dict:
    p = safe_path(cfg, args.get("path", "."))
    limit = min(int(args.get("limit", 300)), 1000)
    if not p.exists(): raise ToolError("Path does not exist")
    if p.is_file(): return {"path": str(p), "type": "file", "size": p.stat().st_size}
    rows = []
    for child in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))[:limit]:
        rows.append({"name":child.name, "type":"dir" if child.is_dir() else "file", "size": child.stat().st_size if child.is_file() else None})
    return {"path":str(p), "entries":rows}

def read_text(cfg: Config, args: dict) -> dict:
    p = safe_path(cfg, args["path"])
    max_bytes = min(int(args.get("max_bytes", 200000)), 1000000)
    b = p.read_bytes()[:max_bytes]
    return {"path":str(p), "text":b.decode("utf-8", errors="replace"), "truncated":p.stat().st_size > len(b)}

def write_text(cfg: Config, args: dict) -> dict:
    p = safe_path(cfg, args["path"])
    p.parent.mkdir(parents=True, exist_ok=True)
    text = str(args.get("text", ""))
    p.write_text(text)
    return {"path":str(p), "bytes":len(text.encode())}

STATE_FILE = ".solbridge_state.json"

def state_get(cfg: Config, args: dict) -> dict:
    p = safe_path(cfg, STATE_FILE)
    if not p.exists():
        return {"state": {}}
    try:
        data = json.loads(p.read_text())
    except Exception:
        data = {}
    key = args.get("key")
    return {"value": data.get(str(key))} if key is not None else {"state": data}

def state_set(cfg: Config, args: dict) -> dict:
    p = safe_path(cfg, STATE_FILE)
    try:
        data = json.loads(p.read_text()) if p.exists() else {}
    except Exception:
        data = {}
    key = str(args["key"])
    if len(key) > 200:
        raise ToolError("state key too long")
    data[key] = args.get("value")
    raw = json.dumps(data, ensure_ascii=False, indent=2)
    if len(raw.encode()) > 1_000_000:
        raise ToolError("state file would exceed 1 MB")
    p.write_text(raw)
    return {"saved": True, "key": key}

def git(cfg: Config, args: dict) -> dict:
    path = safe_path(cfg, args.get("path", "."))
    op = args.get("op", "status")
    commands = {
        "status": ["git", "status", "--short", "--branch"],
        "diff": ["git", "diff", "--"],
        "log": ["git", "log", "--oneline", "-20"],
        "pull": ["git", "pull", "--ff-only"],
    }
    if op not in commands: raise ToolError(f"Unsupported git op: {op}")
    return run(commands[op], timeout=120, cwd=path)

def termux_package(cfg: Config, args: dict) -> dict:
    op = str(args.get("op", "list")).strip()
    if op == "list":
        return run(["pkg", "list-installed"], timeout=120)
    if op == "upgrade":
        return run(["pkg", "upgrade", "-y"], timeout=600)
    if op != "install":
        raise ToolError("termux_package op must be list, install, or upgrade")
    raw = args.get("packages")
    packages = [str(x) for x in (raw if isinstance(raw, list) else [raw]) if x]
    if not packages or len(packages) > 20:
        raise ToolError("install requires 1-20 package names")
    for package in packages:
        if not re.fullmatch(r"[A-Za-z0-9+._-]{1,100}", package):
            raise ToolError(f"invalid Termux package name: {package}")
    return run(["pkg", "install", "-y", *packages], timeout=900)

def python_job(cfg: Config, args: dict) -> dict:
    p = safe_path(cfg, str(args.get("path", "")))
    if p.suffix.lower() != ".py":
        raise ToolError("python_job requires a .py file in the workspace")
    if not p.exists() or not p.is_file():
        raise ToolError("python_job file does not exist")
    if p.stat().st_size > 2_000_000:
        raise ToolError("python_job script exceeds 2 MB")
    argv = args.get("args") or []
    if not isinstance(argv, list) or len(argv) > 50:
        raise ToolError("python_job args must be a list of at most 50 values")
    argv = [str(v)[:2000] for v in argv]
    timeout = max(1, min(int(args.get("timeout", 120)), 900))
    return run(["python", str(p), *argv], timeout=timeout, cwd=p.parent)

def http_download(cfg: Config, args: dict) -> dict:
    url = str(args.get("url", "")).strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ToolError("http_download only allows http/https URLs")
    p = safe_path(cfg, str(args.get("path", "downloads/file.bin")))
    p.parent.mkdir(parents=True, exist_ok=True)
    max_bytes = max(1, min(int(args.get("max_bytes", 50_000_000)), 200_000_000))
    req = Request(url, headers={"User-Agent": "SolBridge/0.3"})
    h = hashlib.sha256()
    total = 0
    tmp = p.with_suffix(p.suffix + ".part")
    final_url = url
    try:
        with urlopen(req, timeout=60) as r, tmp.open("wb") as out:
            final_url = r.geturl()
            length = r.headers.get("Content-Length")
            if length and int(length) > max_bytes:
                raise ToolError("download exceeds configured size limit")
            while True:
                chunk = r.read(1024 * 256)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ToolError("download exceeded configured size limit")
                out.write(chunk)
                h.update(chunk)
        tmp.replace(p)
    finally:
        if tmp.exists() and not p.exists():
            tmp.unlink(missing_ok=True)
    return {"path": str(p), "bytes": total, "sha256": h.hexdigest(), "final_url": final_url}

def file_info(cfg: Config, args: dict) -> dict:
    p = safe_path(cfg, str(args.get("path", "")))
    if not p.exists() or not p.is_file():
        raise ToolError("file does not exist")
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return {"path": str(p), "bytes": p.stat().st_size, "sha256": h.hexdigest()}

def android_action(cfg: Config, args: dict) -> dict:
    name = str(args.get("name", "")).strip()
    if name == "battery":
        _require("termux-battery-status"); return run_json(["termux-battery-status"], timeout=45)
    if name == "wifi":
        _require("termux-wifi-connectioninfo"); return run_json(["termux-wifi-connectioninfo"], timeout=45)
    if name == "location":
        _require("termux-location")
        provider = str(args.get("provider", "network"))
        if provider not in {"gps", "network", "passive"}:
            raise ToolError("provider must be gps, network, or passive")
        return run_json(["termux-location", "-p", provider, "-r", "once"], timeout=60)
    if name in {"sensors", "sensors_list"}:
        _require("termux-sensor"); return run_json(["termux-sensor", "-l"], timeout=45)
    if name == "sensor_sample":
        _require("termux-sensor")
        sensor = str(args.get("sensor", "")).strip()
        if not sensor or len(sensor) > 160:
            raise ToolError("sensor_sample requires sensor name")
        count = max(1, min(int(args.get("count", 1)), 10))
        return run_json(["termux-sensor", "-s", sensor, "-n", str(count)], timeout=45)
    if name == "camera_info":
        _require("termux-camera-info"); return run_json(["termux-camera-info"], timeout=45)
    if name == "camera_photo":
        _require("termux-camera-photo")
        camera_id = max(0, min(int(args.get("camera_id", 0)), 10))
        p = safe_path(cfg, str(args.get("path", "camera/latest.jpg")))
        p.parent.mkdir(parents=True, exist_ok=True)
        r = run(["termux-camera-photo", "-c", str(camera_id), str(p)], timeout=60)
        r["path"] = str(p)
        r["bytes"] = p.stat().st_size if p.exists() else 0
        return r
    if name == "clipboard_get":
        _require("termux-clipboard-get"); return run(["termux-clipboard-get"], timeout=45)
    if name == "clipboard_set":
        _require("termux-clipboard-set")
        text = str(args.get("text", ""))[:100000]
        return run(["termux-clipboard-set"], timeout=45, input_text=text)
    if name == "notification_list":
        _require("termux-notification-list"); return run_json(["termux-notification-list"], timeout=45)
    if name == "notify":
        _require("termux-notification")
        title = str(args.get("title", "SolBridge"))[:160]
        content = str(args.get("content", ""))[:2000]
        notification_id = str(args.get("id", "solbridge"))[:80]
        return run(["termux-notification", "--id", notification_id, "--title", title, "--content", content], timeout=45)
    if name == "vibrate":
        _require("termux-vibrate")
        duration = max(1, min(int(args.get("duration_ms", 250)), 5000))
        return run(["termux-vibrate", "-d", str(duration)], timeout=45)
    if name == "tts":
        _require("termux-tts-speak")
        text = str(args.get("text", ""))[:4000]
        if not text: raise ToolError("tts requires text")
        return run(["termux-tts-speak", text], timeout=60)
    if name == "torch":
        _require("termux-torch")
        state = str(args.get("state", "off")).lower()
        if state not in {"on", "off"}:
            raise ToolError("torch state must be on or off")
        return run(["termux-torch", state], timeout=45)
    if name == "volume":
        _require("termux-volume"); return run_json(["termux-volume"], timeout=45)
    if name == "open_url":
        _require("termux-open-url")
        url = str(args.get("url", "")).strip()
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https", "market"}:
            raise ToolError("open_url only allows http, https, or market URLs")
        return run(["termux-open-url", url], timeout=45)
    if name == "launch_package":
        package = str(args.get("package", "")).strip()
        if not re.fullmatch(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+", package):
            raise ToolError("invalid package name")
        return run(["monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"], timeout=45)
    raise ToolError(f"Unsupported Android action: {name}")

def termux_api(cfg: Config, args: dict) -> dict:
    return android_action(cfg, args)

def adb_shell(cfg: Config, args: dict) -> dict:
    command = str(args.get("command", "")).strip()
    if not command:
        raise ToolError("adb_shell requires command")
    if len(command) > 20000:
        raise ToolError("adb_shell command too long")
    helper = safe_path(cfg, "native-pairer/target/release/adbexec")
    if not helper.exists() or not helper.is_file():
        raise ToolError("native ADB helper is not installed")
    timeout = max(8, min(int(args.get("timeout", 60)), 300))
    result = run([str(helper), command], timeout=timeout)
    result["authority"] = "android-shell"
    return result

def android_ui(cfg: Config, args: dict) -> dict:
    action = str(args.get("action", "state")).strip().lower()
    if action == "state":
        return adb_shell(cfg, {"command": "wm size; dumpsys window | grep -E 'mCurrentFocus|mFocusedApp' | head -4", "timeout": 30})
    if action == "dump":
        return adb_shell(cfg, {"command": "uiautomator dump /sdcard/solbridge-window.xml >/dev/null 2>&1; cat /sdcard/solbridge-window.xml", "timeout": 45})
    if action == "tap":
        x, y = int(args.get("x", -1)), int(args.get("y", -1))
        if not (0 <= x <= 20000 and 0 <= y <= 20000): raise ToolError("invalid tap coordinates")
        return adb_shell(cfg, {"command": f"input tap {x} {y}", "timeout": 20})
    if action == "swipe":
        vals = [int(args.get(k, -1)) for k in ("x1", "y1", "x2", "y2")]
        if any(v < 0 or v > 20000 for v in vals): raise ToolError("invalid swipe coordinates")
        ms = max(50, min(int(args.get("duration_ms", 300)), 5000))
        return adb_shell(cfg, {"command": f"input swipe {vals[0]} {vals[1]} {vals[2]} {vals[3]} {ms}", "timeout": 20})
    if action == "key":
        key = str(args.get("key", "")).strip().upper()
        if not re.fullmatch(r"(?:KEYCODE_)?[A-Z0-9_]{1,60}|[0-9]{1,4}", key): raise ToolError("invalid key")
        if not key.isdigit() and not key.startswith("KEYCODE_"): key = "KEYCODE_" + key
        return adb_shell(cfg, {"command": f"input keyevent {key}", "timeout": 20})
    if action == "text":
        text = str(args.get("text", ""))
        if not text or len(text) > 4000 or chr(10) in text or chr(13) in text: raise ToolError("text must be 1-4000 chars without newlines")
        enc = base64.b64encode(text.encode()).decode()
        cmd = 'input text "$(echo ' + enc + ' | base64 -d)"'
        return adb_shell(cfg, {"command": cmd, "timeout": 30})
    if action == "launch":
        package = str(args.get("package", "")).strip()
        if not re.fullmatch(r"[A-Za-z0-9_]+(?:[.][A-Za-z0-9_]+)+", package): raise ToolError("invalid package name")
        return adb_shell(cfg, {"command": f"monkey -p {package} -c android.intent.category.LAUNCHER 1", "timeout": 30})
    raise ToolError("action must be state, dump, tap, swipe, key, text, or launch")

def workflow(cfg: Config, args: dict) -> dict:
    steps = list(args.get("steps") or [])
    if not steps or len(steps) > 12:
        raise ToolError("workflow requires 1-12 steps")
    results = []
    forbidden = {"workflow", "self_update", "shell"}
    for i, step in enumerate(steps):
        tool = str(step.get("tool", ""))
        if tool in forbidden:
            raise ToolError(f"workflow step {i}: {tool} is not allowed")
        try:
            value = execute(cfg, tool, dict(step.get("args") or {}))
            results.append({"index": i, "tool": tool, "status": "ok", "result": value})
        except Exception as e:
            results.append({"index": i, "tool": tool, "status": "error", "error": f"{type(e).__name__}: {e}"})
            if not bool(step.get("continue_on_error", False)):
                break
    return {"steps": results}

def self_update(cfg: Config, args: dict) -> dict:
    src = cfg.source_dir.resolve()
    package = src / "solbridge"
    if not (src / ".git").exists() or not (package / "solbridge" / "agent.py").exists():
        raise ToolError("Configured SolBridge source checkout is missing")
    before = _git_head(cfg)
    pull = run(["git", "pull", "--ff-only"], timeout=120, cwd=src)
    if pull["returncode"] != 0:
        raise ToolError(f"git pull failed: {pull['stderr'] or pull['stdout']}")
    after = _git_head(cfg)
    return {"updated": True, "before": before, "after": after, "pull": pull, "_restart_agent": True}

def shell(cfg: Config, args: dict) -> dict:
    if not cfg.allow_shell:
        raise ToolError("Shell tool is disabled in config")
    command = str(args.get("command", "")).strip()
    if not command: raise ToolError("Empty command")
    if not any(command == p.rstrip() or command.startswith(p) for p in cfg.allowed_shell_prefixes):
        raise ToolError("Command prefix is not allowlisted")
    cwd = safe_path(cfg, args.get("path", "."))
    return run(command, shell=True, timeout=cfg.shell_timeout, cwd=cwd)

TOOLS = {
    "health": health,
    "capabilities": capabilities,
    "permission_probe": permission_probe,
    "device_snapshot": device_snapshot,
    "system_inspect": system_inspect,
    "package_info": package_info,
    "list_files": list_files,
    "read_text": read_text,
    "write_text": write_text,
    "state_get": state_get,
    "state_set": state_set,
    "git": git,
    "termux_package": termux_package,
    "python_job": python_job,
    "http_download": http_download,
    "file_info": file_info,
    "android_action": android_action,
    "termux_api": termux_api,
    "adb_shell": adb_shell,
    "android_ui": android_ui,
    "workflow": workflow,
    "self_update": self_update,
    "shell": shell,
}

def execute(cfg: Config, tool: str, args: dict) -> dict:
    if tool not in TOOLS:
        raise ToolError(f"Unknown tool: {tool}")
    return TOOLS[tool](cfg, args)
