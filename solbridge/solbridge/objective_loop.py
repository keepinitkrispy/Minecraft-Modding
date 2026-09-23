"""Pixel objective worker: durable reason -> probe -> observe -> revise loop.

The model may choose only registered tools. PASS is computed from observations,
never accepted from model text. Phone keeps the frozen objective in a JSON file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path.home() / "solbridge-workspace"
STATE = ROOT / "objectives" / "autonomy.json"
MODEL = ROOT / "models" / "qwen3-1.7b-q4_k_m.gguf"
SECRET = ROOT / "agent" / "session_secret"
SITE = "https://keepinitkrispy.github.io/Persistent-Fable/fable-enforce/web/"
PORT = 8765
LOCK = threading.RLock()
STOP = threading.Event()
MAX_CHAT = 120


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(content, encoding="utf-8")
    os.replace(temp, path)


def read_state() -> dict:
    with LOCK:
        data = json.loads(STATE.read_text(encoding="utf-8"))
        if data.get("id") != "external-autonomy-harness" or not data.get("statement") or not data.get("target"):
            raise ValueError("Frozen objective is missing")
        return data


def update_state(fn):
    with LOCK:
        data = read_state()
        fn(data)
        atomic_write(STATE, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        return data


def event(data: dict, kind: str, detail: dict) -> None:
    data.setdefault("events", []).append({"at": time.time(), "kind": kind, "detail": detail})
    data["events"] = data["events"][-300:]


def chat(data: dict, role: str, text: str) -> None:
    data.setdefault("chat", []).append({"role": role, "text": text[:1500], "at": time.time()})
    data["chat"] = data["chat"][-MAX_CHAT:]


def fetch_public(url: str) -> dict:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {
        "keepinitkrispy.github.io", "github.com", "raw.githubusercontent.com",
        "huggingface.co", "developers.cloudflare.com"
    }:
        return {"ok": False, "error": "URL is outside the registered public probe hosts"}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "OutcomeGate-Pixel/1.0"})
        with urllib.request.urlopen(req, timeout=20) as response:
            sample = response.read(1_000_001)
            if len(sample) > 1_000_000:
                sample = sample[:1_000_000]
            content = sample.decode("utf-8", "replace")
            return {"ok": response.status == 200, "status": response.status,
                    "url": response.geturl(), "bytes_sampled": len(sample),
                    "sha256": hashlib.sha256(sample).hexdigest(),
                    "chat_ui": "chatForm" in content or "chat-composer" in content}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:220]}"}


def probe(name: str) -> dict:
    if name == "site":
        return fetch_public(SITE)
    if name == "site_script":
        return fetch_public(SITE + "app.js")
    if name == "repository":
        return fetch_public("https://github.com/keepinitkrispy/Persistent-Fable")
    if name == "model":
        return {"ok": MODEL.exists() and MODEL.stat().st_size == 1282439584,
                "model_bytes": MODEL.stat().st_size if MODEL.exists() else 0,
                "inference_binary": bool(shutil.which("llama-cli"))}
    if name == "phone":
        return {"ok": bool(shutil.which("python") and shutil.which("gh")),
                "available": {tool: bool(shutil.which(tool)) for tool in
                              ("python", "gh", "cloudflared", "llama-cli", "curl", "git")},
                "service": subprocess.run(["sv", "status", "solbridge"], capture_output=True,
                                          text=True, timeout=8).stdout.strip()[:180]}
    if name == "tunnel":
        p = ROOT / "agent" / "tunnel_url"
        url = p.read_text().strip() if p.exists() else ""
        return {"ok": url.startswith("https://"), "url_present": bool(url),
                "reachable": fetch_public_tunnel(url) if url else False}
    raise ValueError(f"Unknown registered probe: {name}")


def fetch_public_tunnel(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(".trycloudflare.com"):
        return False
    try:
        with urllib.request.urlopen(url + "/health", timeout=15) as response:
            return response.status == 200
    except Exception:
        return False


PROBES = ("model", "phone", "site", "site_script", "repository", "tunnel")


def extract_plan(text: str) -> dict:
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if not match:
        raise ValueError("Reasoner did not return a JSON plan")
    data = json.loads(match.group(0))
    routes = data.get("routes")
    if not isinstance(routes, list) or len(routes) < 2:
        raise ValueError("Plan must contain two materially different routes")
    chosen = []
    for route in routes:
        if not isinstance(route, dict) or route.get("probe") not in PROBES:
            continue
        if not all(str(route.get(key, "")).strip() for key in ("domain", "mechanism", "mapping", "test")):
            continue
        if route["probe"] not in {r["probe"] for r in chosen} and route["domain"].lower() not in {r["domain"].lower() for r in chosen}:
            chosen.append({key: str(route[key])[:350] for key in ("domain", "mechanism", "mapping", "test", "probe")})
        if len(chosen) == 2:
            break
    if len(chosen) != 2:
        raise ValueError("Plan must choose two different executable probes and domains")
    return {"reply": str(data.get("reply", ""))[:600],
            "abstraction": str(data.get("abstraction", ""))[:700],
            "blocker_variable": str(data.get("blocker_variable", ""))[:500],
            "routes": chosen}


def reason(data: dict) -> dict:
    if not MODEL.exists():
        raise RuntimeError("Local model has not been downloaded and verified")
    executable = shutil.which("llama-cli")
    if not executable:
        raise RuntimeError("llama-cli is not installed")
    history = data.get("generations", [])[-3:]
    prompt = (
        "You are a grounded objective controller. Preserve the original goal and target. "
        "Treat the current blocker as a variable. Abstract above its surface form, discover "
        "mechanisms from unrelated domains, diverge into two materially different routes, "
        "then return to an executable discriminator. Never call a probe result a completed "
        "real-world objective. Return ONLY compact valid JSON: "
        '{\"reply\":\"Brief natural update\",\"abstraction\":\"...\",\"blocker_variable\":\"...\",\"routes\":['
        '{\"domain\":\"...\",\"mechanism\":\"...\",\"mapping\":\"...\",'
        '\"test\":\"...\",\"probe\":\"site\"},'
        '{\"domain\":\"...\",\"mechanism\":\"...\",\"mapping\":\"...\",'
        '\"test\":\"...\",\"probe\":\"phone\"}]}. '
        "Allowed probes: " + ", ".join(PROBES) + ". "
        "OBJECTIVE: " + str(data["statement"])[:800] + " "
        "TARGET: " + json.dumps(data["target"])[:800] + " "
        "CURRENT BLOCKER: " + str(data.get("blocker", ""))[:500] + " "
        "LATEST USER MESSAGES: " + json.dumps([x["text"] for x in data.get("chat", [])
                                                if x.get("role") == "user"][-2:], ensure_ascii=False)[:500] + " "
        "PAST ATTEMPTS: " + json.dumps(history, ensure_ascii=False)[-1600:]
    )
    cmd = [executable, "-m", str(MODEL), "-p", prompt, "-n", "500",
           "-c", "4096", "--temp", "0.25", "--no-display-prompt", "--simple-io"]
    output = subprocess.run(cmd, capture_output=True, text=True, timeout=500)
    if output.returncode:
        raise RuntimeError(f"reasoner exit {output.returncode}: {output.stderr[-500:]}")
    return extract_plan(output.stdout)


def cycle() -> dict:
    before = read_state()
    if before.get("status") == "PASS":
        return {"status": "PASS"}
    try:
        plan = reason(before)
    except Exception as exc:
        message = f"{type(exc).__name__}: {str(exc)[:350]}"
        update_state(lambda d: (event(d, "reasoner_blocker", {"error": message}),
                                d.update({"blocker": message, "status": "OPEN"})))
        return {"status": "WAIT", "error": message}
    evidence = []
    for route in plan["routes"]:
        try:
            observation = probe(route["probe"])
        except Exception as exc:
            observation = {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:180]}"}
        evidence.append({"route": route, "observation": observation, "at": time.time()})
    def save(d):
        number = len(d.setdefault("generations", [])) + 1
        prior = d.get("blocker", "")
        entry = {"generation": number, "abstraction": plan["abstraction"],
                 "blocker_variable": plan["blocker_variable"], "blocker_before": prior,
                 "tested": evidence}
        d["generations"].append(entry)
        event(d, "divergence_executed", {"generation": number, "probes": [x["route"]["probe"] for x in evidence]})
        d["blocker"] = ("After testing " + ", ".join(x["route"]["probe"] for x in evidence) +
                        ": " + "; ".join(str(x["observation"].get("error") or x["observation"].get("status") or
                                             x["observation"].get("available") or "no target proof")[:180] for x in evidence))
        d["nextAction"] = "Abstract this blocker and test fresh, materially different mechanisms."
        d["status"] = "OPEN"
        reply = plan["reply"] or f"I tested {evidence[0]['route']['domain']} and {evidence[1]['route']['domain']}."
        chat(d, "assistant", f"{reply} I completed cycle {number}. The goal stays open while I revise the blocker from the observed results.")
    update_state(save)
    return {"status": "OPEN", "tested": [x["route"]["probe"] for x in evidence]}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, _format, *_args):
        return

    def authorized(self) -> bool:
        token = SECRET.read_text().strip()
        raw = self.headers.get("Cookie", "")
        c = cookies.SimpleCookie()
        try:
            c.load(raw)
            return c.get("og_session") is not None and secrets.compare_digest(c["og_session"].value, token)
        except Exception:
            return False

    def send(self, code: int, body: bytes, typ="application/json; charset=utf-8", headers=None):
        self.send_response(code)
        self.send_header("Content-Type", typ)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/health":
            self.send(200, b'{"ok":true}')
            return
        token = SECRET.read_text().strip()
        if path.startswith("/invite/") and secrets.compare_digest(path.removeprefix("/invite/"), token):
            self.send(303, b"", headers={"Location": "/",
                     "Set-Cookie": f"og_session={token}; HttpOnly; Secure; SameSite=Strict; Path=/"})
            return
        if not self.authorized():
            self.send(404, b'{"error":"not found"}')
            return
        if path == "/api/state":
            self.send(200, json.dumps(read_state(), ensure_ascii=False).encode("utf-8"))
        elif path == "/":
            self.send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
        elif path == "/app.js":
            self.send(200, CLIENT.encode("utf-8"), "text/javascript; charset=utf-8")
        else:
            self.send(404, b'{"error":"not found"}')

    def do_POST(self):
        if self.path != "/api/message" or not self.authorized():
            self.send(404, b'{"error":"not found"}')
            return
        length = int(self.headers.get("Content-Length", 0))
        if length < 2 or length > 4000:
            self.send(413, b'{"error":"message too large"}')
            return
        try:
            payload = json.loads(self.rfile.read(length))
            text = str(payload.get("message", "")).strip()[:1500]
            if not text:
                raise ValueError("Empty message")
            update_state(lambda d: (chat(d, "user", text), event(d, "user_note", {"text": text})))
            self.send(202, b'{"saved":true}')
        except Exception:
            self.send(400, b'{"error":"invalid message"}')


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Outcome Gate · Pixel</title><style>
:root{font-family:system-ui,-apple-system,sans-serif;color:#172033;background:#f7f9fd}*{box-sizing:border-box}body{margin:0}
main{width:min(740px,100%);min-height:100dvh;margin:auto;background:white;display:flex;flex-direction:column;border-inline:1px solid #e3e9f2}
header{padding:20px;border-bottom:1px solid #e3e9f2}h1{font-size:20px;margin:0}#goal{font-size:14px;line-height:1.5;margin:10px 0 0}
#state{font-size:12px;color:#53637b;margin:8px 0 0}#log{flex:1;min-height:55vh;max-height:70vh;overflow:auto;padding:22px 18px;display:flex;flex-direction:column;gap:15px}
.bubble{max-width:88%;padding:13px 16px;background:#eff3f9;border-radius:17px 17px 17px 5px;white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.48}
.user{align-self:flex-end;background:#e3edff;border-radius:17px 17px 5px 17px}
form{display:flex;gap:8px;border-top:1px solid #e3e9f2;padding:14px}textarea{flex:1;border:1px solid #cbd5e4;border-radius:12px;padding:12px;font:inherit;min-height:54px}
button{border:0;background:#205de1;color:white;border-radius:10px;padding:11px 15px;font-weight:600}footer{color:#69778d;font-size:11px;padding:0 18px 14px}
</style></head><body><main><header><h1>Outcome Gate</h1><p id="goal"></p><p id="state">Checking Pixel worker…</p></header>
<section id="log" role="log" aria-label="Conversation"></section><form id="composer"><textarea id="message" aria-label="Message" placeholder="Talk normally about your original goal…" required></textarea><button>Send</button></form>
<footer>The Pixel continues working from the saved objective. “PASS” requires verified outside change.</footer></main><script src="/app.js"></script></body></html>"""

CLIENT = """const goal=document.querySelector('#goal'),line=document.querySelector('#state'),log=document.querySelector('#log');
let previous='';
async function sync(){try{const response=await fetch('/api/state',{cache:'no-store'});if(!response.ok)throw Error('Pixel unavailable');
const data=await response.json();goal.textContent=data.statement;line.textContent='Objective '+data.status+' · '+(data.generations||[]).length+' tested cycles · blocker: '+data.blocker;
const messages=JSON.stringify(data.chat||[]);if(messages!==previous){log.replaceChildren();for(const item of data.chat||[]){const b=document.createElement('div');b.className='bubble '+(item.role==='user'?'user':'');b.textContent=item.text;log.append(b)}log.scrollTop=log.scrollHeight;previous=messages}
}catch{line.textContent='Reconnecting to the Pixel worker…'}}
document.querySelector('#composer').addEventListener('submit',async e=>{e.preventDefault();const input=document.querySelector('#message');const message=input.value.trim();if(!message)return;
const r=await fetch('/api/message',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message})});if(r.ok){input.value='';await sync()}});
sync();setInterval(sync,5000);"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--serve-only", action="store_true")
    args = parser.parse_args()
    SECRET.parent.mkdir(parents=True, exist_ok=True)
    if not SECRET.exists():
        atomic_write(SECRET, secrets.token_urlsafe(32) + "\n")
        os.chmod(SECRET, 0o600)
    if args.once:
        print(json.dumps(cycle(), ensure_ascii=False))
        return
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    update_state(lambda d: (event(d, "worker_started", {"pid": os.getpid()}),
                            chat(d, "assistant", "I’m working from your original objective. I’ll test distinct routes and report observed changes here.")))
    try:
        while not STOP.is_set():
            if not args.serve_only:
                cycle()
            STOP.wait(180)
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
