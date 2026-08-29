from __future__ import annotations

import importlib.util
import time
from pathlib import Path

BASE = Path.home() / ".local/share/solbridge-src/solbridge/deploy_guardian.py"
spec = importlib.util.spec_from_file_location("solbridge_deploy_guardian_base", BASE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load guardian deployer: {BASE}")
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


def launch_and_verify_guardian():
    am = d.shutil.which("am") or str(d.PREFIX / "bin/am")
    launch = d.run([am, "start", "--user", "0", "-n", "dev.solbridge.companion/.MainActivity"], timeout=30)
    deadline = time.time() + 35
    health = None
    forced = None
    permission_taps = []
    errors = []
    while time.time() < deadline:
        try:
            forced = d.companion_get("/guardian")
            health = d.companion_get("/health")
            if isinstance(forced, dict) and forced.get("ok") is True and health.get("guardian_dispatch") is True and not health.get("guardian_error"):
                return {
                    "verified": True,
                    "launch": launch,
                    "forced_guardian": forced,
                    "health": health,
                    "permission_taps": permission_taps,
                    "errors": errors[-5:],
                }
            tree = d.companion_get("/tree")
            for n in tree if isinstance(tree, list) else []:
                hay = (str(n.get("text") or "") + " " + str(n.get("desc") or "")).strip().lower()
                if hay in {"allow", "while using the app", "ok"}:
                    if d.tap_node(n):
                        permission_taps.append({k: n.get(k) for k in ("text", "desc", "id", "b")})
                        break
        except Exception as e:
            errors.append(f"{type(e).__name__}: {e}")
        time.sleep(1)
    return {
        "verified": False,
        "launch": launch,
        "forced_guardian": forced,
        "health": health,
        "permission_taps": permission_taps,
        "errors": errors[-10:],
        "boundary": "guardian installed but explicit RUN_COMMAND recovery dispatch was not verified",
    }


d.launch_and_verify_guardian = launch_and_verify_guardian

if __name__ == "__main__":
    d.main()
