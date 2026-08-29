from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from solbridge.companion import _get as companion_get, _q as companion_query

HOME = Path.home()
SOURCE = HOME / ".local/share/solbridge-src/solbridge"
WORK = HOME / "solbridge-workspace"
ANDROID_JAR = WORK / "native-companion/android.jar"
AM_APK = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr")) / "libexec/termux-am/am.apk"
STAGE_APK = Path("/sdcard/Download/SolBridgeCompanion.apk")


def run(cmd, *, timeout=120, cwd=None, env=None, check=True):
    p = subprocess.run(
        [str(x) for x in cmd],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    result = {
        "cmd": [str(x) for x in cmd],
        "returncode": p.returncode,
        "stdout": p.stdout[-12000:],
        "stderr": p.stderr[-12000:],
    }
    if check and p.returncode != 0:
        raise RuntimeError(json.dumps(result))
    return result


def load_deployer():
    path = SOURCE / "deploy_guardian.py"
    spec = importlib.util.spec_from_file_location("solbridge_guardian_deployer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compile_commit_probe() -> Path:
    root = WORK / "guardian-live-install/commit-probe"
    classes = root / "classes"
    dex = root / "dex"
    shutil.rmtree(root, ignore_errors=True)
    classes.mkdir(parents=True)
    dex.mkdir(parents=True)
    source = SOURCE / "appuid-installer/CommitStatusProbe.java"
    javac = shutil.which("javac")
    d8 = shutil.which("d8")
    if not javac or not d8 or not ANDROID_JAR.exists() or not AM_APK.exists():
        raise RuntimeError("PackageInstaller probe toolchain is incomplete")
    run([javac, "-source", "8", "-target", "8", "-cp", ANDROID_JAR, "-d", classes, source], timeout=120)
    class_file = classes / "com/termux/termuxam/CommitStatusProbe.class"
    run([d8, "--lib", ANDROID_JAR, "--output", dex, class_file], timeout=120)
    classes_dex = dex / "classes.dex"
    classes_dex.chmod(0o400)
    return classes_dex


def stage_apk() -> tuple[int, dict]:
    stage_script = SOURCE / "appuid-installer/run_stage.py"
    result = run(["python", stage_script], timeout=300)
    match = re.search(r"STAGED_SESSION=(\d+)", result["stdout"])
    if not match:
        raise RuntimeError("PackageInstaller staging produced no session id: " + result["stdout"][-3000:])
    return int(match.group(1)), result


def commit_session(session_id: int, classes_dex: Path) -> tuple[int, dict]:
    env = os.environ.copy()
    env["CLASSPATH"] = f"{AM_APK}:/system/framework/services.jar:{classes_dex}"
    env.pop("LD_LIBRARY_PATH", None)
    env.pop("LD_PRELOAD", None)
    result = run(
        ["/system/bin/app_process", "-Xnoimage-dex2oat", "/", "com.termux.termuxam.CommitStatusProbe", str(session_id)],
        timeout=120,
        env=env,
    )
    match = re.search(r"^STATUS=(-?\d+)\s*$", result["stdout"], re.MULTILINE)
    if not match:
        raise RuntimeError("PackageInstaller commit produced no status: " + result["stdout"][-3000:])
    return int(match.group(1)), result


def launch_confirmation(session_id: int) -> dict:
    am = shutil.which("am")
    if not am:
        raise RuntimeError("Termux am client is unavailable")
    return run(
        [
            am,
            "start",
            "-W",
            "--user",
            "0",
            "-a",
            "android.content.pm.action.CONFIRM_INSTALL",
            "-p",
            "com.google.android.packageinstaller",
            "--ei",
            "android.content.pm.extra.SESSION_ID",
            str(session_id),
        ],
        timeout=40,
    )


def center(bounds: str):
    try:
        x1, y1, x2, y2 = [int(x) for x in bounds.split(",")]
        if x2 <= x1 or y2 <= y1:
            return None
        return (x1 + x2) // 2, (y1 + y2) // 2
    except Exception:
        return None


def tree_sample(tree, limit=30):
    out = []
    for node in tree if isinstance(tree, list) else []:
        text = str(node.get("text") or "")
        desc = str(node.get("desc") or "")
        if text not in {"", "null", "None"} or desc not in {"", "null", "None"} or node.get("click"):
            out.append({k: node.get(k) for k in ("cls", "text", "desc", "id", "click", "b")})
        if len(out) >= limit:
            break
    return out


def tap_best(tree, wanted):
    wanted = [x.lower() for x in wanted]
    candidates = []
    for node in tree if isinstance(tree, list) else []:
        text = str(node.get("text") or "").strip()
        desc = str(node.get("desc") or "").strip()
        hay = (text + " " + desc).strip().lower()
        if not hay:
            continue
        point = center(str(node.get("b") or ""))
        if not point:
            continue
        for rank, target in enumerate(wanted):
            exact = hay == target
            contains = target in hay
            if exact or contains:
                # Prefer clickable exact buttons, then clickable contains, then bounded text.
                score = (0 if node.get("click") else 2) + (0 if exact else 1)
                candidates.append((rank, score, node, point))
                break
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], x[1]))
    _, _, node, (x, y) = candidates[0]
    result = companion_query("/tap", {"x": x, "y": y})
    return {
        "target": {k: node.get(k) for k in ("text", "desc", "id", "click", "b")},
        "x": x,
        "y": y,
        "result": result,
    }


def drive_install(deployer, timeout=45):
    deadline = time.time() + timeout
    trail = []
    last_tree = []
    while time.time() < deadline:
        installed = deployer.installed_has_guardian()
        if installed.get("verified"):
            return {"verified": True, "installed": installed, "trail": trail, "last_tree": tree_sample(last_tree)}
        try:
            tree = companion_get("/tree")
            last_tree = tree
            tap = tap_best(tree, ["update", "install", "install anyway", "allow", "continue", "ok"])
            trail.append({"tree": tree_sample(tree, 12), "tap": tap})
            if tap:
                time.sleep(1.2)
            else:
                time.sleep(0.7)
        except Exception as e:
            trail.append({"companion_error": f"{type(e).__name__}: {e}"})
            time.sleep(0.7)
    return {
        "verified": False,
        "installed": deployer.installed_has_guardian(),
        "trail": trail[-12:],
        "last_tree": tree_sample(last_tree),
    }


def launch_new_companion(timeout=25):
    am = shutil.which("am")
    if not am:
        raise RuntimeError("Termux am client is unavailable")
    launch = run([am, "start", "-W", "--user", "0", "-n", "dev.solbridge.companion/.MainActivity"], timeout=30, check=False)
    deadline = time.time() + timeout
    last = None
    errors = []
    while time.time() < deadline:
        try:
            last = companion_get("/health")
            if isinstance(last, dict) and "heartbeat_age_ms" in last:
                return {"verified": True, "launch": launch, "health": last, "errors": errors[-5:]}
        except Exception as e:
            errors.append(f"{type(e).__name__}: {e}")
        time.sleep(0.5)
    return {"verified": False, "launch": launch, "health": last, "errors": errors[-10:]}


def grant_run_command(timeout=45):
    trail = []
    try:
        first = companion_get("/guardian")
        if isinstance(first, dict) and first.get("ok") is True:
            return {"verified": True, "already_granted": True, "guardian": first, "trail": trail}
    except Exception as e:
        trail.append({"initial_guardian_error": f"{type(e).__name__}: {e}"})

    companion_get("/permission_settings")
    time.sleep(0.8)
    deadline = time.time() + timeout
    last_tree = []
    while time.time() < deadline:
        try:
            guardian = companion_get("/guardian")
            if isinstance(guardian, dict) and guardian.get("ok") is True:
                health = companion_get("/health")
                return {"verified": True, "already_granted": False, "guardian": guardian, "health": health, "trail": trail}
        except Exception as e:
            trail.append({"guardian_error": f"{type(e).__name__}: {e}"})

        try:
            tree = companion_get("/tree")
            last_tree = tree
            tap = tap_best(
                tree,
                [
                    "permissions",
                    "additional permissions",
                    "run commands in termux environment",
                    "allow",
                    "while using the app",
                    "ok",
                ],
            )
            trail.append({"tree": tree_sample(tree, 15), "tap": tap})
            time.sleep(0.9 if tap else 0.5)
        except Exception as e:
            trail.append({"tree_error": f"{type(e).__name__}: {e}"})
            time.sleep(0.5)

    return {"verified": False, "trail": trail[-15:], "last_tree": tree_sample(last_tree)}


def main():
    deployer = load_deployer()
    out = {"source_head": run(["git", "rev-parse", "HEAD"], cwd=HOME / ".local/share/solbridge-src")["stdout"].strip()}
    out["recovery"] = deployer.write_termux_recovery()
    out["build"] = deployer.build_apk()
    shutil.copy2(deployer.SHARED_APK, STAGE_APK)
    out["stage_apk"] = {"path": str(STAGE_APK), "bytes": STAGE_APK.stat().st_size}

    session_id, stage = stage_apk()
    out["session_id"] = session_id
    out["stage"] = stage
    classes_dex = compile_commit_probe()
    status, commit = commit_session(session_id, classes_dex)
    out["commit_status"] = status
    out["commit"] = commit

    if status == -1:
        out["confirmation"] = launch_confirmation(session_id)
    elif status != 0:
        raise RuntimeError(f"PackageInstaller commit failed with status {status}")

    out["install"] = drive_install(deployer)
    if not out["install"].get("verified"):
        print(json.dumps(out, indent=2))
        raise SystemExit(20)

    out["companion"] = launch_new_companion()
    if not out["companion"].get("verified"):
        print(json.dumps(out, indent=2))
        raise SystemExit(21)

    out["permission"] = grant_run_command()
    if not out["permission"].get("verified"):
        print(json.dumps(out, indent=2))
        raise SystemExit(22)

    health = companion_get("/health")
    out["final_health"] = health
    out["verified"] = bool(
        out["install"].get("verified")
        and out["companion"].get("verified")
        and out["permission"].get("verified")
        and isinstance(health, dict)
        and health.get("guardian_dispatch") is True
        and not health.get("guardian_error")
    )
    print(json.dumps(out, indent=2))
    raise SystemExit(0 if out["verified"] else 23)


if __name__ == "__main__":
    main()
