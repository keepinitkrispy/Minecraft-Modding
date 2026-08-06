#!/usr/bin/env python3
"""
Faithful trace: clean character art -> Bedrock model + texture.

Built for art produced by an image generator (flat colours, clear silhouette,
often a transparent background). Nothing is smoothed into an idealised blob -
arms, hands, legs and feet survive because every occupied cell becomes geometry
and keeps its own colour.

This is the opposite of the sketch path: a pencil scan needs cleaning up, but
finished art must be reproduced exactly as drawn.
"""

from PIL import Image

GW = 32          # grid across - fine enough for fingers and feet
GH = 40          # grid down
DEPTH = 4
CELL = 1.0
SWATCH = (48, 0)   # flat colour for the thin sides


def dist(a, b):
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) ** 0.5


def load_art(path, rotate=0):
    im = Image.open(path)
    if rotate:
        im = im.rotate(-rotate, expand=True)
    return im.convert("RGBA")


def _background(im):
    """Alpha if the art has it, else the median border colour."""
    a = im.getchannel("A")
    if a.getextrema()[0] < 250:
        return None                              # real transparency present
    rgb = im.convert("RGB")
    W, H = rgb.size
    px = rgb.load()
    ring = []
    for x in range(0, W, 2):
        ring.append(px[x, 0]); ring.append(px[x, H - 1])
    for y in range(0, H, 2):
        ring.append(px[0, y]); ring.append(px[W - 1, y])
    return [sorted(c[i] for c in ring)[len(ring) // 2] for i in range(3)]


def trace(im, gw=GW, gh=GH, thresh=52, cover=0.34):
    """Grid of (occupied, colour) sampled from the art, cropped to its subject."""
    bg = _background(im)
    W, H = im.size
    px = im.load()

    def solid_px(x, y):
        r, g, b, a = px[x, y]
        if bg is None:
            return a > 128
        return a > 128 and dist((r, g, b), bg) > thresh

    xs = [x for x in range(W) for y in range(0, H, 2) if solid_px(x, y)]
    ys = [y for y in range(H) for x in range(0, W, 2) if solid_px(x, y)]
    if not xs or not ys:
        raise SystemExit("no character found in that image")
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)

    # keep the art's aspect ratio inside the grid so nothing is squashed
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    cells_w, cells_h = gw, gh
    if bw / bh > gw / gh:
        cells_h = max(1, int(round(gw * bh / bw)))
    else:
        cells_w = max(1, int(round(gh * bw / bh)))
    offx, offy = (gw - cells_w) // 2, (gh - cells_h) // 2

    grid = [[None] * gw for _ in range(gh)]
    for cy in range(cells_h):
        for cx in range(cells_w):
            sx0 = x0 + int(cx * bw / cells_w); sx1 = max(sx0 + 1, x0 + int((cx + 1) * bw / cells_w))
            sy0 = y0 + int(cy * bh / cells_h); sy1 = max(sy0 + 1, y0 + int((cy + 1) * bh / cells_h))
            n = 0; tot = 0; acc = [0, 0, 0]
            for yy in range(sy0, min(sy1, H)):
                for xx in range(sx0, min(sx1, W)):
                    tot += 1
                    if solid_px(xx, yy):
                        n += 1
                        r, g, b, _ = px[xx, yy]
                        acc[0] += r; acc[1] += g; acc[2] += b
            if tot and n / tot >= cover:
                grid[offy + cy][offx + cx] = (acc[0] // n, acc[1] // n, acc[2] // n)
    return grid


def prune(grid, gw=GW, gh=GH):
    """Drop specks that are not attached to the main body."""
    seen = [[False] * gw for _ in range(gh)]
    best = []
    for y in range(gh):
        for x in range(gw):
            if grid[y][x] is None or seen[y][x]:
                continue
            stack, cells = [(x, y)], []
            seen[y][x] = True
            while stack:
                cx, cy = stack.pop()
                cells.append((cx, cy))
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < gw and 0 <= ny < gh and grid[ny][nx] is not None \
                       and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            if len(cells) > len(best):
                best = cells
    keep = set(best)
    return [[grid[y][x] if (x, y) in keep else None for x in range(gw)] for y in range(gh)]


def cubes(grid, gw=GW, gh=GH):
    """One cube per horizontal run, merged down while runs match exactly."""
    rows = []
    for y in range(gh):
        runs, x = [], 0
        while x < gw:
            if grid[y][x] is not None:
                x0 = x
                while x < gw and grid[y][x] is not None:
                    x += 1
                runs.append((x0, x - 1))
            else:
                x += 1
        rows.append(runs)

    used = [False] * gh
    out = []
    for y in range(gh):
        if used[y] or not rows[y]:
            continue
        y2 = y
        while y2 + 1 < gh and rows[y2 + 1] == rows[y] \
              and all(grid[y2 + 1][x] == grid[y][x]
                      for (a, b) in rows[y] for x in range(a, b + 1)):
            y2 += 1
        for yy in range(y, y2 + 1):
            used[yy] = True
        for (c0, c1) in rows[y]:
            out.append({"c0": c0, "c1": c1, "r0": y, "r1": y2})
    return out


def build_texture(grid, tex=64, gw=GW, gh=GH):
    """The art itself at grid resolution, fully opaque, plus a side swatch."""
    fallback = (150, 150, 150)
    filled = [c for row in grid for c in row if c]
    if filled:
        fallback = tuple(sum(c[i] for c in filled) // len(filled) for i in range(3))
    img = Image.new("RGBA", (tex, tex), fallback + (255,))
    p = img.load()
    for y in range(gh):
        for x in range(gw):
            p[x, y] = (grid[y][x] or fallback) + (255,)
    sx, sy = SWATCH
    dark = tuple(max(0, int(v * 0.62)) for v in fallback)
    for dy in range(2):
        for dx in range(2):
            p[sx + dx, sy + dy] = dark + (255,)
    for y in range(tex):
        for x in range(tex):
            r, g, b, _ = p[x, y]
            p[x, y] = (r, g, b, 255)
    return img


def build_geometry(cid, cs, tex=64, gw=GW, gh=GH):
    body = {"name": "body", "pivot": [0, 0, 0], "cubes": []}
    for c in cs:
        w = (c["c1"] - c["c0"] + 1) * CELL
        h = (c["r1"] - c["r0"] + 1) * CELL
        body["cubes"].append({
            "origin": [round((c["c0"] - gw / 2.0) * CELL, 3),
                       round((gh - 1 - c["r1"]) * CELL, 3),
                       -DEPTH / 2.0],
            "size": [round(w, 3), round(h, 3), DEPTH],
            "uv": {
                "north": {"uv": [c["c0"], c["r0"]],
                          "uv_size": [c["c1"] - c["c0"] + 1, c["r1"] - c["r0"] + 1]},
                "south": {"uv": [c["c0"], c["r0"]],
                          "uv_size": [c["c1"] - c["c0"] + 1, c["r1"] - c["r0"] + 1]},
                "west":  {"uv": list(SWATCH), "uv_size": [1, 1]},
                "east":  {"uv": list(SWATCH), "uv_size": [1, 1]},
                "up":    {"uv": list(SWATCH), "uv_size": [1, 1]},
                "down":  {"uv": list(SWATCH), "uv_size": [1, 1]},
            },
        })
    return {
        "format_version": "1.16.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": f"geometry.{cid}.main",
                "texture_width": tex, "texture_height": tex,
                "visible_bounds_width": 4, "visible_bounds_height": 4,
                "visible_bounds_offset": [0, 1, 0],
            },
            "bones": [{"name": "root", "pivot": [0, 0, 0], "children": ["body"]}, body],
        }],
    }


def dims(cs):
    top = min(c["r0"] for c in cs); bot = max(c["r1"] for c in cs)
    left = min(c["c0"] for c in cs); right = max(c["c1"] for c in cs)
    return (right - left + 1) * CELL, (bot - top + 1) * CELL


def palette(grid):
    """Most-used colours in the art, for the spawn egg and item icon."""
    counts = {}
    for row in grid:
        for c in row:
            if c:
                k = (c[0] >> 4, c[1] >> 4, c[2] >> 4)
                e = counts.setdefault(k, [0, 0, 0, 0])
                e[0] += 1; e[1] += c[0]; e[2] += c[1]; e[3] += c[2]
    top = sorted(counts.values(), key=lambda e: -e[0])[:3]
    pal = [[e[1] // e[0], e[2] // e[0], e[3] // e[0]] for e in top]
    while len(pal) < 3:
        pal.append(pal[-1] if pal else [120, 160, 110])
    return pal
