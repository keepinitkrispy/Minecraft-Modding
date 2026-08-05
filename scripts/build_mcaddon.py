#!/usr/bin/env python3
"""
Build JunkBunch.mcaddon.

Validates the packs, then writes an archive whose ROOT contains exactly:

    JunkBunch_BP/
    JunkBunch_RP/

No repo folders, no `packs/` prefix, no extra nesting, no temp files.

Usage:
    python3 scripts/build_mcaddon.py
"""

import json
import os
import subprocess
import sys
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "packs")
OUT = os.path.join(REPO, "JunkBunch.mcaddon")

PACK_DIRS = ["JunkBunch_BP", "JunkBunch_RP"]
BP_MANIFEST = os.path.join(SRC, "JunkBunch_BP", "manifest.json")
RP_MANIFEST = os.path.join(SRC, "JunkBunch_RP", "manifest.json")


def bump_versions():
    """Increment the patch version of both packs, keeping UUIDs stable.

    Bedrock treats a re-import with the same header UUID and the SAME version as
    'already installed' and keeps the old cached copy - which is exactly how an
    update silently fails to apply. Bumping the version every build (while UUIDs
    stay put, so it's still recognised as the same pack being updated) makes
    updates reliable.
    """
    bp = json.load(open(BP_MANIFEST))
    rp = json.load(open(RP_MANIFEST))

    cur = max(tuple(bp["header"]["version"]), tuple(rp["header"]["version"]))
    new = [cur[0], cur[1], cur[2] + 1]

    for manifest in (bp, rp):
        manifest["header"]["version"] = list(new)
        for mod in manifest["modules"]:
            mod["version"] = list(new)
    # keep the BP -> RP dependency pinned to the RP's new version
    for dep in bp.get("dependencies", []):
        if dep.get("uuid") == rp["header"]["uuid"]:
            dep["version"] = list(new)

    with open(BP_MANIFEST, "w") as fh:
        json.dump(bp, fh, indent=2)
        fh.write("\n")
    with open(RP_MANIFEST, "w") as fh:
        json.dump(rp, fh, indent=2)
        fh.write("\n")
    print(f"Version bumped to {new[0]}.{new[1]}.{new[2]} (UUIDs unchanged)\n")
    return new

EXCLUDE_NAMES = {
    ".gitkeep",
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    "README.md",
}
EXCLUDE_DIRS = {".git", "__pycache__", ".vscode", ".idea"}
EXCLUDE_SUFFIXES = (".pyc", ".mcaddon", ".mcpack", ".zip", ".bak", ".orig", ".tmp")


def should_skip(name):
    if name in EXCLUDE_NAMES:
        return True
    if name.startswith("_"):          # template / scratch files
        return True
    if name.endswith(EXCLUDE_SUFFIXES):
        return True
    return False


def validate():
    print("Validating packs before packaging...")
    result = subprocess.run(
        [sys.executable, os.path.join(REPO, "scripts", "validate_packs.py"), SRC]
    )
    if result.returncode != 0:
        print("\nBuild aborted: validation failed. Fix the errors above and re-run.")
        sys.exit(1)
    print()


def build():
    if os.path.exists(OUT):
        os.remove(OUT)

    written = []
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for pack in PACK_DIRS:
            pack_root = os.path.join(SRC, pack)
            if not os.path.isdir(pack_root):
                print(f"ERROR: missing {pack}/ under {SRC}")
                sys.exit(1)
            for dirpath, dirnames, filenames in os.walk(pack_root):
                dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS)
                for filename in sorted(filenames):
                    if should_skip(filename):
                        continue
                    full = os.path.join(dirpath, filename)
                    # arcname is relative to packs/, so the pack folders land at the
                    # archive root exactly as Minecraft expects.
                    arcname = os.path.relpath(full, SRC)
                    zf.write(full, arcname)
                    written.append(arcname)

    size_kb = os.path.getsize(OUT) / 1024
    print(f"Built {os.path.relpath(OUT, REPO)}  ({size_kb:.1f} KB, {len(written)} files)")
    for name in written:
        print(f"    {name}")

    roots = sorted({n.split("/")[0] for n in written})
    if roots != sorted(PACK_DIRS):
        print(f"\nERROR: archive root is {roots}, expected {sorted(PACK_DIRS)}")
        sys.exit(1)
    print(f"\nArchive root contains exactly: {', '.join(roots)}")


if __name__ == "__main__":
    bump_versions()
    validate()
    build()
