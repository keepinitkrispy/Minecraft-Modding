#!/usr/bin/env python3
"""Import your own textures into Course Craft.

1. Put PNGs into  projects/course_craft/textures_in/  (or pass a .zip / folder path).
   Name each file after its slot, e.g. cc_goal_top.png  (see TEXTURES.md).
2. Run:  python3 tools/import_textures.py [folder_or_zip]
3. Run:  python3 tools/build.py   -> CourseCraft.mcaddon

Rules: PNG, square, 16/32/64/128 px. Unknown file names are reported and skipped.
Only the slots you provide are replaced; every other slot keeps its current art.
Exit code 0 = all supplied files imported, 1 = something was rejected.
"""
import io
import os
import sys
import zipfile

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "packs", spec.RP)
DEFAULT_IN = os.path.join(ROOT, "textures_in")


def dest(slot):
    sub = "items" if slot in spec.ITEM_SLOTS else "blocks"
    return os.path.join(RP, "textures", sub, f"{slot}.png")


def iter_sources(src):
    """Yield (basename, bytes) from a folder or zip, ignoring OS junk files."""
    if os.path.isfile(src) and src.lower().endswith(".zip"):
        with zipfile.ZipFile(src) as zf:
            for info in zf.infolist():
                name = os.path.basename(info.filename)
                if info.is_dir() or not name or name.startswith(".") or "__MACOSX" in info.filename:
                    continue
                yield name, zf.read(info)
    elif os.path.isdir(src):
        for dirpath, _d, files in os.walk(src):
            for name in sorted(files):
                if name.startswith("."):
                    continue
                with open(os.path.join(dirpath, name), "rb") as fh:
                    yield name, fh.read()
    else:
        raise FileNotFoundError(src)


def check_image(data):
    """Return (Image, None) or (None, reason)."""
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception as exc:  # noqa: BLE001 - any decode failure is a rejection
        return None, f"not a readable image ({exc.__class__.__name__})"
    if im.format != "PNG":
        return None, f"must be PNG, got {im.format}"
    w, h = im.size
    if w != h:
        return None, f"must be square, got {w}x{h}"
    if w not in spec.ALLOWED_SIZES:
        return None, f"size {w}x{h} not allowed (use {sorted(spec.ALLOWED_SIZES)})"
    return im.convert("RGBA"), None


def run(src):
    slots = set(spec.all_slots())
    imported, rejected, unknown = [], [], []
    for name, data in iter_sources(src):
        stem, ext = os.path.splitext(name)
        slot = stem.lower()
        if ext.lower() != ".png" or slot not in slots:
            unknown.append(name)
            continue
        im, why = check_image(data)
        if im is None:
            rejected.append((name, why))
            continue
        im.save(dest(slot))
        imported.append((slot, im.size[0]))
    sizes = {s for _n, s in imported}
    for slot, size in imported:
        print(f"  imported  {slot}  ({size}x{size})")
    for name, why in rejected:
        print(f"  REJECTED  {name}: {why}")
    for name in unknown:
        print(f"  skipped   {name}: not a Course Craft slot name (see TEXTURES.md)")
    if len(sizes) > 1:
        print(f"  note: mixed sizes {sorted(sizes)}; Bedrock scales them, but matching sizes look best.")
    print(f"{len(imported)} imported, {len(rejected)} rejected, {len(unknown)} skipped.")
    return 0 if not rejected else 1


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IN
    if not os.path.exists(src):
        os.makedirs(DEFAULT_IN, exist_ok=True)
        print(f"Put your PNGs in {DEFAULT_IN} and run again.")
        return 1
    return run(src)


if __name__ == "__main__":
    sys.exit(main())
