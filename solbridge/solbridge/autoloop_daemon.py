from __future__ import annotations

import fcntl
import json
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
    with urllib.request.urlopen(req, timeout=8) as r:
        data = json.load(r)
    if not isinstance(data, dict) or not data.get("webSocketDebuggerUrl"):
        raise RuntimeError("CDP did not create a usable page target")
    return data


def _close_target(page: dict) -> None:
    ident = str(page.get("id") or "").strip()
    if not ident:
        return
    for method in ("PUT", "GET"):
        try:
            req = urllib.request.Request(CDP + "/json/close/" + urllib.parse.quote(ident, safe=""), method=method)
            with urllib.request.urlopen(req, timeout=5):
                return
        except Exception:
            pass


def _ws(page: dict):
    endpoint = page.get("webSocketDebuggerUrl")
    if not endpoint:
        raise RuntimeError("CDP page has no websocket endpoint")
    return websocket.create_connection(endpoint, timeout=25, origin="http://localhost")


def _ask_chatgpt_once(prompt: str) -> str:
    ensure_chrome()
    page = _new_target("https://chatgpt.com/")
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

    def ev_ready(js: str, tries: int = 120, delay: float = 0.2):
        last = None
        for _ in range(tries):
            try:
                return ev(js)
            except RuntimeError as exc:
                last = exc
                if "execution context" not in str(exc).lower():
                    raise
                time.sleep(delay)
        raise RuntimeError("ChatGPT execution context unavailable: " + repr(last))

    try:
        call("Runtime.enable")
        call("Page.enable")
        ev_ready("1")

        state = {}
        for _ in range(120):
            state = ev_ready(
                "(()=>({ready:document.readyState,url:location.href,composer:!!document.querySelector('#mobile-composer-prompt'),text:(document.body?.innerText||'').slice(0,1800)}))()",
                tries=5,
                delay=0.1,
            ) or {}
            body = str(state.get("text") or "").lower()
            if "unable to connect" in body or "no internet" in body:
                raise RuntimeError("ChatGPT page reports offline")
            if state.get("ready") in {"interactive", "complete"} and state.get("composer"):
                break
            time.sleep(0.2)
        else:
            raise RuntimeError("ChatGPT composer unavailable: " + repr(state))

        payload = json.dumps(prompt)
        set_state = ev_ready(
            "(()=>{let x=document.querySelector('#mobile-composer-prompt');if(!x)return {ok:false};"
            "let d=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value');"
            "if(d&&d.set)d.set.call(x," + payload + ");else x.value=" + payload + ";"
            "x.dispatchEvent(new Event('input',{bubbles:true}));"
            "x.dispatchEvent(new Event('change',{bubbles:true}));x.focus();"
            "return {ok:true,value:x.value};})()"
        ) or {}
        if not set_state.get("ok") or str(set_state.get("value") or "") != prompt:
            raise RuntimeError("ChatGPT composer text did not bind: " + repr(set_state))

        gate = None
        for _ in range(100):
            gate = ev_ready(
                "(()=>{let b=[...document.querySelectorAll('button')].find(b=>(b.getAttribute('aria-label')||'')==='Send message');"
                "return b?{enabled:!b.disabled&&b.getAttribute('aria-disabled')!=='true'&&!b.hasAttribute('data-visually-disabled'),disabled:!!b.disabled,aria:b.getAttribute('aria-disabled'),visual:b.hasAttribute('data-visually-disabled')}:null})()",
                tries=5,
                delay=0.1,
            )
            if gate and gate.get("enabled"):
                break
            time.sleep(0.1)
        if not gate or not gate.get("enabled"):
            raise RuntimeError("ChatGPT send gate never enabled: " + repr(gate))

        sent = ev_ready(
            "(()=>{let b=[...document.querySelectorAll('button')].find(b=>(b.getAttribute('aria-label')||'')==='Send message');"
            "if(!b||b.disabled||b.getAttribute('aria-disabled')==='true'||b.hasAttribute('data-visually-disabled'))return false;b.click();return true;})()"
        )
        if not sent:
            raise RuntimeError("ChatGPT send click failed")

        last = ""
        stable = 0
        final_state = {}
        for _ in range(180):
            final_state = ev_ready(
                "(()=>{let u=[...document.querySelectorAll('[data-message-role=user]')];let a=[...document.querySelectorAll('[data-message-role=assistant]')];"
                "let q=a[a.length-1],z=u[u.length-1];let body=(document.body?.innerText||'');"
                "return {user:z?(z.innerText||z.textContent||'').trim():'',text:q?(q.querySelector('[data-assistant-markdown]')?.innerText||q.innerText||'').trim():'',"
                "stream:q?q.hasAttribute('data-message-streaming'):false,offline:/unable to connect|no internet/i.test(body)};})()",
                tries=5,
                delay=0.1,
            ) or {}
            if final_state.get("offline"):
                raise RuntimeError("ChatGPT went offline while waiting for response")
            cur_user = str(final_state.get("user") or "").strip()
            cur = str(final_state.get("text") or "").strip()
            if (cur_user == prompt.strip() or cur_user.endswith(prompt.strip())) and cur and not final_state.get("stream"):
                stable = stable + 1 if cur == last else 0
                last = cur
                if stable >= 1:
                    return cur
            else:
                stable = 0
                if cur:
                    last = cur
            time.sleep(0.5)
        raise RuntimeError("assistant response timed out; state=" + repr(final_state))
    finally:
        try:
            ws.close()
        finally:
            _close_target(page)


def ask_chatgpt(prompt: str) -> str:
    errors = []
    for attempt in range(1, 4):
        try:
            return _ask_chatgpt_once(prompt)
        except Exception as exc:
            errors.append(f"attempt {attempt}: {type(exc).__name__}: {exc}")
            log("REASONER_RECOVER " + errors[-1])
            time.sleep(min(8, 2 * attempt))
    raise RuntimeError("ChatGPT reasoning unavailable after recovery attempts: " + " | ".join(errors))


def ui_snapshot() -> dict:
    health = _get("/health")
    events = _get("/events")
    tree = _get("/tree")
    tail = events[-20:] if isinstance(events, list) else []
    latest_pkg = ""
    for event in reversed(tail):
        if isinstance(event, dict) and event.get("pkg"):
            latest_pkg = str(event["pkg"])
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
        match = re.search(r"\{.*\}", response, re.S)
        if not match:
            raise RuntimeError("assistant did not return JSON")
        action = json.loads(match.group(0))
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
                except Exception as exc:
                    retry_or_fail(path, exc)
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
