#!/usr/bin/env python3
"""Render a Bedrock .geo.json (box UV, format 1.12.0) with its texture, orthographic,
from the four visual-gate views, beside a 1.8-block player reference.

Draws every visible face texel-by-texel from the texture, so a UV mistake shows up
as a wrong-coloured face. Approximation limits (stated, not hidden): no bone
rotation/animation, painter's-algorithm depth sort, no Bedrock lighting/material.
"""
import json
import math
import os

from PIL import Image, ImageDraw

S = 11            # pixels per model unit
PLAYER_UNITS = 1.8 * 16
VIEWS = {"front": (0, 0), "side": (90, 0), "back": (180, 0), "three_quarter": (35, 22)}


def faces(origin, size, uv):
    ox, oy, oz = origin
    w, h, d = size
    u, v = uv
    # (texture region x, y, cols, rows, corner, U axis, V axis, outward normal)
    return [
        (u + d, v + d, w, h, (ox + w, oy + h, oz), (-1, 0, 0), (0, -1, 0), (0, 0, -1)),        # north
        (u + 2 * d + w, v + d, w, h, (ox, oy + h, oz + d), (1, 0, 0), (0, -1, 0), (0, 0, 1)),  # south
        (u, v + d, d, h, (ox + w, oy + h, oz + d), (0, 0, -1), (0, -1, 0), (1, 0, 0)),         # east
        (u + d + w, v + d, d, h, (ox, oy + h, oz), (0, 0, 1), (0, -1, 0), (-1, 0, 0)),         # west
        (u + d, v, w, d, (ox, oy + h, oz), (1, 0, 0), (0, 0, 1), (0, 1, 0)),                   # up
        (u + d + w, v, w, d, (ox, oy, oz), (1, 0, 0), (0, 0, 1), (0, -1, 0)),                  # down
    ]


def project(p, yaw, pitch):
    a, b = math.radians(yaw), math.radians(pitch)
    x, y, z = p
    x1 = x * math.cos(a) + z * math.sin(a)
    z1 = -x * math.sin(a) + z * math.cos(a)
    y2 = y * math.cos(b) + z1 * math.sin(b)
    z2 = -y * math.sin(b) + z1 * math.cos(b)
    return (-x1, y2, z2)


def render(geo_path, tex_path, yaw, pitch, label=""):
    geo = json.load(open(geo_path))["minecraft:geometry"][0]
    tex = Image.open(tex_path).convert("RGBA")
    tw, th = geo["description"]["texture_width"], geo["description"]["texture_height"]
    sx, sy = tex.width / tw, tex.height / th  # allows hi-res skins with the same UV layout
    quads = []
    for bone in geo["bones"]:
        for c in bone.get("cubes", []):
            for (tx, ty, cols, rows, corner, U, V, n) in faces(c["origin"], c["size"], c["uv"]):
                if project(n, yaw, pitch)[2] >= -1e-6:
                    continue  # back-facing
                for j in range(rows):
                    for i in range(cols):
                        col = tex.getpixel((min(tex.width - 1, int((tx + i + 0.5) * sx)), min(tex.height - 1, int((ty + j + 0.5) * sy))))
                        if col[3] < 128:
                            continue
                        pts3 = [tuple(corner[k] + U[k] * (i + du) + V[k] * (j + dv) for k in range(3))
                                for du, dv in ((0, 0), (1, 0), (1, 1), (0, 1))]
                        pr = [project(p, yaw, pitch) for p in pts3]
                        quads.append((sum(p[2] for p in pr) / 4, [(p[0], p[1]) for p in pr], col))
    quads.sort(key=lambda q: -q[0])
    xs = [p[0] for q in quads for p in q[1]]
    ys = [p[1] for q in quads for p in q[1]]
    minx, maxx, maxy = min(xs), max(xs), max(max(ys), PLAYER_UNITS)
    pad, ref_w = 30, 60
    W = int((maxx - minx) * S) + pad * 3 + ref_w
    H = int((maxy - min(0, min(ys))) * S) + pad * 2 + 20
    img = Image.new("RGBA", (W, H), (236, 240, 244, 255))
    d = ImageDraw.Draw(img)
    ground = H - pad - 20
    ox = pad - minx * S
    d.line([(0, ground), (W, ground)], fill=(170, 175, 180, 255))
    for _z, pts, col in quads:
        d.polygon([(ox + x * S, ground - y * S) for x, y in pts], fill=col, outline=col)
    px = W - pad - ref_w + 20
    d.rectangle([px, ground - PLAYER_UNITS * S * math.cos(math.radians(pitch)), px + 0.6 * 16 * S / 2, ground],
                fill=(200, 205, 212, 255), outline=(140, 145, 150, 255))
    d.text((px - 14, ground + 4), "player 1.8", fill=(80, 85, 90, 255))
    d.text((6, 6), label, fill=(40, 40, 50, 255))
    return img


def render_all(geo_path, tex_path, out_dir, stem, name):
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for view, (yaw, pitch) in VIEWS.items():
        p = os.path.join(out_dir, f"{stem}_{view}.png")
        render(geo_path, tex_path, yaw, pitch, f"{name} - {view}").save(p)
        paths[view] = p
    return paths
