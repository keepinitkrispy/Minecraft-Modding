#!/usr/bin/env python3
"""Build enemy geometry (.geo.json, format 1.12.0, box UV) + base-material textures
from tools/enemies.py, then render the ACTUAL geometry for the visual gate.

Writes into packs/CourseCraft_RP/{models/entity,textures/entity} and
characters/renders/<id>_{front,side,back,three_quarter}.png.
Behavior-pack entities are deliberately NOT generated here: per WORKFLOW.md,
gameplay engineering waits until the visual gate is approved.
"""
import json
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from enemies import ENEMIES  # noqa: E402
import render_geo  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "packs", "CourseCraft_RP")
TEX = 64


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c) + (255,)


def pack_uvs(cubes):
    """Shelf-pack box-UV nets (2*(d+w) x (d+h)) into a TEX x TEX sheet."""
    x = y = row_h = 0
    uvs = []
    for (_o, s, *_r) in cubes:
        w, h, d = s
        nw, nh = 2 * (d + w), d + h
        if x + nw > TEX:
            x, y, row_h = 0, y + row_h, 0
        if y + nh > TEX:
            raise ValueError("texture sheet overflow; raise TEX")
        uvs.append((x, y))
        x += nw
        row_h = max(row_h, nh)
    return uvs


def paint(img, uv, size, colour, front_paint):
    u, v = uv
    w, h, d = size
    px = img.load()

    def rect(x0, y0, rw, rh, c):
        for yy in range(y0, y0 + rh):
            for xx in range(x0, x0 + rw):
                px[xx, yy] = c

    rect(u + d, v, w, d, shade(colour, 1.15))            # up
    rect(u + d + w, v, w, d, shade(colour, 0.7))         # down
    rect(u, v + d, d, h, shade(colour, 0.9))             # east
    rect(u + d, v + d, w, h, shade(colour, 1.0))         # north (front)
    rect(u + d + w, v + d, d, h, shade(colour, 0.9))     # west
    rect(u + 2 * d + w, v + d, w, h, shade(colour, 0.85))  # south
    for (fx, fy, fw, fh, c) in front_paint or []:
        rect(u + d + fx, v + d + fy, fw, fh, c + (255,))


def build(eid, e):
    flat = [c for b in e["bones"] for c in b["cubes"]]
    uvs = pack_uvs(flat)
    img = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))
    bones, i = [], 0
    for b in e["bones"]:
        cubes = []
        for c in b["cubes"]:
            o, s, col = c[0], c[1], c[2]
            paint(img, uvs[i], s, col, c[3] if len(c) > 3 else None)
            cubes.append({"origin": o, "size": s, "uv": list(uvs[i])})
            i += 1
        bones.append({"name": b["name"], "pivot": b["pivot"], "cubes": cubes})
    xs = [v for c in flat for v in (c[0][0], c[0][0] + c[1][0])]
    ys = [v for c in flat for v in (c[0][1], c[0][1] + c[1][1])]
    geo = {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": f"geometry.cc.{eid}", "texture_width": TEX, "texture_height": TEX,
                        "visible_bounds_width": max(2, round((max(xs) - min(xs)) / 16 + 1)),
                        "visible_bounds_height": max(2, round((max(ys) - min(ys)) / 16 + 1)),
                        "visible_bounds_offset": [0, (max(ys) / 32), 0]},
        "bones": bones}]}
    gpath = os.path.join(RP, "models", "entity", f"cc_{eid}.geo.json")
    tpath = os.path.join(RP, "textures", "entity", f"cc_{eid}.png")
    os.makedirs(os.path.dirname(gpath), exist_ok=True)
    os.makedirs(os.path.dirname(tpath), exist_ok=True)
    with open(gpath, "w") as fh:
        json.dump(geo, fh, indent=2); fh.write("\n")
    if not os.path.exists(tpath) or "--repaint" in sys.argv:
        img.save(tpath)
    renders = render_geo.render_all(gpath, tpath, os.path.join(ROOT, "characters", "renders"), f"cc_{eid}", e["name"])
    return gpath, tpath, renders


def main():
    for eid, e in ENEMIES.items():
        g, t, r = build(eid, e)
        print(f"{eid}: {os.path.relpath(g, ROOT)}  {os.path.relpath(t, ROOT)}  renders={len(r)}")


if __name__ == "__main__":
    main()
