#!/usr/bin/env python3
"""
Render a front view of a generated character straight from its .geo.json boxes
and .png skin, so the result can be eyeballed before it ever reaches a console.

    python3 scripts/preview_pack.py build/<id> [out.png]
"""
import glob
import json
import os
import sys

from PIL import Image, ImageDraw


def face_north(u, v, w, h, d):
    return (u + d, v + d, w, h)


def main():
    pack = sys.argv[1]
    rp = os.path.join(pack, "JunkBunch_RP")
    geo_path = glob.glob(os.path.join(rp, "models/entity/*.geo.json"))[0]
    geo = json.load(open(geo_path))["minecraft:geometry"][0]
    cid = os.path.basename(geo_path).replace(".geo.json", "")
    tex = Image.open(os.path.join(rp, f"textures/entity/junkbunch/{cid}.png")).convert("RGBA")

    ce = json.load(open(os.path.join(rp, "entity", f"{cid}.json")))
    bp_ent = glob.glob(os.path.join(pack, "JunkBunch_BP/entities/*.json"))[0]
    scale = json.load(open(bp_ent))["minecraft:entity"]["components"]["minecraft:scale"]["value"]

    bones = {b["name"]: b for b in geo["bones"]}
    cubes = [(n, c) for n, b in bones.items() for c in b.get("cubes", [])]

    ys = [c["origin"][1] for _, c in cubes] + [c["origin"][1] + c["size"][1] for _, c in cubes]
    xs = [c["origin"][0] for _, c in cubes] + [c["origin"][0] + c["size"][0] for _, c in cubes]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)

    UNIT = 16
    eff = UNIT * scale
    pad = 70
    player_px = int(1.8 * 16 * eff)
    W = int((maxx - minx) * eff) + pad * 2 + 150
    H = player_px + pad * 2

    img = Image.new("RGBA", (W, H), (246, 247, 245, 255))
    d = ImageDraw.Draw(img)
    ground = H - pad
    cx = pad - int(minx * eff)

    # player reference
    px0 = W - pad - 46
    d.rectangle([px0, ground - player_px, px0 + 34, ground], fill=(206, 212, 216), outline=(150, 157, 162))
    d.text((px0 - 4, ground + 8), "player 1.8", fill=(105, 112, 108))

    order = [n for n in ["left_leg", "right_leg", "left_arm", "right_arm", "body", "topper"]
             if n in bones] or [n for n in bones if bones[n].get("cubes")]
    for name in order:
        b = bones.get(name)
        if not b:
            continue
        for c in b.get("cubes", []):
            ox, oy, _ = c["origin"]
            w, h, dep = c["size"]
            u = c["uv"]
            if isinstance(u, dict):
                n = u["north"]
                fx, fy = n["uv"]
                fw, fh = n["uv_size"]
            else:
                fx, fy, fw, fh = face_north(u[0], u[1], w, h, dep)
            face = tex.crop((fx, fy, fx + fw, fy + fh)).resize(
                (max(1, int(w * eff)), max(1, int(h * eff))), Image.NEAREST)
            img.alpha_composite(face, (int(cx + ox * eff), int(ground - (oy + h) * eff)))

    height_blocks = (maxy - miny) * scale / 16
    d.text((pad - 10, ground + 8), f"{cid}  ~{height_blocks:.2f} blocks", fill=(105, 112, 108))

    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(pack, "preview.png")
    img.save(out)
    print(f"wrote {out}  ({W}x{H}, character ~{height_blocks:.2f} blocks)")


if __name__ == "__main__":
    main()
