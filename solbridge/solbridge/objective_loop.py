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
from generic_agent import cycle_inplace as generic_cycle_inplace, submit_message

ROOT = Path.home() / "solbridge-workspace"
STATE = ROOT / "objectives" / "autonomy.json"
MODEL = ROOT / "models" / "qwen3-1.7b-q4_k_m.gguf"
SECRET = ROOT / "agent" / "session_secret"
SITE = "https://keepinitkrispy.github.io/Persistent-Fable/fable-enforce/web/"
PORT = 8877
LOCK = threading.RLock()
STOP = threading.Event()
WAKE = threading.Event()
MAX_CHAT = 120


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(content, encoding="utf-8")
    os.replace(temp, path)


def read_state() -> dict:
    with LOCK:
        data = json.loads(STATE.read_text(encoding="utf-8"))
        if not data.get("statement") or not data.get("target"):
            raise ValueError("Frozen objective is missing")
        return data


def start_objective(statement: str) -> dict:
    statement = statement.strip()
    if not statement or len(statement) > 1500:
        raise ValueError("Objective must be 1..1500 characters")
    with LOCK:
        previous = read_state()
        archive = STATE.parent / "archive"
        archive.mkdir(parents=True, exist_ok=True)
        atomic_write(archive / (str(int(time.time()*1000)) + "-" + secrets.token_hex(4) + ".json"),
                     json.dumps(previous, ensure_ascii=False, indent=2) + "\n")
        data = {
            "id": "objective-" + secrets.token_hex(8), "statement": statement,
            "target": {"description": statement, "verification": "semantic evidence review"},
            "mode": "single_objective",
            "status": "OPEN", "blocker": "Objective accepted; no action has been attempted yet.",
            "nextAction": "Reason, act, observe, verify, and continue automatically.",
            "chat": [], "events": [], "procedure_registry": {}, "abstraction_stack": [],
            "generic": {"cycle": 0, "evidence": [], "attempts": [], "fail_streak": 0}
        }
        chat(data, "user", statement)
        event(data, "objective_created", {"previous_id": previous["id"]})
        atomic_write(STATE, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        WAKE.set()
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
        env = dict(os.environ, SVDIR=os.environ.get("PREFIX", "/data/data/com.termux/files/usr") + "/var/service")
        return {"ok": bool(shutil.which("python") and shutil.which("gh")),
                "available": {tool: bool(shutil.which(tool)) for tool in
                              ("python", "gh", "cloudflared", "llama-cli", "curl", "git")},
                "service": subprocess.run(["sv", "status", "solbridge"], capture_output=True,
                                          text=True, timeout=8, env=env).stdout.strip()[:180]}
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


def assess_result(data: dict, tunnel_reachable: bool) -> None:
    """Evaluate this frozen harness target from external observations."""
    if data.get("id") != "external-autonomy-harness":
        return
    visits = data.get("device_visits", {})
    generations = data.get("generations", [])
    tests = [item for gen in generations for item in gen.get("tested", [])]
    distinct_routes = any(len({item["route"]["domain"].lower() for item in gen.get("tested", [])}) >= 2
                          for gen in generations)
    model_ready = MODEL.exists() and MODEL.stat().st_size == 1282439584
    evidence = {
        "free_local_model_present": model_ready,
        "reasoned_and_tested_distinct_routes": distinct_routes,
        "pixel_https_app_reachable": tunnel_reachable,
        "pixel_browser_opened_app": bool(visits.get("Android")),
        "mac_browser_opened_app": bool(visits.get("Macintosh")),
        "external_observations_recorded": len(tests) >= 2,
        "worker_recovered_after_process_death": data.get("restart_verified") is True,
    }
    data["target_evidence"] = evidence
    data["status"] = "PASS" if all(evidence.values()) else "OPEN"
    if data["status"] == "PASS" and not data.get("passAt"):
        data["passAt"] = time.time()
        event(data, "target_changed_and_verified", evidence)
        chat(data, "assistant", "The Pixel and Mac both opened this HTTPS app, and the Pixel completed two distinct, observed routes. The original objective now has verified outside changes.")


def method_registry(data: dict) -> dict:
    reg = data.setdefault("procedure_registry", {})
    for name in PROBES:
        reg.setdefault(name, {
            "name": name, "steps": [name], "origin": "primitive",
            "validated": True, "successes": 0, "failures": 0
        })
    return reg


def ensure_active_frame(data: dict) -> dict:
    stack = data.setdefault("abstraction_stack", [])
    if not stack:
        stack.append({
            "kind": "objective_blocker",
            "depth": 0,
            "blocker": str(data.get("blocker") or "The original objective remains unmet."),
            "attempted": [],
            "created_at": time.time()
        })
    return stack[-1]


def execute_method(method: dict) -> dict:
    rows = []
    for name in method.get("steps", []):
        if name not in PROBES:
            rows.append({"probe": name, "observation": {"ok": False, "error": "unknown primitive"}})
            continue
        try:
            observation = probe(name)
        except Exception as exc:
            observation = {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:180]}"}
        rows.append({"probe": name, "observation": observation})
    return {
        "ok": bool(rows) and all(bool(row["observation"].get("ok")) for row in rows),
        "observations": rows,
        "at": time.time()
    }


def choose_known_method(data: dict, frame: dict) -> dict | None:
    registry = method_registry(data)
    attempted = set(map(str, frame.setdefault("attempted", [])))
    preferred = frame.get("preferred_method")
    if preferred and preferred in registry and preferred not in attempted:
        return registry[preferred]
    choices = [m for name, m in registry.items()
               if name not in attempted and m.get("validated") is True]
    if not choices:
        return None
    choices.sort(key=lambda m: (
        -int(m.get("successes", 0)),
        int(m.get("failures", 0)),
        len(m.get("steps", [])),
        str(m.get("name", ""))
    ))
    return choices[0]


def _extract_json(text: str) -> dict:
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if not match:
        raise ValueError("reasoner returned no JSON object")
    return json.loads(match.group(0))


def ontological_invention(data: dict, frame: dict) -> dict:
    """Turn a blocker into a relational ontology and derive a new executable method."""
    registry = method_registry(data)
    existing = [{"name": m["name"], "steps": m.get("steps", [])} for m in registry.values()]
    if not MODEL.exists() or not shutil.which("llama-cli"):
        raise RuntimeError("local ontology reasoner unavailable")
    prompt = (
        "Perform ONTOLOGICAL abstraction, not analogy. Rewrite the blocker as entities, "
        "relations, constraints, controllable variables, invariants, failure condition, and "
        "required state transition. Find a foreign ontology with the same relational weak "
        "point. Map its native mechanism back into ONE new executable procedure made only "
        "from the registered primitives. Return ONLY JSON: "
        "{\"ontology\":{\"entities\":\"\",\"relations\":\"\",\"constraints\":\"\","
        "\"controls\":\"\",\"invariants\":\"\",\"failure\":\"\",\"transition\":\"\"},"
        "\"foreign\":{\"domain\":\"\",\"mechanism\":\"\",\"mapping\":\"\",\"weak_point\":\"\"},"
        "\"procedure\":{\"name\":\"\",\"steps\":[\"primitive\",\"primitive\"]},\"reply\":\"\"}. "
        "Procedure steps length 2..4 and must not duplicate an existing ordered sequence. "
        "PRIMITIVES=" + json.dumps(list(PROBES)) + " "
        "EXISTING=" + json.dumps(existing, separators=(",", ":"))[-900:] + " "
        "ORIGINAL_OBJECTIVE=" + str(data.get("statement", ""))[:220] + " "
        "ACTIVE_BLOCKER=" + str(frame.get("blocker", ""))[:360] + " "
        "DEPTH=" + str(frame.get("depth", 0)) + " /no_think"
    )
    cmd = [shutil.which("llama-cli"), "-m", str(MODEL), "-p", prompt, "-n", "180",
           "-c", "1536", "--temp", "0.35", "--no-display-prompt", "--simple-io", "--single-turn"]
    out = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=90)
    if out.returncode:
        raise RuntimeError(f"ontology reasoner exit {out.returncode}: {out.stderr[-240:]}")
    obj = _extract_json(out.stdout)
    ontology = obj.get("ontology") if isinstance(obj.get("ontology"), dict) else {}
    ontology_keys = ("entities","relations","constraints","controls","invariants","failure","transition")
    if not all(str(ontology.get(k, "")).strip() for k in ontology_keys):
        raise ValueError("incomplete ontology")
    foreign = obj.get("foreign") if isinstance(obj.get("foreign"), dict) else {}
    foreign_keys = ("domain","mechanism","mapping","weak_point")
    if not all(str(foreign.get(k, "")).strip() for k in foreign_keys):
        raise ValueError("incomplete foreign ontology mapping")
    proc = obj.get("procedure") if isinstance(obj.get("procedure"), dict) else {}
    steps = proc.get("steps")
    if not isinstance(steps, list) or not (2 <= len(steps) <= 4) or any(s not in PROBES for s in steps):
        raise ValueError("invalid engineered procedure")
    if any(tuple(m.get("steps", [])) == tuple(steps) for m in registry.values()):
        raise ValueError("duplicate engineered procedure")
    name = re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(proc.get("name", "engineered"))).strip("-")[:72] or "engineered"
    base, n = name, 2
    while name in registry:
        name = f"{base}-{n}"
        n += 1
    return {
        "ontology": {k: str(ontology[k])[:360] for k in ontology_keys},
        "foreign": {k: str(foreign[k])[:360] for k in foreign_keys},
        "procedure": {"name": name, "steps": list(steps)},
        "reply": str(obj.get("reply", ""))[:420]
    }


def fallback_invention(data: dict, frame: dict) -> dict:
    """Untested methodology fallback so a failed reasoner cannot stop continuation."""
    registry = method_registry(data)
    seen = {tuple(m.get("steps", [])) for m in registry.values()}
    for length in (2, 3):
        if length == 2:
            candidates = ((a, b) for a in PROBES for b in PROBES if a != b)
        else:
            candidates = ((a, b, c) for a in PROBES for b in PROBES for c in PROBES
                          if len({a, b, c}) >= 2)
        for steps in candidates:
            if tuple(steps) in seen:
                continue
            name = "compose-" + "-".join(steps)
            return {
                "ontology": {
                    "entities": "available capabilities and the blocked state",
                    "relations": "capabilities expose or alter relations relevant to the blocked state",
                    "constraints": "all previously known methods at this level were exhausted",
                    "controls": "composition, ordering, and reuse of available capabilities",
                    "invariants": "the original objective and acceptance conditions remain fixed",
                    "failure": str(frame.get("blocker", ""))[:360],
                    "transition": "create a capability whose combined operation makes the blocker irrelevant"
                },
                "foreign": {
                    "domain": "compositional systems engineering",
                    "mechanism": "compose primitives into a derived operation with behavior absent from either primitive alone",
                    "mapping": "the ordered primitive sequence becomes a newly registered executable method",
                    "weak_point": "the blocker may depend on interaction between capabilities rather than one primitive"
                },
                "procedure": {"name": name, "steps": list(steps)},
                "reply": "I used an untested derived method because the ontology reasoner did not return a usable construction."
            }
    raise RuntimeError("derived-method search space exhausted")


def invent_capability(data: dict, frame: dict) -> dict:
    try:
        return ontological_invention(data, frame)
    except Exception as exc:
        event(data, "ontology_reasoner_fallback", {"error": f"{type(exc).__name__}: {str(exc)[:220]}"})
        return fallback_invention(data, frame)


def root_blocker(data: dict) -> str:
    evidence = data.get("target_evidence")
    if isinstance(evidence, dict):
        missing = [k for k, v in evidence.items() if v is not True]
        if missing:
            return "Original objective still unmet; missing verified conditions: " + ", ".join(missing)
    return str(data.get("blocker") or "Original objective remains unmet.")


def blocker_irrelevant(data: dict, frame: dict, result: dict) -> bool:
    if frame.get("kind") == "capability_validation":
        return bool(result.get("ok"))
    # The root blocker becomes irrelevant only when the external acceptance gate passes.
    tunnel = probe("tunnel")
    assess_result(data, bool(tunnel.get("reachable")))
    return data.get("status") == "PASS"


def collapse_resolved_frames(data: dict) -> None:
    stack = data.setdefault("abstraction_stack", [])
    while len(stack) > 1 and stack[-1].get("resolved") is True:
        solved = stack.pop()
        event(data, "abstraction_collapsed", {
            "depth": solved.get("depth"), "resolved_blocker": solved.get("blocker"),
            "return_to": stack[-1].get("blocker")
        })


def cycle() -> dict:
    def mutate(data: dict) -> dict:
        if data.get("status") == "PASS":
            return {"status": "PASS"}

        if data.get("id") != "external-autonomy-harness":
            return generic_cycle_inplace(data)
        registry = method_registry(data)
        collapse_resolved_frames(data)
        frame = ensure_active_frame(data)
        method = choose_known_method(data, frame)

        if method is None:
            invention = invent_capability(data, frame)
            proc = invention["procedure"]
            registry[proc["name"]] = {
                "name": proc["name"], "steps": proc["steps"], "origin": "ontological_abstraction",
                "validated": False, "successes": 0, "failures": 0,
                "ontology": invention["ontology"], "foreign": invention["foreign"],
                "created_at": time.time()
            }
            child = {
                "kind": "capability_validation",
                "depth": int(frame.get("depth", 0)) + 1,
                "blocker": "Validate engineered capability " + proc["name"] +
                           " so it can be used against parent blocker: " + str(frame.get("blocker", ""))[:260],
                "parent_blocker": frame.get("blocker"),
                "preferred_method": proc["name"],
                "attempted": [],
                "ontology": invention["ontology"],
                "foreign": invention["foreign"],
                "created_at": time.time()
            }
            data.setdefault("abstraction_stack", []).append(child)
            event(data, "ontological_abstraction", {
                "depth": child["depth"], "parent_blocker": frame.get("blocker"),
                "weak_point": invention["foreign"]["weak_point"],
                "engineered_method": proc
            })
            chat(data, "assistant", invention["reply"] or
                 f"I exhausted known methods for this blocker, abstracted it ontologically, and engineered {proc['name']}.")
            data["blocker"] = child["blocker"]
            data["nextAction"] = "Validate the engineered capability; if it fails, continue upward rather than stopping."
            return {"status": "OPEN", "transition": "abstracted", "depth": child["depth"]}

        name = method["name"]
        frame.setdefault("attempted", []).append(name)
        result = execute_method(method)
        if result["ok"]:
            method["successes"] = int(method.get("successes", 0)) + 1
        else:
            method["failures"] = int(method.get("failures", 0)) + 1
        event(data, "method_executed", {
            "depth": frame.get("depth"), "blocker": frame.get("blocker"),
            "method": name, "result": result
        })

        if blocker_irrelevant(data, frame, result):
            if frame.get("kind") == "capability_validation":
                method["validated"] = True
                frame["resolved"] = True
                event(data, "blocker_became_irrelevant", {
                    "depth": frame.get("depth"), "blocker": frame.get("blocker"), "method": name
                })
                collapse_resolved_frames(data)
                parent = ensure_active_frame(data)
                data["blocker"] = parent.get("blocker")
                data["nextAction"] = "Return downward and attack the parent blocker with the newly validated capability."
                return {"status": "OPEN", "transition": "descended", "method": name}
            return {"status": data.get("status", "PASS"), "transition": "objective_verified"}

        # Failure never halts. Keep this blocker active. If known methods remain,
        # next cycle uses them; if none remain, the next cycle abstracts upward.
        if frame.get("kind") == "objective_blocker":
            frame["blocker"] = root_blocker(data)
        data["blocker"] = frame.get("blocker")
        data["nextAction"] = (
            "Continue on this blocker. Try another known validated method; "
            "when those are exhausted, abstract ontologically and engineer an untested capability."
        )
        data["status"] = "OPEN"
        return {"status": "OPEN", "transition": "continue", "method": name, "method_ok": result["ok"]}

    result_box = {}
    def apply(data):
        result_box.update(mutate(data))
    update_state(apply)
    return result_box



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
            user_agent = self.headers.get("User-Agent", "")
            platform = "Android" if "Android" in user_agent else "Macintosh" if "Macintosh" in user_agent else ""
            if platform:
                update_state(lambda d: (d.setdefault("device_visits", {}).update({platform: time.time()}),
                                        event(d, "browser_opened_app", {"platform": platform})))
                tunnel_path = ROOT / "agent" / "tunnel_url"
                url = tunnel_path.read_text().strip() if tunnel_path.exists() else ""
                reachable = fetch_public_tunnel(url) if url else False
                update_state(lambda d: assess_result(d, reachable))
            self.send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
        elif path == "/app.js":
            self.send(200, CLIENT.encode("utf-8"), "text/javascript; charset=utf-8")
        else:
            self.send(404, b'{"error":"not found"}')

    def do_POST(self):
        if self.path not in ("/api/message", "/api/objectives") or not self.authorized():
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
            if self.path == "/api/objectives":
                data = start_objective(text)
                self.send(201, json.dumps({"created": True, "id": data["id"]}).encode("utf-8"))
                return
            update_state(lambda d: submit_message(d, text))
            WAKE.set()
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
<section id="log" role="log" aria-label="Conversation"></section><form id="composer"><textarea id="message" aria-label="Message" placeholder="Message SolBridge…" required></textarea><button>Send</button></form>
<footer>Your task persists. SolBridge keeps working until the observed result verifies it or you change it.</footer></main><script src="/app.js"></script></body></html>"""

CLIENT = """const goal=document.querySelector('#goal'),line=document.querySelector('#state'),log=document.querySelector('#log');
let previous='';
async function sync(){try{const response=await fetch('/api/state',{cache:'no-store'});if(!response.ok)throw Error('Pixel unavailable');
const data=await response.json();goal.textContent=(data.active_task||data.last_completed_task||'Ready');const cycles=(data.generic&&data.generic.cycle)||0;line.textContent=(data.status==='IDLE'?'Ready':('Working · cycle '+cycles+(data.blocker?' · '+data.blocker:'')));
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
    update_state(lambda d: event(d, "worker_started", {"pid": os.getpid()}))
    try:
        while not STOP.is_set():
            if not args.serve_only:
                cycle()
            WAKE.wait(45)
            WAKE.clear()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
