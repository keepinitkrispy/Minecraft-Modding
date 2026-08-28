from __future__ import annotations
import shutil, subprocess, sys, time
from pathlib import Path
from typing import Any
from .config import Config

class ToolError(RuntimeError): pass

def run(cmd: list[str] | str, *, timeout=30, shell=False, cwd=None):
    p = subprocess.run(cmd, shell=shell, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return {"returncode": p.returncode, "stdout": p.stdout[-20000:], "stderr": p.stderr[-20000:]}

def safe_path(cfg: Config, user_path: str) -> Path:
    cfg.workspace.mkdir(parents=True, exist_ok=True)
    base = cfg.workspace.resolve()
    p = (base / user_path).resolve() if not Path(user_path).is_absolute() else Path(user_path).resolve()
    if p != base and base not in p.parents:
        raise ToolError("Path escapes configured workspace")
    return p

def health(cfg: Config, args: dict) -> dict:
    return {
        "ok": True,
        "device_id": cfg.device_id,
        "workspace": str(cfg.workspace),
        "source_dir": str(cfg.source_dir),
        "allow_shell": cfg.allow_shell,
        "time": int(time.time()),
        "python": shutil.which("python") or shutil.which("python3"),
        "termux_api": bool(shutil.which("termux-battery-status")),
        "rish": bool(shutil.which("rish")),
    }

def device_snapshot(cfg: Config, args: dict) -> dict:
    out: dict[str, Any] = {
        "device_id": cfg.device_id,
        "uname": run(["uname", "-a"]),
        "disk": run(["df", "-h", str(cfg.workspace)]),
    }
    if shutil.which("termux-battery-status"):
        out["battery"] = run(["termux-battery-status"])
    if shutil.which("termux-wifi-connectioninfo"):
        out["wifi"] = run(["termux-wifi-connectioninfo"])
    if shutil.which("getprop"):
        out["android_release"] = run(["getprop", "ro.build.version.release"])
        out["device"] = run(["getprop", "ro.product.model"])
    return out

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

def termux_api(cfg: Config, args: dict) -> dict:
    name = args.get("name")
    allowed = {
        "battery": ["termux-battery-status"],
        "wifi": ["termux-wifi-connectioninfo"],
        "location": ["termux-location", "-p", str(args.get("provider", "network")), "-r", "once"],
        "clipboard_get": ["termux-clipboard-get"],
        "volume": ["termux-volume"],
    }
    if name not in allowed: raise ToolError(f"Unsupported Termux API op: {name}")
    if not shutil.which(allowed[name][0]): raise ToolError(f"{allowed[name][0]} is unavailable")
    return run(allowed[name], timeout=45)

def self_update(cfg: Config, args: dict) -> dict:
    src = cfg.source_dir.resolve()
    package = src / "solbridge"
    if not (src / ".git").exists() or not (package / "pyproject.toml").exists():
        raise ToolError("Configured SolBridge source checkout is missing")
    pull = run(["git", "pull", "--ff-only"], timeout=120, cwd=src)
    if pull["returncode"] != 0:
        raise ToolError(f"git pull failed: {pull['stderr'] or pull['stdout']}")
    install = run([sys.executable, "-m", "pip", "install", "-q", "."], timeout=180, cwd=package)
    if install["returncode"] != 0:
        raise ToolError(f"pip install failed: {install['stderr'] or install['stdout']}")
    return {"updated": True, "pull": pull, "install": install, "_restart_agent": True}

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
    "device_snapshot": device_snapshot,
    "list_files": list_files,
    "read_text": read_text,
    "write_text": write_text,
    "git": git,
    "termux_api": termux_api,
    "self_update": self_update,
    "shell": shell,
}

def execute(cfg: Config, tool: str, args: dict) -> dict:
    if tool not in TOOLS:
        raise ToolError(f"Unknown tool: {tool}")
    return TOOLS[tool](cfg, args)
