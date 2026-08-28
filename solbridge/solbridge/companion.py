from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class CompanionError(RuntimeError):
    pass


def _token() -> str:
    p = Path.home() / ".config" / "solbridge" / "companion.token"
    if not p.exists():
        raise CompanionError("companion token is missing")
    token = p.read_text().strip()
    if not token:
        raise CompanionError("companion token is empty")
    return token


def _get(path: str, timeout: float = 6.0) -> Any:
    req = Request(
        "http://127.0.0.1:8765" + path,
        headers={"X-SolBridge-Token": _token(), "User-Agent": "SolBridge-Agent/companion"},
    )
    try:
        with urlopen(req, timeout=timeout) as r:
            raw = r.read(1_000_000).decode("utf-8", errors="replace")
    except Exception as e:
        raise CompanionError(f"companion request failed: {type(e).__name__}: {e}") from e
    try:
        return json.loads(raw)
    except Exception:
        return {"raw": raw}


def _q(path: str, params: dict[str, Any]) -> Any:
    return _get(path + "?" + urlencode({k: str(v) for k, v in params.items()}))


def _tree_summary(tree: Any) -> dict:
    if not isinstance(tree, list):
        return {"nodes": 0, "sample": [], "raw_type": type(tree).__name__}
    sample = []
    for n in tree:
        if not isinstance(n, dict):
            continue
        text = str(n.get("text") or "")
        desc = str(n.get("desc") or "")
        rid = str(n.get("id") or "")
        if text or desc or rid or bool(n.get("edit")) or bool(n.get("click")):
            sample.append({
                "cls": str(n.get("cls") or "")[-100:],
                "text": text[:180],
                "desc": desc[:180],
                "id": rid[-180:],
                "click": bool(n.get("click")),
                "edit": bool(n.get("edit")),
                "b": str(n.get("b") or "")[:80],
            })
        if len(sample) >= 24:
            break
    return {"nodes": len(tree), "sample": sample}


def _events_tail(events: Any, n: int = 30) -> list:
    return events[-n:] if isinstance(events, list) else []


def _find_chatgpt_package() -> str:
    try:
        r = subprocess.run(["pm", "list", "packages"], capture_output=True, text=True, timeout=20)
        packages = [line.split(":", 1)[1].strip() for line in r.stdout.splitlines() if line.startswith("package:")]
        preferred = [p for p in packages if p == "com.openai.chatgpt"]
        if preferred:
            return preferred[0]
        candidates = [p for p in packages if "openai" in p.lower() or "chatgpt" in p.lower()]
        if candidates:
            return candidates[0]
    except Exception:
        pass
    return "com.openai.chatgpt"


def execute_companion(cfg, args: dict) -> dict:
    action = str(args.get("action", "health")).strip().lower()

    if action == "health":
        return {"health": _get("/health")}
    if action == "events":
        return {"events": _events_tail(_get("/events"), max(1, min(int(args.get("limit", 50)), 200)))}
    if action == "tree":
        tree = _get("/tree")
        if bool(args.get("full", False)):
            return {"tree": tree}
        return {"tree": _tree_summary(tree)}
    if action == "tap":
        x = int(args.get("x", -1)); y = int(args.get("y", -1))
        if not (0 <= x <= 20000 and 0 <= y <= 20000):
            raise CompanionError("invalid tap coordinates")
        return {"tap": _q("/tap", {"x": x, "y": y})}
    if action in {"back", "home"}:
        return {action: _get("/" + action)}
    if action == "text":
        value = str(args.get("value", ""))
        if len(value) > 4000:
            raise CompanionError("text exceeds 4000 characters")
        return {"text": _q("/text", {"value": value})}
    if action == "launch":
        package = str(args.get("package", "")).strip()
        if not re.fullmatch(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+", package):
            raise CompanionError("invalid package name")
        return {"launch": _q("/launch", {"package": package})}
    if action == "prove":
        out: dict[str, Any] = {}
        out["health"] = _get("/health")
        if not isinstance(out["health"], dict) or not out["health"].get("accessibility"):
            out["verified"] = False
            out["failure"] = "accessibility service is not connected"
            return out

        out["before_events"] = _events_tail(_get("/events"), 12)
        out["before_tree"] = _tree_summary(_get("/tree"))

        out["launch_settings"] = _q("/launch", {"package": "com.android.settings"})
        time.sleep(1.4)
        settings_events = _events_tail(_get("/events"), 40)
        out["settings_seen"] = any(isinstance(e, dict) and e.get("pkg") == "com.android.settings" for e in settings_events)
        out["settings_events"] = settings_events[-12:]
        out["settings_tree"] = _tree_summary(_get("/tree"))

        chat_pkg = _find_chatgpt_package()
        out["chatgpt_package"] = chat_pkg
        out["launch_chatgpt"] = _q("/launch", {"package": chat_pkg})
        time.sleep(1.4)
        chat_events = _events_tail(_get("/events"), 50)
        out["chatgpt_seen"] = any(isinstance(e, dict) and e.get("pkg") == chat_pkg for e in chat_events)
        out["chatgpt_events"] = chat_events[-12:]
        out["chatgpt_tree"] = _tree_summary(_get("/tree"))
        out["verified"] = bool(
            isinstance(out.get("launch_settings"), dict) and out["launch_settings"].get("ok")
            and out.get("settings_seen")
            and isinstance(out.get("launch_chatgpt"), dict) and out["launch_chatgpt"].get("ok")
            and out.get("chatgpt_seen")
            and out.get("chatgpt_tree", {}).get("nodes", 0) > 0
        )
        return out

    raise CompanionError("action must be health, events, tree, tap, back, home, text, launch, or prove")
