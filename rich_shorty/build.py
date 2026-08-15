#!/usr/bin/env python3
from pathlib import Path
import sys
import types

root = Path(__file__).resolve().parent
parts = sorted((root / "src").glob("build.part*"))
if not parts:
    raise SystemExit("No Rich & Shorty builder source parts found.")
source = "".join(p.read_text(encoding="utf-8") for p in parts)
target = root / "build_rich_shorty.py"
target.write_text(source, encoding="utf-8")

# Load the complete builder as a real module first. Registering it in
# sys.modules is required by dataclasses/type introspection on Python 3.12.
module_name = "rich_shorty_builder"
module = types.ModuleType(module_name)
module.__file__ = str(target)
sys.modules[module_name] = module
exec(compile(source, str(target), "exec"), module.__dict__)

# Invoke only after every source part (including late polish layers) exists.
addon = module.make_pack()
report = module.validate(addon)
print(module.json.dumps(report, indent=2))
if report["errors"]:
    raise SystemExit(1)
