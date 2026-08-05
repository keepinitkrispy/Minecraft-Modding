#!/usr/bin/env python3
"""
Render a front view of Leafy straight from the .geo.json boxes + the .png skin,
sampling each box's north-face UV region. This is the closest verification to
"does it render in Bedrock" that can be done without a console: if the boxes map
to the wrong texels, it shows here.
"""
import json
import os
from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_SCALE = 0.85       # matches minecraft:scale on the entity
BLOCK_UNITS = 16         # model units per block
PLAYER_BLOCKS = 1.8      # reference height
RP = os.path.join(REPO, "packs", "JunkBunch_RP")

geo = json.load(open(os.path.join(RP, "models", "entity", "leafy.geo.json")))
tex = Image.open(os.path.join(RP, "textures", "entity", "characters", "leafy.png")).convert("RGBA")

bones = {b["name"]: b for b in geo["minecraft:geometry"][0]["bones"]}

SCALE = 20          # px per model unit
PAD = 60

# world extents to size/centre the model
xs, ys = [], []
for b in bones.values():
    for c in b.get("cubes", []):
        ox, oy, oz = c["origin"]; sx, sy, sz = c["size"]
        xs += [ox, ox + sx]; ys += [oy, oy + sy]
minx, maxx = min(xs), max(xs)
miny, maxy = min(ys), max(ys)

eff = SCALE * MODEL_SCALE           # on-screen units per model unit for Leafy
player_px = int(PLAYER_BLOCKS * BLOCK_UNITS * eff)
model_w_px = int((maxx - minx) * eff)

canvas_w = model_w_px + PAD * 2 + 120
canvas_h = player_px + PAD * 2
img = Image.new("RGBA", (canvas_w, canvas_h), (244, 246, 244, 255))
draw = ImageDraw.Draw(img)

ground_y = canvas_h - PAD
leafy_cx = PAD + model_w_px // 2

# player-height reference on the right
pref_x = canvas_w - PAD - 46
draw.rectangle([pref_x, ground_y - player_px, pref_x + 34, ground_y],
               fill=(210, 214, 218, 255), outline=(150, 155, 160, 255))
draw.text((pref_x - 6, ground_y + 6), "player 1.8", fill=(90, 95, 100, 255))
# Leafy height marker line
leafy_top_units = (maxy - miny)
leafy_px = int(leafy_top_units * eff)
draw.line([(PAD - 12, ground_y - leafy_px), (canvas_w - PAD, ground_y - leafy_px)],
          fill=(200, 205, 200, 255))
leafy_blocks = leafy_top_units * MODEL_SCALE / BLOCK_UNITS
draw.text((PAD - 14, ground_y - leafy_px - 16),
          f"Leafy ~{leafy_blocks:.2f} blocks (~half a player)", fill=(120, 140, 120, 255))


def north_face_uv(u, v, w, h, d):
    w, h, d = int(round(w)), int(round(h)), int(round(d))
    return (u + d, v + d, w, h)


origin_px = (leafy_cx - int((minx + (maxx - minx) / 2) * eff), ground_y + int(miny * eff))

for name, b in bones.items():
    for c in b.get("cubes", []):
        ox, oy, oz = c["origin"]; sx, sy, sz = c["size"]; u, v = c["uv"]
        fx, fy, fw, fh = north_face_uv(u, v, sx, sy, sz)
        face = tex.crop((fx, fy, fx + fw, fy + fh))
        dst_w = max(1, int(sx * eff))
        dst_h = max(1, int(sy * eff))
        face = face.resize((dst_w, dst_h), Image.NEAREST)
        sxp = origin_px[0] + int(ox * eff)
        syp = origin_px[1] - int((oy + sy) * eff)
        img.alpha_composite(face, (sxp, syp))

out = os.path.join(REPO, "characters", "leafy_model_preview.png")
img.save(out)
print("wrote", os.path.relpath(out, REPO), img.size,
      f"| Leafy ~{leafy_top_units*MODEL_SCALE/BLOCK_UNITS:.2f} blocks tall")
