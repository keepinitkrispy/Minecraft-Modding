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
        if len(sample) >= 18:
            break
    return {"nodes": len(tree), "sample": sample}


def _events_tail(events: Any, n: int = 30) -> list:
    return events[-n:] if isinstance(events, list) else []


def _interesting(tree: Any, limit: int = 60) -> list:
    if not isinstance(tree, list):
        return []
    out = []
    for n in tree:
        if not isinstance(n, dict):
            continue
        text = str(n.get("text") or "")
        desc = str(n.get("desc") or "")
        if text not in {"", "null", "None"} or desc not in {"", "null", "None"} or bool(n.get("click")) or bool(n.get("edit")):
            out.append({
                "cls": str(n.get("cls") or "")[-100:],
                "text": text[:220],
                "desc": desc[:220],
                "id": str(n.get("id") or "")[-180:],
                "click": bool(n.get("click")),
                "edit": bool(n.get("edit")),
                "b": str(n.get("b") or "")[:80],
            })
        if len(out) >= limit:
            break
    return out


def _find_chatgpt_package() -> str:
    try:
        r = subprocess.run(["/system/bin/pm", "list", "packages", "--user", "0"], capture_output=True, text=True, timeout=20)
        packages = [line.split(":", 1)[1].strip() for line in r.stdout.splitlines() if line.startswith("package:")]
        if "com.openai.chatgpt" in packages:
            return "com.openai.chatgpt"
        candidates = [p for p in packages if "openai" in p.lower() or "chatgpt" in p.lower()]
        if candidates:
            return candidates[0]
    except Exception:
        pass
    return "com.openai.chatgpt"


def _launcher_component(package: str) -> str | None:
    try:
        p = subprocess.run(["/system/bin/pm", "path", "--user", "0", package], capture_output=True, text=True, timeout=20)
        apk = next((line.split(":", 1)[1].strip() for line in p.stdout.splitlines() if line.startswith("package:")), None)
        if not apk:
            return None
        aapt = "/data/data/com.termux/files/usr/bin/aapt2"
        b = subprocess.run([aapt, "dump", "badging", apk], capture_output=True, text=True, timeout=30)
        m = re.search(r"launchable-activity: name='([^']+)'", b.stdout)
        if not m:
            return None
        activity = m.group(1)
        if activity.startswith("."):
            activity = package + activity
        elif "." not in activity:
            activity = package + "." + activity
        return package + "/" + activity
    except Exception:
        return None


def _launch(package: str) -> dict:
    native = _q("/launch", {"package": package})
    if isinstance(native, dict) and native.get("ok"):
        return {"ok": True, "method": "companion-native"}
    component = _launcher_component(package)
    if not component:
        return {"ok": False, "method": "explicit-component", "error": "launcher component could not be resolved"}
    try:
        am = "/data/data/com.termux/files/usr/bin/am"
        r = subprocess.run([am, "start", "--user", "0", "-n", component], capture_output=True, text=True, timeout=30)
        text = (r.stdout + "\n" + r.stderr)[-3000:]
        ok = r.returncode == 0 and "Error:" not in text
        return {"ok": ok, "method": "explicit-component", "component": component, "returncode": r.returncode, "detail": text}
    except Exception as e:
        return {"ok": False, "method": "explicit-component", "component": component, "error": f"{type(e).__name__}: {e}"}


def _bounds_center(bounds: str) -> tuple[int, int] | None:
    try:
        a = [int(x) for x in bounds.split(",")]
        if len(a) != 4 or a[2] <= a[0] or a[3] <= a[1]:
            return None
        return ((a[0] + a[2]) // 2, (a[1] + a[3]) // 2)
    except Exception:
        return None


def execute_companion(cfg, args: dict) -> dict:
    action = str(args.get("action", "health")).strip().lower()
    if action == "health":
        return {"health": _get("/health")}
    if action == "events":
        return {"events": _events_tail(_get("/events"), max(1, min(int(args.get("limit", 50)), 200)))}
    if action == "tree":
        tree = _get("/tree")
        return {"tree": tree if bool(args.get("full", False)) else _tree_summary(tree)}
    if action == "tap":
        x = int(args.get("x", -1)); y = int(args.get("y", -1))
        if not (0 <= x <= 20000 and 0 <= y <= 20000):
            raise CompanionError("invalid tap coordinates")
        return {"tap": _q("/tap", {"x": x, "y": y})}
    if action == "tap_text":
        needle = str(args.get("text", "")).strip()
        if not needle or len(needle) > 200:
            raise CompanionError("tap_text requires 1-200 characters")
        tree = _get("/tree")
        matches = []
        if isinstance(tree, list):
            for n in tree:
                if not isinstance(n, dict):
                    continue
                hay = (str(n.get("text") or "") + " " + str(n.get("desc") or "")).lower()
                if needle.lower() not in hay:
                    continue
                center = _bounds_center(str(n.get("b") or ""))
                if center:
                    matches.append((0 if n.get("click") else 1, n, center))
        if not matches:
            return {"ok": False, "error": "text target not found", "needle": needle, "interesting": _interesting(tree, 40)}
        matches.sort(key=lambda x: x[0])
        _, node, (x, y) = matches[0]
        result = _q("/tap", {"x": x, "y": y})
        time.sleep(float(args.get("wait", 0.7)))
        return {"ok": bool(isinstance(result, dict) and result.get("ok")), "needle": needle, "x": x, "y": y, "node": node, "tap": result, "after": _interesting(_get("/tree"), 50)}
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
        return {"launch": _launch(package)}
    if action == "capture_launch":
        package = str(args.get("package", "")).strip()
        if not re.fullmatch(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+", package):
            raise CompanionError("invalid package name")
        launched = _launch(package)
        samples = []
        for delay in (0.05, 0.15, 0.35, 0.7, 1.2):
            time.sleep(delay)
            tree = _get("/tree")
            samples.append({"delay": delay, "nodes": len(tree) if isinstance(tree, list) else 0, "interesting": _interesting(tree, 50)})
        events = _events_tail(_get("/events"), 120)
        return {"launch": launched, "samples": samples, "package_events": [e for e in events if isinstance(e, dict) and e.get("pkg") == package][-20:]}
    if action == "prove":
        out: dict[str, Any] = {"health": _get("/health")}
        if not isinstance(out["health"], dict) or not out["health"].get("accessibility"):
            return {**out, "verified": False, "failure": "accessibility service is not connected"}
        out["before_tree"] = _tree_summary(_get("/tree"))
        out["launch_settings"] = _launch("com.android.settings")
        time.sleep(1.2)
        settings_events = _events_tail(_get("/events"), 40)
        out["settings_seen"] = any(isinstance(e, dict) and e.get("pkg") == "com.android.settings" for e in settings_events)
        chat_pkg = _find_chatgpt_package()
        out["chatgpt_package"] = chat_pkg
        out["launch_chatgpt"] = _launch(chat_pkg)
        time.sleep(1.5)
        chat_events = _events_tail(_get("/events"), 50)
        out["chatgpt_seen"] = any(isinstance(e, dict) and e.get("pkg") == chat_pkg for e in chat_events)
        out["chatgpt_events"] = [e for e in chat_events if isinstance(e, dict) and e.get("pkg") == chat_pkg][-8:]
        out["chatgpt_tree"] = _tree_summary(_get("/tree"))
        out["verified"] = bool(out["launch_settings"].get("ok") and out["settings_seen"] and out["launch_chatgpt"].get("ok") and out["chatgpt_seen"] and out["chatgpt_tree"].get("nodes", 0) > 0)
        return out
    raise CompanionError("action must be health, events, tree, tap, tap_text, back, home, text, launch, capture_launch, or prove")
