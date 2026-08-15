#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parent
parts = sorted((root / "src").glob("build.part*"))
if not parts:
    raise SystemExit("No Rich & Shorty builder source parts found.")
source = "".join(p.read_text(encoding="utf-8") for p in parts)
target = root / "build_rich_shorty.py"
target.write_text(source, encoding="utf-8")

# Load the complete builder as a module first. This deliberately prevents the
# legacy __main__ block inside the concatenated source from firing before later
# polish/override parts have been defined.
namespace = {"__name__": "rich_shorty_builder", "__file__": str(target)}
exec(compile(source, str(target), "exec"), namespace)
addon = namespace["make_pack"]()
report = namespace["validate"](addon)
print(namespace["json"].dumps(report, indent=2))
if report["errors"]:
    raise SystemExit(1)
