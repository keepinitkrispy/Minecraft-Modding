from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

import websocket

from .companion import _get, _launch, _tree_summary

ROOT = Path.home() / "solbridge-workspace"
BASE = ROOT / "autoloop"
INBOX = BASE / "inbox"
DONE = BASE / "done"
FAILED = BASE / "failed"
PROOFS = BASE / "proofs"
PIDFILE = BASE / "autoloop.pid"
LOG = BASE / "autoloop.log"
PROFILE = ROOT / "chatgpt-browser" / "profile"
STOP = False

for p in (BASE, INBOX, DONE, FAILED, PROOFS, PROFILE):
    p.mkdir(parents=True, exist_ok=True)


def log(msg: str) -> None:
    with LOG.open("a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%dT%H:%M:%S%z") + " " + msg.replace("\n", " ") + "\n")


def stop(*_):
    global STOP
    STOP = True


def chrome_targets():
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=2) as r:
            return json.load(r)
    except Exception:
        return None


def ensure_chrome():
    targets = chrome_targets()
    if targets:
        return targets
    exe = shutil.which("chromium-browser") or shutil.which("chromium")
    if not exe:
        raise RuntimeError("native Chromium is missing")
    log_file = (ROOT / "chatgpt-browser" / "autoloop-chromium.log").open("ab", buffering=0)
    cmd = [
        exe,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--no-first-run",
        "--no-default-browser-check",
        "--remote-debugging-address=127.0.0.1",
        "--remote-debugging-port=9222",
        "--remote-allow-origins=*",
        "--disable-blink-features=AutomationControlled",
        "--user-data-dir=" + str(PROFILE),
        "--user-agent=Mozilla/5.0 (Linux; Android 17; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Mobile Safari/537.36",
        "https://chatgpt.com/",
    ]
    subprocess.Popen(cmd, stdout=log_file, stderr=log_file, start_new_session=True)
    for _ in range(60):
        time.sleep(0.5)
        targets = chrome_targets()
        if targets:
            return targets
    raise RuntimeError("Chromium did not expose CDP")


def ask_chatgpt(prompt: str) -> str:
    targets = ensure_chrome()
    pages = [x for x in targets if x.get("type") == "page" and "chatgpt.com" in x.get("url", "")]
    if not pages:
        raise RuntimeError("ChatGPT page not found")
    page = pages[0]
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=25, origin="http://localhost")
    seq = 0

    def call(method: str, params=None):
        nonlocal seq
        seq += 1
        ident = seq
        ws.send(json.dumps({"id": ident, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == ident:
                return msg

    def ev(js: str):
        r = call("Runtime.evaluate", {"expression": js, "returnByValue": True})
        return r.get("result", {}).get("result", {}).get("value")

    try:
        before = ev("document.querySelectorAll('[data-message-role=assistant]').length") or 0
        focused = ev("(()=>{let x=document.querySelector('#mobile-composer-prompt')||document.querySelector('textarea');if(!x)return false;x.focus();return true;})()")
        if not focused:
            raise RuntimeError("ChatGPT composer unavailable")
        call("Input.insertText", {"text": prompt})
        time.sleep(0.25)
        sent = ev("(()=>{let b=[...document.querySelectorAll('button')].find(b=>/send message/i.test(b.getAttribute('aria-label')||''));if(!b||b.disabled)return false;b.click();return true;})()")
        if not sent:
            raise RuntimeError("ChatGPT send button unavailable")
        last = ""
        stable = 0
        for _ in range(150):
            d = ev("(()=>{let t=[...document.querySelectorAll('[data-message-role=assistant]')];let q=t[t.length-1];return {n:t.length,text:q?(q.querySelector('[data-assistant-markdown]')?.innerText||q.innerText.replace(/^ChatGPT said:/,'')).trim():'',busy:[...document.querySelectorAll('button')].some(b=>/stop/i.test((b.getAttribute('aria-label')||'')+' '+(b.innerText||'')))};})()") or {}
            cur = (d.get("text") or "").strip()
            if d.get("n", 0) > before and cur:
                stable = stable + 1 if cur == last and not d.get("busy") else 0
                last = cur
                if stable >= 2:
                    return cur
            time.sleep(1)
        raise RuntimeError("assistant response timed out; last=" + repr(last))
    finally:
        ws.close()


def ui_snapshot() -> dict:
    health = _get("/health")
    events = _get("/events")
    tree = _get("/tree")
    tail = events[-20:] if isinstance(events, list) else []
    latest_pkg = ""
    for e in reversed(tail):
        if isinstance(e, dict) and e.get("pkg"):
            latest_pkg = str(e["pkg"])
            break
    return {
        "health": health,
        "latest_event_package": latest_pkg,
        "events": tail[-8:],
        "tree": _tree_summary(tree),
    }


def parse_action(response: str) -> dict:
    try:
        action = json.loads(response)
    except Exception:
        m = re.search(r"\{.*\}", response, re.S)
        if not m:
            raise RuntimeError("assistant did not return JSON")
        action = json.loads(m.group(0))
    name = str(action.get("action", ""))
    if name == "launch":
        package = str(action.get("package", ""))
        if not re.fullmatch(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+", package):
            raise RuntimeError("invalid launch package")
        return {"action": "launch", "package": package}
    if name in {"home", "back"}:
        return {"action": name}
    raise RuntimeError("assistant chose unsupported action: " + name)


def execute_action(action: dict) -> dict:
    before = _get("/events")
    if action["action"] == "launch":
        result = _launch(action["package"])
    else:
        result = _get("/" + action["action"])
    time.sleep(1.5)
    after = _get("/events")
    tree = _tree_summary(_get("/tree"))
    tail = after[-50:] if isinstance(after, list) else []
    if action["action"] == "launch":
        verified = bool(result.get("ok")) and any(isinstance(e, dict) and e.get("pkg") == action["package"] for e in tail)
    else:
        verified = bool(isinstance(result, dict) and result.get("ok")) and after != before
    return {"result": result, "verified": verified, "events_tail": tail[-12:], "tree": tree}


def process_mission(path: Path) -> None:
    mission = json.loads(path.read_text())
    mid = str(mission.get("id") or path.stem)
    goal = str(mission.get("goal") or "").strip()
    if not goal:
        raise RuntimeError("mission has no goal")
    before = ui_snapshot()
    prompt = (
        "You are the reasoning controller for the user's own Android Pixel. "
        "A local observer supplied the UI state below. Choose exactly one safe UI action that best advances the goal. "
        "Allowed JSON forms are: {\"action\":\"launch\",\"package\":\"PACKAGE\"}, {\"action\":\"home\"}, or {\"action\":\"back\"}. "
        "Return ONLY one minified JSON object, no markdown or explanation.\n"
        "GOAL: " + goal + "\n"
        "UI_STATE: " + json.dumps(before, ensure_ascii=False)[:12000]
    )
    started = time.time()
    response = ask_chatgpt(prompt)
    action = parse_action(response)
    execution = execute_action(action)
    if not execution.get("verified"):
        raise RuntimeError("chosen UI action did not verify")
    proof = {
        "id": mid,
        "mission_created_at": mission.get("created_at"),
        "processed_at": time.time(),
        "elapsed": time.time() - started,
        "attempts": int(mission.get("attempts", 0)) + 1,
        "trigger": "local_inbox_watcher",
        "goal": goal,
        "before": before,
        "assistant_response": response,
        "action": action,
        "execution": execution,
        "verified": True,
    }
    (PROOFS / f"{mid}.json").write_text(json.dumps(proof, indent=2, ensure_ascii=False))
    path.rename(DONE / path.name)
    log("DONE " + mid + " action=" + json.dumps(action) + " verified=True attempts=" + str(proof["attempts"]))


def retry_or_fail(path: Path, exc: Exception) -> None:
    try:
        mission = json.loads(path.read_text())
    except Exception:
        mission = {"id": path.stem, "goal": ""}
    attempts = int(mission.get("attempts", 0)) + 1
    mission["attempts"] = attempts
    mission["last_error"] = f"{type(exc).__name__}: {exc}"
    mission["last_failed_at"] = time.time()
    if attempts >= 60:
        (FAILED / path.name).write_text(json.dumps({"error": mission["last_error"], "mission": mission}, indent=2))
        path.unlink(missing_ok=True)
        log("GIVEUP " + path.name + " attempts=" + str(attempts) + " " + mission["last_error"])
        return
    delay = min(300, 5 * (2 ** min(attempts - 1, 6)))
    mission["not_before"] = time.time() + delay
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(mission, indent=2))
    tmp.replace(path)
    log("RETRY " + path.name + " attempts=" + str(attempts) + " delay=" + str(delay) + " " + mission["last_error"])


def main() -> None:
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    PIDFILE.write_text(str(os.getpid()))
    log("START pid=" + str(os.getpid()))
    try:
        while not STOP:
            now = time.time()
            for path in sorted(INBOX.glob("*.json")):
                if STOP:
                    break
                try:
                    mission = json.loads(path.read_text())
                    if float(mission.get("not_before", 0) or 0) > now:
                        continue
                    process_mission(path)
                except Exception as e:
                    retry_or_fail(path, e)
            for _ in range(10):
                if STOP:
                    break
                time.sleep(0.1)
    finally:
        try:
            if PIDFILE.exists() and PIDFILE.read_text().strip() == str(os.getpid()):
                PIDFILE.unlink()
        except Exception:
            pass
        log("STOP pid=" + str(os.getpid()))


if __name__ == "__main__":
    main()
