from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

HOME = Path.home()
SOURCE = HOME / ".local/share/solbridge-src/solbridge"
TEMPLATE = SOURCE / "native-companion-template"
WORK = HOME / "solbridge-workspace/native-companion"
BUILD = WORK / "build"
SHARED_APK = Path("/sdcard/Download/SolBridgeCompanion-guardian.apk")
TOKEN_FILE = HOME / ".config/solbridge/companion.token"
ENSURE = HOME / ".local/bin/solbridge-ensure"
PROPS = HOME / ".termux/termux.properties"
PREFIX = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr"))


def run(cmd, timeout=120, cwd=None, check=False):
    p = subprocess.run([str(x) for x in cmd], cwd=cwd, capture_output=True, text=True, timeout=timeout)
    out = {"cmd": [str(x) for x in cmd], "returncode": p.returncode, "stdout": p.stdout[-8000:], "stderr": p.stderr[-8000:]}
    if check and p.returncode != 0:
        raise RuntimeError(json.dumps(out))
    return out


def write_termux_recovery():
    ENSURE.parent.mkdir(parents=True, exist_ok=True)
    ENSURE.write_text("""#!/data/data/com.termux/files/usr/bin/sh
set -u
export SVDIR="$PREFIX/var/service"
export LOGDIR="$PREFIX/var/log"
PIDFILE="$PREFIX/var/run/service-daemon.pid"
if [ ! -s "$PIDFILE" ] || ! kill -0 "$(cat "$PIDFILE" 2>/dev/null)" 2>/dev/null; then
  service-daemon start >/dev/null 2>&1 || true
fi
for _ in $(seq 1 20); do
  [ -e "$PREFIX/var/service/solbridge/supervise/ok" ] && break
  sleep 0.25
done
rm -f "$PREFIX/var/service/solbridge/down"
sv up solbridge >/dev/null 2>&1 || exit 1
sv status solbridge
""")
    ENSURE.chmod(0o700)
    PROPS.parent.mkdir(parents=True, exist_ok=True)
    text = PROPS.read_text(errors="replace") if PROPS.exists() else ""
    if re.search(r"(?m)^\s*allow-external-apps\s*=.*$", text):
        text = re.sub(r"(?m)^\s*allow-external-apps\s*=.*$", "allow-external-apps=true", text)
    else:
        text = text.rstrip("\n") + "\nallow-external-apps=true\n"
    PROPS.write_text(text)
    reload_result = run(["termux-reload-settings"], timeout=20) if shutil.which("termux-reload-settings") else {"returncode": 127}
    return {"ensure": str(ENSURE), "properties": str(PROPS), "reload": reload_result}


def android_jar():
    p = WORK / "android.jar"
    if p.exists() and p.stat().st_size > 1_000_000:
        return p
    p.parent.mkdir(parents=True, exist_ok=True)
    url = "https://raw.githubusercontent.com/Sable/android-platforms/master/android-35/android.jar"
    req = urllib.request.Request(url, headers={"User-Agent": "SolBridge-Guardian"})
    with urllib.request.urlopen(req, timeout=180) as r:
        p.write_bytes(r.read())
    if p.stat().st_size <= 1_000_000:
        raise RuntimeError("downloaded android.jar is unexpectedly small")
    return p


def build_apk():
    token = TOKEN_FILE.read_text().strip()
    if not token:
        raise RuntimeError("companion token is empty")
    src = WORK / "src/dev/solbridge/companion"
    res = WORK / "res"
    src.mkdir(parents=True, exist_ok=True)
    if res.exists():
        shutil.rmtree(res)
    shutil.copytree(TEMPLATE / "res", res)
    for name in ["MainActivity.java", "BootReceiver.java", "BridgeService.java", "SolAccessibilityService.java"]:
        text = (TEMPLATE / "src/dev/solbridge/companion" / name).read_text()
        if name == "BridgeService.java":
            text = text.replace("__TOKEN__", token)
        (src / name).write_text(text)
    shutil.copy2(TEMPLATE / "AndroidManifest.xml", WORK / "AndroidManifest.xml")

    BUILD.mkdir(parents=True, exist_ok=True)
    for name in ["compiled.zip", "base.apk", "aligned.apk", "SolBridgeCompanion.apk"]:
        (BUILD / name).unlink(missing_ok=True)
    shutil.rmtree(BUILD / "classes", ignore_errors=True)
    shutil.rmtree(BUILD / "dex", ignore_errors=True)
    (BUILD / "classes").mkdir()
    (BUILD / "dex").mkdir()
    jar = android_jar()
    required = ["aapt2", "javac", "d8", "zip", "zipalign", "apksigner", "keytool"]
    missing = [x for x in required if not shutil.which(x)]
    if missing:
        raise RuntimeError("missing build tools: " + ",".join(missing))
    log = []
    def go(cmd, timeout=300):
        r = run(cmd, timeout=timeout, cwd=WORK, check=True)
        log.append(r)
        return r
    go(["aapt2", "compile", "--dir", "res", "-o", BUILD / "compiled.zip"])
    go(["aapt2", "link", "-o", BUILD / "base.apk", "-I", jar, "--manifest", "AndroidManifest.xml", BUILD / "compiled.zip"])
    java = sorted(src.glob("*.java"))
    go(["javac", "-source", "11", "-target", "11", "-cp", jar, "-d", BUILD / "classes", *java])
    classes = sorted((BUILD / "classes").rglob("*.class"))
    go(["d8", "--lib", jar, "--output", BUILD / "dex", *classes])
    go(["zip", "-j", BUILD / "base.apk", BUILD / "dex/classes.dex"])
    go(["zipalign", "-f", "4", BUILD / "base.apk", BUILD / "aligned.apk"])
    ks = WORK / "solbridge.keystore"
    if not ks.exists():
        raise RuntimeError("existing companion signing key is missing; refusing to create an incompatible replacement key")
    apk = BUILD / "SolBridgeCompanion.apk"
    signed = False
    for password in ("changeit", "solbridge"):
        r = run(["apksigner", "sign", "--ks", ks, "--ks-pass", f"pass:{password}", "--key-pass", f"pass:{password}", "--out", apk, BUILD / "aligned.apk"], timeout=120, cwd=WORK)
        log.append(r)
        if r["returncode"] == 0:
            signed = True
            break
    if not signed:
        raise RuntimeError("could not sign guardian APK with existing companion key")
    go(["apksigner", "verify", "--verbose", apk])
    badging = go(["aapt", "dump", "badging", apk])
    shutil.copy2(apk, SHARED_APK)
    return {"apk": str(apk), "shared_apk": str(SHARED_APK), "bytes": apk.stat().st_size, "badging": badging["stdout"][:3000], "log": log}


def companion_get(path, timeout=5):
    token = TOKEN_FILE.read_text().strip()
    req = urllib.request.Request("http://127.0.0.1:8765" + path, headers={"X-SolBridge-Token": token})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def center(bounds):
    try:
        x1, y1, x2, y2 = [int(x) for x in bounds.split(",")]
        return (x1 + x2) // 2, (y1 + y2) // 2
    except Exception:
        return None


def tap_node(node):
    c = center(str(node.get("b") or ""))
    if not c:
        return False
    x, y = c
    companion_get(f"/tap?x={x}&y={y}")
    return True


def installed_has_guardian():
    p = run(["/system/bin/pm", "path", "--user", "0", "dev.solbridge.companion"], timeout=20)
    paths = [line.split(":", 1)[1].strip() for line in p["stdout"].splitlines() if line.startswith("package:")]
    if not paths:
        return {"verified": False, "reason": "package not installed", "pm": p}
    manifest = run(["aapt2", "dump", "xmltree", paths[0], "AndroidManifest.xml"], timeout=60)
    permission = "com.termux.permission.RUN_COMMAND" in manifest["stdout"]
    try:
        import zipfile
        with zipfile.ZipFile(paths[0]) as z:
            dex = z.read("classes.dex")
        guardian_marker = b"solbridge-ensure" in dex and b"com.termux.RUN_COMMAND" in dex
    except Exception:
        guardian_marker = False
    return {"verified": bool(permission and guardian_marker), "permission": permission, "guardian_marker": guardian_marker, "pm": p}


def install_with_accessibility():
    before = installed_has_guardian()
    launch = run(["termux-open", "--view", str(SHARED_APK)], timeout=30)
    trail = []
    deadline = time.time() + 45
    preferred = ["update", "install", "continue", "allow"]
    while time.time() < deadline:
        now = installed_has_guardian()
        if now["verified"]:
            return {"installed": True, "before": before, "after": now, "launch": launch, "trail": trail}
        try:
            tree = companion_get("/tree")
        except Exception as e:
            trail.append({"tree_error": f"{type(e).__name__}: {e}"})
            time.sleep(1)
            continue
        candidates = []
        for n in tree if isinstance(tree, list) else []:
            hay = (str(n.get("text") or "") + " " + str(n.get("desc") or "")).strip().lower()
            for rank, word in enumerate(preferred):
                if hay == word or hay.startswith(word + " "):
                    candidates.append((rank, n))
                    break
        if candidates:
            candidates.sort(key=lambda x: x[0])
            n = candidates[0][1]
            trail.append({"tap": {k: n.get(k) for k in ("text", "desc", "id", "b")}})
            try:
                tap_node(n)
            except Exception as e:
                trail.append({"tap_error": f"{type(e).__name__}: {e}"})
        time.sleep(1)
    return {"installed": False, "before": before, "after": installed_has_guardian(), "launch": launch, "trail": trail[-20:]}


def launch_and_verify_guardian():
    am = shutil.which("am") or str(PREFIX / "bin/am")
    launch = run([am, "start", "--user", "0", "-n", "dev.solbridge.companion/.MainActivity"], timeout=30)
    deadline = time.time() + 25
    health = None
    permission_taps = []
    while time.time() < deadline:
        try:
            health = companion_get("/health")
            if health.get("guardian_dispatch") is True and not health.get("guardian_error"):
                return {"verified": True, "launch": launch, "health": health, "permission_taps": permission_taps}
            tree = companion_get("/tree")
            for n in tree if isinstance(tree, list) else []:
                hay = (str(n.get("text") or "") + " " + str(n.get("desc") or "")).strip().lower()
                if hay in {"allow", "while using the app", "ok"}:
                    if tap_node(n):
                        permission_taps.append({k: n.get(k) for k in ("text", "desc", "id", "b")})
                        break
        except Exception:
            pass
        time.sleep(1)
    return {"verified": False, "launch": launch, "health": health, "permission_taps": permission_taps, "boundary": "guardian installed but RUN_COMMAND dispatch was not verified"}


def main():
    out = {"recovery": write_termux_recovery()}
    out["build"] = build_apk()
    out["install"] = install_with_accessibility()
    if not out["install"].get("installed"):
        out["verified"] = False
        out["boundary"] = "Android package update could not be verified automatically"
        print(json.dumps(out, indent=2))
        raise SystemExit(2)
    out["guardian"] = launch_and_verify_guardian()
    out["verified"] = bool(out["guardian"].get("verified"))
    if not out["verified"]:
        out["boundary"] = out["guardian"].get("boundary")
    print(json.dumps(out, indent=2))
    raise SystemExit(0 if out["verified"] else 3)


if __name__ == "__main__":
    main()
