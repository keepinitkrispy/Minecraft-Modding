from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from solbridge.companion import _get as companion_get

HOME = Path.home()
SOURCE = HOME / ".local/share/solbridge-src/solbridge"
WORK = HOME / "solbridge-workspace"
LOG = WORK / "guardian-install-last.json"
INSTALLER = SOURCE / "install_guardian_live.py"


def is_locked_or_unknown(tree) -> bool:
    if not isinstance(tree, list) or len(tree) < 3:
        return True
    for node in tree:
        if not isinstance(node, dict):
            continue
        rid = str(node.get("id") or "")
        desc = str(node.get("desc") or "")
        if (
            desc == "Lock screen"
            or "keyguard_root_view" in rid
            or "device_entry_icon_view" in rid
            or "keyguard_indication" in rid
        ):
            return True
    return False


def sample(tree, limit=15):
    out = []
    for node in tree if isinstance(tree, list) else []:
        text = str(node.get("text") or "")
        desc = str(node.get("desc") or "")
        rid = str(node.get("id") or "")
        if text not in {"", "null", "None"} or desc not in {"", "null", "None"} or rid:
            out.append({k: node.get(k) for k in ("cls", "text", "desc", "id", "click", "b")})
        if len(out) >= limit:
            break
    return out


def save(data):
    WORK.mkdir(parents=True, exist_ok=True)
    LOG.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def wait_for_stable_unlock(timeout=180):
    deadline = time.time() + timeout
    consecutive = 0
    trail = []
    last = []
    while time.time() < deadline:
        try:
            last = companion_get("/tree")
            locked = is_locked_or_unknown(last)
            trail.append({"locked_or_unknown": locked, "nodes": len(last) if isinstance(last, list) else 0, "sample": sample(last, 5)})
            if locked:
                consecutive = 0
            else:
                consecutive += 1
                if consecutive >= 3:
                    return {"verified": True, "trail": trail[-8:], "sample": sample(last)}
        except Exception as e:
            consecutive = 0
            trail.append({"error": f"{type(e).__name__}: {e}"})
        time.sleep(0.5)
    return {"verified": False, "trail": trail[-12:], "sample": sample(last)}


def main():
    out = {"unlock": wait_for_stable_unlock()}
    if not out["unlock"].get("verified"):
        out["boundary"] = "device did not reach a stable unlocked accessibility state"
        save(out)
        print(json.dumps(out, indent=2))
        raise SystemExit(30)

    p = subprocess.run(
        ["python", str(INSTALLER)],
        capture_output=True,
        text=True,
        timeout=180,
    )
    out["installer"] = {
        "returncode": p.returncode,
        "stdout": p.stdout[-60000:],
        "stderr": p.stderr[-20000:],
    }
    out["verified"] = p.returncode == 0
    save(out)
    print(json.dumps(out, indent=2))
    raise SystemExit(p.returncode)


if __name__ == "__main__":
    main()
