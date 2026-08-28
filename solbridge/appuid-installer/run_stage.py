from pathlib import Path
import subprocess, os, shutil, json

root = Path.home()/"solbridge-workspace"/"appuid-installer"
root.mkdir(parents=True, exist_ok=True)
repo = "https://raw.githubusercontent.com/keepinitkrispy/Minecraft-Modding/60c9a6b69d3546a4aae66c542baf6df284c585ab/solbridge/appuid-installer/InstallerStage.java"
src = root/"InstallerStage.java"
subprocess.run(["curl","-fsSL",repo,"-o",str(src)],check=True,timeout=60)
android_jar = Path.home()/"solbridge-workspace"/"native-companion"/"android.jar"
am_apk = Path(os.environ.get("PREFIX","/data/data/com.termux/files/usr"))/"libexec/termux-am/am.apk"
classes = root/"classes"
classes.mkdir(exist_ok=True)
cp = f"{android_jar}:{am_apk}"
r = subprocess.run([shutil.which("javac"),"-source","8","-target","8","-cp",cp,"-d",str(classes),str(src)],capture_output=True,text=True,timeout=120)
out={"javac":{"rc":r.returncode,"stdout":r.stdout,"stderr":r.stderr}}
if r.returncode:
    print(json.dumps(out,indent=2)); raise SystemExit(1)
dex = root/"dex"
dex.mkdir(exist_ok=True)
r = subprocess.run([shutil.which("d8"),"--lib",str(android_jar),"--classpath",str(am_apk),"--output",str(dex),str(classes/"com/termux/termuxam/InstallerStage.class")],capture_output=True,text=True,timeout=120)
out["d8"]={"rc":r.returncode,"stdout":r.stdout,"stderr":r.stderr}
if r.returncode:
    print(json.dumps(out,indent=2)); raise SystemExit(1)
classes_dex=dex/"classes.dex"
os.chmod(classes_dex,0o400)
env=os.environ.copy(); env["CLASSPATH"]=f"{am_apk}:{classes_dex}"; env.pop("LD_LIBRARY_PATH",None);env.pop("LD_PRELOAD",None)
r=subprocess.run(["/system/bin/app_process","-Xnoimage-dex2oat","/","com.termux.termuxam.InstallerStage","/sdcard/Download/SolBridgeCompanion.apk"],env=env,capture_output=True,text=True,timeout=90)
out["run"]={"rc":r.returncode,"stdout":r.stdout,"stderr":r.stderr}
print(json.dumps(out,indent=2))
