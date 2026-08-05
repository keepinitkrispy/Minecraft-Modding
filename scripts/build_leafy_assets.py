#!/usr/bin/env python3
"""
Generate Leafy's geometry and texture together from ONE source of truth.

Why this exists: an entity's .geo.json box-UV layout and its .png skin must agree
pixel-for-pixel, and the skin must be fully opaque, or faces render invisible under
the entity_alphatest material. Hand-drawing a 2D "sticker" and hoping it lines up
with the 3D boxes does not work. This script defines the boxes once, computes the
exact Bedrock box-UV rectangle for every face, and paints those rectangles - so the
model is guaranteed to render with the right colors.

Outputs:
    packs/JunkBunch_RP/models/entity/leafy.geo.json
    packs/JunkBunch_RP/textures/entity/characters/leafy.png
"""

import json
import os
from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(REPO, "packs", "JunkBunch_RP")

TEX_W, TEX_H = 64, 64

# Colours ------------------------------------------------------------------
LEAF        = (58, 150, 90, 255)     # main body green
LEAF_DARK   = (32, 92, 54, 255)      # veins / shading
LEAF_LIGHT  = (128, 205, 140, 255)   # highlight
STEM        = (96, 138, 66, 255)     # stem green-brown
WOOD        = (120, 82, 45, 255)     # limbs
WOOD_DARK   = (86, 58, 32, 255)
BLACK       = (20, 20, 20, 255)

# Box definitions: name, origin (min corner x,y,z), size (x,y,z), uv (u,v), colour
# origin/size are in Bedrock model units (16 = 1 block). Pivot defaults to a sensible
# point. UV regions are hand-placed so none overlap inside the 64x64 sheet.
BOXES = [
    # name        origin            size          uv        base colour
    ("body",     (-3.5, 0,  -3),   (7, 12, 6),   (0, 0),   LEAF),
    ("face",     (-2.5, 6,  -3.6), (5, 5, 1),    (28, 0),  LEAF_LIGHT),
    ("stem",     (-0.5, 12, -0.5), (1, 3, 1),    (28, 8),  STEM),
    ("left_arm", (-6.5, 6,  -0.5), (3, 1, 1),    (0, 20),  WOOD),
    ("right_arm",(3.5,  6,  -0.5), (3, 1, 1),    (10, 20), WOOD),
    ("left_leg", (-2.5, -3, -0.5), (1, 3, 1),    (20, 20), WOOD),
    ("right_leg",(1.5,  -3, -0.5), (1, 3, 1),    (26, 20), WOOD),
]

BONE_TREE = {
    "root": ["body"],
    "body": ["face", "stem", "left_arm", "right_arm", "left_leg", "right_leg"],
}
PIVOTS = {
    "root": [0, 0, 0],
    "body": [0, 0, 0],
    "face": [0, 7, -3],
    "stem": [0, 12, 0],
    "left_arm": [-3.5, 6, 0],
    "right_arm": [3.5, 6, 0],
    "left_leg": [-1.5, 0, 0],
    "right_leg": [1.5, 0, 0],
}
ROTATIONS = {
    "stem": [0, 0, 8],
    "left_arm": [0, 0, -8],
    "right_arm": [0, 0, 8],
}


def box_uv_faces(u, v, w, h, d):
    """Bedrock/Blockbench box-UV net. Returns face -> (x0, y0, fw, fh) in texels."""
    w, h, d = int(round(w)), int(round(h)), int(round(d))
    return {
        "up":    (u + d,           v,     w, d),
        "down":  (u + d + w,       v,     w, d),
        "west":  (u,               v + d, d, h),
        "north": (u + d,           v + d, w, h),   # front
        "east":  (u + d + w,       v + d, d, h),
        "south": (u + 2 * d + w,   v + d, w, h),   # back
    }


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------
def build_geometry():
    box_by_name = {b[0]: b for b in BOXES}
    bones = []
    order = ["root", "body", "face", "stem", "left_arm", "right_arm", "left_leg", "right_leg"]
    for name in order:
        bone = {"name": name, "pivot": PIVOTS[name]}
        if name in ROTATIONS:
            bone["rotation"] = ROTATIONS[name]
        if name in BONE_TREE:
            bone["children"] = BONE_TREE[name]
        if name in box_by_name:
            _, origin, size, uv, _ = box_by_name[name]
            bone["cubes"] = [{"origin": list(origin), "size": list(size), "uv": list(uv)}]
        bones.append(bone)

    return {
        "format_version": "1.16.0",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": "geometry.leafy.main",
                    "texture_width": TEX_W,
                    "texture_height": TEX_H,
                    "visible_bounds_width": 3,
                    "visible_bounds_height": 3,
                    "visible_bounds_offset": [0, 1, 0],
                },
                "bones": bones,
            }
        ],
    }


# --------------------------------------------------------------------------
# texture
# --------------------------------------------------------------------------
def fill(draw, rect, colour):
    x0, y0, w, h = rect
    if w <= 0 or h <= 0:
        return
    draw.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], fill=colour)


def build_texture():
    # Fully opaque base so NO face can ever sample a transparent texel.
    img = Image.new("RGBA", (TEX_W, TEX_H), LEAF)
    draw = ImageDraw.Draw(img)

    for name, origin, size, uv, colour in BOXES:
        w, h, d = size
        faces = box_uv_faces(uv[0], uv[1], w, h, d)
        for rect in faces.values():
            fill(draw, rect, colour)

        if name == "body":
            # veins + highlight on the front (north) face of the body
            nx, ny, nw, nh = faces["north"]
            cx = nx + nw // 2
            draw.line([(cx, ny + 1), (cx, ny + nh - 1)], fill=LEAF_DARK, width=1)
            for i in range(1, 4):
                yy = ny + int(nh * i / 4)
                draw.line([(cx, yy), (cx - 2, yy + 2)], fill=LEAF_DARK)
                draw.line([(cx, yy), (cx + 2, yy + 2)], fill=LEAF_DARK)
            draw.rectangle([nx + 1, ny + 1, nx + 2, ny + 3], fill=LEAF_LIGHT)

        if name == "face":
            # cheeks/blush and a friendly face on BOTH front (north) and back (south)
            for key in ("north", "south"):
                fx, fy, fw, fh = faces[key]   # fw=5, fh=5
                # eyes: single dark pixels, one column in from each side, row 1
                draw.point((fx + 1, fy + 1), fill=BLACK)
                draw.point((fx + fw - 2, fy + 1), fill=BLACK)
                # smile: gentle curve on the lower rows with a clear gap from the eyes
                draw.point((fx + 1, fy + fh - 2), fill=BLACK)
                draw.point((fx + 2, fy + fh - 1), fill=BLACK)
                draw.point((fx + fw - 3, fy + fh - 1), fill=BLACK)
                draw.point((fx + fw - 2, fy + fh - 2), fill=BLACK)

        if name in ("left_arm", "right_arm", "left_leg", "right_leg", "stem"):
            # a little shading line down each limb front
            fx, fy, fw, fh = faces["north"]
            shade = STEM if name == "stem" else WOOD_DARK
            draw.line([(fx, fy), (fx, fy + fh - 1)], fill=shade)

    return img


def build_rake_icon():
    """A clear 16x16 rake item icon on a transparent background (item icons keep alpha)."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # handle (diagonal wooden shaft)
    for i in range(9):
        d.point((5 + i, 13 - i), fill=WOOD)
        d.point((6 + i, 13 - i), fill=WOOD_DARK)
    # head bar
    d.rectangle([2, 3, 11, 4], fill=(150, 150, 155, 255), outline=WOOD_DARK)
    # tines
    for tx in (2, 4, 6, 8, 10):
        d.rectangle([tx, 4, tx, 6], fill=(120, 120, 128, 255))
    return img


def main():
    geo = build_geometry()
    geo_path = os.path.join(RP, "models", "entity", "leafy.geo.json")
    os.makedirs(os.path.dirname(geo_path), exist_ok=True)
    with open(geo_path, "w") as fh:
        json.dump(geo, fh, indent=2)
    print(f"wrote {os.path.relpath(geo_path, REPO)}")

    tex = build_texture()
    tex_path = os.path.join(RP, "textures", "entity", "characters", "leafy.png")
    os.makedirs(os.path.dirname(tex_path), exist_ok=True)
    tex.save(tex_path)
    # report opacity
    px = tex.load()
    opaque = sum(1 for y in range(TEX_H) for x in range(TEX_W) if px[x, y][3] == 255)
    print(f"wrote {os.path.relpath(tex_path, REPO)}  ({opaque}/{TEX_W*TEX_H} opaque texels)")

    rake = build_rake_icon()
    rake_path = os.path.join(RP, "textures", "items", "summon_rake.png")
    os.makedirs(os.path.dirname(rake_path), exist_ok=True)
    rake.save(rake_path)
    print(f"wrote {os.path.relpath(rake_path, REPO)}")


if __name__ == "__main__":
    main()
