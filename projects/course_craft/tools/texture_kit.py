#!/usr/bin/env python3
"""Export the current textures as an editable kit.

Writes:
  texture_kit/CourseCraft_texture_kit.zip  - every slot PNG, correctly named; edit and re-import
  texture_kit/TEXTURE_GUIDE.png            - labelled preview of every slot
Usage: python3 tools/texture_kit.py
"""
import os
import sys
import zipfile

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec  # noqa: E402
from import_textures import dest  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "texture_kit")


def main():
    os.makedirs(OUT, exist_ok=True)
    slots = spec.all_slots()
    with zipfile.ZipFile(os.path.join(OUT, "CourseCraft_texture_kit.zip"), "w", zipfile.ZIP_DEFLATED) as zf:
        for s in slots:
            zf.write(dest(s), f"{s}.png")
    cell, cols = 128, 4
    rows = (len(slots) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * (cell + 16) + 16, rows * (cell + 44) + 16), (40, 40, 48, 255))
    d = ImageDraw.Draw(sheet)
    for i, s in enumerate(slots):
        x = 16 + (i % cols) * (cell + 16)
        y = 16 + (i // cols) * (cell + 44)
        im = Image.open(dest(s)).convert("RGBA").resize((cell, cell), Image.NEAREST)
        sheet.alpha_composite(im, (x, y))
        d.text((x, y + cell + 4), s, fill=(255, 255, 255, 255))
        d.text((x, y + cell + 18), spec.SLOT_HINTS[s][:24], fill=(170, 170, 185, 255))
    sheet.save(os.path.join(OUT, "TEXTURE_GUIDE.png"))
    print(f"Wrote {len(slots)} slots to texture_kit/CourseCraft_texture_kit.zip and texture_kit/TEXTURE_GUIDE.png")


if __name__ == "__main__":
    main()
