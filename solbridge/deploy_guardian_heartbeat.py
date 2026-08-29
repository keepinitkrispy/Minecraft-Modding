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


def node_text(n):
    return (str(n.get("text") or "") + " " + str(n.get("desc") or "")).strip().lower()


def tap_match(tree, needles, *, contains=False):
    candidates = []
    for n in tree if isinstance(tree, list) else []:
        hay = node_text(n)
        for rank, needle in enumerate(needles):
            needle = needle.lower()
            matched = needle in hay if contains else hay == needle
            if matched:
                candidates.append((rank, 0 if n.get("click") else 1, n))
                break
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], x[1]))
    n = candidates[0][2]
    if d.tap_node(n):
        return {k: n.get(k) for k in ("text", "desc", "id", "b", "click")}
    return None


def launch_and_verify_guardian():
    am = d.shutil.which("am") or str(d.PREFIX / "bin/am")
    launch = d.run([am, "start", "--user", "0", "-n", "dev.solbridge.companion/.MainActivity"], timeout=30)
    deadline = time.time() + 75
    health = None
    forced = None
    permission_actions = []
    errors = []
    settings_opened = False
    last_navigation = 0.0
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
                    "permission_actions": permission_actions,
                    "errors": errors[-5:],
                }

            tree = d.companion_get("/tree")
            # A normal runtime permission prompt is the fastest path when Android offers one.
            tapped = tap_match(tree, ["allow", "while using the app", "ok"])
            if tapped:
                permission_actions.append({"step": "runtime-allow", "node": tapped})
                time.sleep(1)
                continue

            permission_missing = isinstance(health, dict) and "permission not granted" in str(health.get("guardian_error") or "").lower()
            if permission_missing and not settings_opened:
                opened = d.companion_get("/permission_settings")
                permission_actions.append({"step": "open-app-permission-settings", "result": opened})
                settings_opened = True
                last_navigation = time.time()
                time.sleep(1.2)
                continue

            if settings_opened and time.time() - last_navigation > 0.7:
                # Pixel settings can expose the custom permission either directly on the
                # Permissions screen or under Additional permissions. Work from most
                # specific target outward so headings do not trap the navigator.
                custom = tap_match(tree, ["run commands in termux environment"], contains=True)
                if custom:
                    permission_actions.append({"step": "select-run-command-permission", "node": custom})
                    last_navigation = time.time()
                    time.sleep(1)
                    continue
                additional = tap_match(tree, ["additional permissions"], contains=True)
                if additional:
                    permission_actions.append({"step": "open-additional-permissions", "node": additional})
                    last_navigation = time.time()
                    time.sleep(1)
                    continue
                permissions = tap_match(tree, ["permissions"], contains=False)
                if permissions:
                    permission_actions.append({"step": "open-permissions", "node": permissions})
                    last_navigation = time.time()
                    time.sleep(1)
                    continue
        except Exception as e:
            errors.append(f"{type(e).__name__}: {e}")
        time.sleep(1)
    return {
        "verified": False,
        "launch": launch,
        "forced_guardian": forced,
        "health": health,
        "permission_actions": permission_actions,
        "errors": errors[-10:],
        "boundary": "guardian installed but RUN_COMMAND permission/dispatch could not be verified after automated permission recovery",
    }


d.launch_and_verify_guardian = launch_and_verify_guardian

if __name__ == "__main__":
    d.main()
