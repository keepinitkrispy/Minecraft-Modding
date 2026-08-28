from __future__ import annotations

import json
import fcntl
import os
import re
import shutil
import signal
import subprocess
import time
import urllib.parse
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
LOCKFILE = BASE / "autoloop.lock"
PROFILE = ROOT / "chatgpt-browser" / "profile"
CDP = "http://127.0.0.1:9222"
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
        with urllib.request.urlopen(CDP + "/json/list", timeout=2) as r:
            data = json.load(r)
            return data if isinstance(data, list) else []
    except Exception:
        return None


def _start_chromium() -> None:
    exe = shutil.which("chromium-browser") or shutil.which("chromium")
    if not exe:
        raise RuntimeError("native Chromium is missing")
    log_path = ROOT / "chatgpt-browser" / "autoloop-chromium.log"
    log_file = log_path.open("ab", buffering=0)
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


def ensure_chrome():
    targets = chrome_targets()
    if targets is not None:
        return targets
    _start_chromium()
    for _ in range(80):
        time.sleep(0.5)
        targets = chrome_targets()
        if targets is not None:
            return targets
    raise RuntimeError("Chromium did not expose CDP")


def _new_target(url: str):
    encoded = urllib.parse.quote(url, safe=":/?=&")
    req = urllib.request.Request(CDP + "/json/new?" + encoded, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.load(r)
            return data if isinstance(data, dict) else None
    except Exception as e:
        log("CDP new-target failed " + type(e).__name__ + ": " + str(e))
        return None


def _ws(page: dict):
    endpoint = page.get("webSocketDebuggerUrl")
    if not endpoint:
        raise RuntimeError("CDP page has no websocket endpoint")
    return websocket.create_connection(endpoint, timeout=25, origin="http://localhost")


def _navigate_page(page: dict, url: str) -> None:
    ws = _ws(page)
    try:
        ws.send(json.dumps({"id": 1, "method": "Page.enable", "params": {}}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == 1:
                break
        ws.send(json.dumps({"id": 2, "method": "Page.navigate", "params": {"url": url}}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == 2:
                break
    finally:
        ws.close()


def ensure_chatgpt_page() -> dict:
    targets = ensure_chrome() or []
    pages = [x for x in targets if x.get("type") == "page"]
    chat = [x for x in pages if "chatgpt.com" in str(x.get("url", ""))]
    if chat:
        return chat[0]

    made = _new_target("https://chatgpt.com/")
    if made and made.get("webSocketDebuggerUrl"):
        return made

    if pages:
        try:
            _navigate_page(pages[0], "https://chatgpt.com/")
        except Exception as e:
            log("CDP navigate-existing failed " + type(e).__name__ + ": " + str(e))
        for _ in range(30):
            time.sleep(0.5)
            targets = chrome_targets() or []
            chat = [x for x in targets if x.get("type") == "page" and "chatgpt.com" in str(x.get("url", ""))]
            if chat:
                return chat[0]

    # CDP may be alive with only dead/non-page targets. A new browser process using
    # the same profile/port will either create a page in the existing browser or fail
    # harmlessly because the port is owned. Try it, then re-enumerate.
    _start_chromium()
    for _ in range(60):
        time.sleep(0.5)
        targets = chrome_targets() or []
        chat = [x for x in targets if x.get("type") == "page" and "chatgpt.com" in str(x.get("url", ""))]
        if chat:
            return chat[0]
        pages = [x for x in targets if x.get("type") == "page"]
        if pages:
            try:
                _navigate_page(pages[0], "https://chatgpt.com/")
            except Exception:
                pass
    raise RuntimeError("unable to create or recover ChatGPT CDP page")


def _ask_chatgpt_once(prompt: str) -> str:
    page = ensure_chatgpt_page()
    ws = _ws(page)
    seq = 0

    def call(method: str, params=None):
        nonlocal seq
        seq += 1
        ident = seq
        ws.send(json.dumps({"id": ident, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == ident:
                if msg.get("error"):
                    raise RuntimeError("CDP " + method + " failed: " + json.dumps(msg["error"]))
                return msg

    def ev(js: str):
        r = call("Runtime.evaluate", {"expression": js, "returnByValue": True, "awaitPromise": True})
        return r.get("result", {}).get("result", {}).get("value")

    try:
        call("Page.enable")
        call("Page.navigate", {"url": "https://chatgpt.com/"})

        ready = False
        last_state = {}
        for _ in range(120):
            time.sleep(0.5)
            last_state = ev(
                "(()=>({ready:document.readyState,url:location.href,"
                "composer:!!(document.querySelector('#mobile-composer-prompt')||document.querySelector('textarea')||document.querySelector('[contenteditable=\"true\"]')),"
                "text:(document.body?.innerText||'').slice(0,1200)}))()"
            ) or {}
            body = str(last_state.get("text") or "").lower()
            if "unable to connect" in body or "no internet" in body:
                raise RuntimeError("ChatGPT page reports offline")
            if last_state.get("ready") in {"interactive", "complete"} and last_state.get("composer"):
                ready = True
                break
        if not ready:
            raise RuntimeError("ChatGPT composer unavailable after navigation; state=" + repr(last_state))

        before = ev("document.querySelectorAll('[data-message-role=assistant]').length") or 0
        focused = ev(
            "(()=>{let x=document.querySelector('#mobile-composer-prompt')||document.querySelector('textarea')||document.querySelector('[contenteditable=\"true\"]');"
            "if(!x)return false;x.focus();return true;})()"
        )
        if not focused:
            raise RuntimeError("ChatGPT composer unavailable")

        call("Input.insertText", {"text": prompt})
        time.sleep(0.4)
        sent = ev(
            "(()=>{let b=[...document.querySelectorAll('button')].find(b=>/send( message)?/i.test((b.getAttribute('aria-label')||'')+' '+(b.getAttribute('data-testid')||'')));"
            "if(!b||b.disabled)return false;b.click();return true;})()"
        )
        if not sent:
            # ChatGPT's DOM changes regularly. With the composer focused, Enter is a
            # stable semantic fallback and avoids binding the daemon to one button label.
            call("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13})
            call("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13})

        last = ""
        stable = 0
        for _ in range(180):
            d = ev(
                "(()=>{let t=[...document.querySelectorAll('[data-message-role=assistant]')];let q=t[t.length-1];"
                "let body=(document.body?.innerText||'');return {n:t.length,text:q?(q.querySelector('[data-assistant-markdown]')?.innerText||q.innerText.replace(/^ChatGPT said:/,'')).trim():'',"
                "busy:[...document.querySelectorAll('button')].some(b=>/stop/i.test((b.getAttribute('aria-label')||'')+' '+(b.innerText||''))),"
                "offline:/unable to connect|no internet/i.test(body)};})()"
            ) or {}
            if d.get("offline"):
                raise RuntimeError("ChatGPT went offline while waiting for response")
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


def ask_chatgpt(prompt: str) -> str:
    errors = []
    for attempt in range(1, 4):
        try:
            return _ask_chatgpt_once(prompt)
        except Exception as e:
            errors.append(f"attempt {attempt}: {type(e).__name__}: {e}")
            log("REASONER_RECOVER " + errors[-1])
            # Force a fresh target on the next pass. A stale/offline SPA can otherwise
            # survive a network outage indefinitely even after the network returns.
            _new_target("https://chatgpt.com/")
            time.sleep(min(8, 2 * attempt))
    raise RuntimeError("ChatGPT reasoning unavailable after recovery attempts: " + " | ".join(errors))


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
    (FAILED / path.name).unlink(missing_ok=True)
    path.rename(DONE / path.name)
    log("DONE " + mid + " action=" + json.dumps(action) + " verified=True attempts=" + str(proof["attempts"]))


def retry_or_fail(path: Path, exc: Exception) -> None:
    try:
        mission = json.loads(path.read_text())
        if not isinstance(mission, dict):
            raise ValueError("mission is not an object")
    except Exception:
        mission = {"id": path.stem, "goal": ""}
    attempts = int(mission.get("attempts", 0)) + 1
    mission["attempts"] = attempts
    mission["last_error"] = f"{type(exc).__name__}: {exc}"
    mission["last_failed_at"] = time.time()
    if attempts >= 60 or not str(mission.get("goal") or "").strip():
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
    lock_handle = LOCKFILE.open("a+")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log("DUPLICATE_EXIT pid=" + str(os.getpid()))
        lock_handle.close()
        return
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
