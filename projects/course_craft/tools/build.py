#!/usr/bin/env python3
"""Validate and package Course Craft.

Steps: regenerate JSON (art untouched) -> static validation -> Script API
type-check + logic tests (if node is available) -> bump patch version ->
write CourseCraft.mcaddon whose root holds exactly CourseCraft_BP/ and CourseCraft_RP/.

Usage: python3 tools/build.py [--no-bump]
"""
import json
import os
import shutil
import subprocess
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec  # noqa: E402
import generate  # noqa: E402
import validate  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "CourseCraft.mcaddon")


def node_checks():
    if not shutil.which("npx") or not os.path.isdir(os.path.join(ROOT, "node_modules", "@minecraft", "server")):
        print("SKIPPED: Script API type-check/tests (run `npm install` in projects/course_craft to enable).")
        return True
    ok = subprocess.run(["npx", "tsc", "-p", "tsconfig.json"], cwd=ROOT).returncode == 0
    ok = subprocess.run(["node", "--import", "./tests/mock/register.mjs", "--test", "tests/course.test.js", "tests/world_sim.test.js"], cwd=ROOT).returncode == 0 and ok
    return ok


def bump():
    paths = [os.path.join(ROOT, "packs", p, "manifest.json") for p in (spec.BP, spec.RP)]
    v = json.load(open(paths[0]))["header"]["version"]
    v = [v[0], v[1], v[2] + 1]
    for p in paths:
        m = json.load(open(p))
        m["header"]["version"] = v
        for mod in m["modules"]:
            mod["version"] = v
        for dep in m.get("dependencies", []):
            if "uuid" in dep:
                dep["version"] = v
        with open(p, "w") as fh:
            json.dump(m, fh, indent=2); fh.write("\n")
    return v


def package():
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for pack in (spec.BP, spec.RP):
            base = os.path.join(ROOT, "packs", pack)
            for dirpath, _d, files in os.walk(base):
                for f in sorted(files):
                    if f.startswith("."):
                        continue
                    full = os.path.join(dirpath, f)
                    zf.write(full, os.path.join(pack, os.path.relpath(full, base)))


def main():
    generate.main()
    if validate.run() != 0:
        print("Build aborted: static validation failed."); return 1
    if not node_checks():
        print("Build aborted: script type-check or logic tests failed."); return 1
    if "--no-bump" not in sys.argv:
        print(f"Version -> {bump()}")
    package()
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
