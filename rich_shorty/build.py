#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parent
parts = sorted((root / "src").glob("build.part*"))
if not parts:
    raise SystemExit("No Rich & Shorty builder source parts found.")
source = "".join(p.read_text(encoding="utf-8") for p in parts)
target = root / "build_rich_shorty.py"
target.write_text(source, encoding="utf-8")
namespace = {"__name__": "__main__", "__file__": str(target)}
exec(compile(source, str(target), "exec"), namespace)
