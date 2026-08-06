#!/usr/bin/env python3
"""
Turn a drawing into a Bedrock model whose SHAPE is the drawing's shape.

The earlier approach kept a fixed humanoid body and pasted the drawing on the
front, so a leaf came out as a rectangle wearing a picture of a leaf. Here the
silhouette drives the geometry: the drawing is reduced to an occupancy grid,
the interior is flood filled, and each horizontal run of solid cells becomes a
cube. A leaf gives a leaf-shaped mob; a mound gives a mound-shaped mob.

Per-face UVs let every cube's front face sample exactly its own slice of the
drawing, so the art lines up with the geometry no matter how the shape is cut.
"""

from PIL import Image, ImageFilter

GRID_W = 22          # cells across
GRID_H = 30          # cells tall
DEPTH = 4            # model units of thickness
CELL = 1.0           # model units per cell

# where the flat colour swatches live on the texture sheet
SOLID = {"body": (40, 0), "dark": (42, 0), "accent": (44, 0)}


def luma(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def dist(a, b):
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) ** 0.5


def occupancy(crop, bg, thresh, gw=GRID_W, gh=GRID_H, cover=0.10):
    """Fraction of each grid cell that is ink, then a boolean ink map."""
    img = crop.convert("RGB")
    if min(img.size) >= 5:
        img = img.filter(ImageFilter.MedianFilter(3))
    W, H = img.size
    px = img.load()
    ink = [[False] * gw for _ in range(gh)]
    for gy in range(gh):
        for gx in range(gw):
            x0 = int(gx * W / gw); x1 = max(x0 + 1, int((gx + 1) * W / gw))
            y0 = int(gy * H / gh); y1 = max(y0 + 1, int((gy + 1) * H / gh))
            d = t = 0
            for yy in range(y0, min(y1, H)):
                for xx in range(x0, min(x1, W)):
                    t += 1
                    if dist(px[xx, yy], bg) > thresh:
                        d += 1
            ink[gy][gx] = bool(t) and (d / t) >= cover
    return ink


def solidify(ink):
    """Ink outline -> filled shape.

    Flood fill from the border across non-ink cells; whatever the fill cannot
    reach is inside the drawing. That fills a leaf's body while leaving real
    gaps (between two legs, or under an arm) genuinely empty.
    """
    gh, gw = len(ink), len(ink[0])
    outside = [[False] * gw for _ in range(gh)]
    stack = []
    for x in range(gw):
        for y in (0, gh - 1):
            if not ink[y][x] and not outside[y][x]:
                outside[y][x] = True; stack.append((x, y))
    for y in range(gh):
        for x in (0, gw - 1):
            if not ink[y][x] and not outside[y][x]:
                outside[y][x] = True; stack.append((x, y))
    while stack:
        x, y = stack.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < gw and 0 <= ny < gh and not ink[ny][nx] and not outside[ny][nx]:
                outside[ny][nx] = True
                stack.append((nx, ny))
    return [[ink[y][x] or not outside[y][x] for x in range(gw)] for y in range(gh)]


def largest_component(solid):
    """Keep only the main mass, so specks of grain do not float beside the mob."""
    gh, gw = len(solid), len(solid[0])
    seen = [[False] * gw for _ in range(gh)]
    best = []
    for y in range(gh):
        for x in range(gw):
            if solid[y][x] and not seen[y][x]:
                stack, cells = [(x, y)], []
                seen[y][x] = True
                while stack:
                    cx, cy = stack.pop()
                    cells.append((cx, cy))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < gw and 0 <= ny < gh and solid[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            stack.append((nx, ny))
                if len(cells) > len(best):
                    best = cells
    out = [[False] * gw for _ in range(gh)]
    for x, y in best:
        out[y][x] = True
    return out


def smooth(solid):
    """Fill single-cell notches and shave single-cell spurs.

    A hand drawing scanned to a 16-wide grid has ragged edges; this keeps the
    silhouette readable without changing its overall form.
    """
    gh, gw = len(solid), len(solid[0])

    def neighbours(g, x, y):
        n = 0
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < gw and 0 <= ny < gh and g[ny][nx]:
                n += 1
        return n

    cur = [row[:] for row in solid]
    for _ in range(2):
        nxt = [row[:] for row in cur]
        for y in range(gh):
            for x in range(gw):
                n = neighbours(cur, x, y)
                if not cur[y][x] and n >= 3:
                    nxt[y][x] = True        # fill a notch
                elif cur[y][x] and n <= 1:
                    nxt[y][x] = False       # shave a spur
        cur = nxt
    return cur


def runs_of(row):
    out, x = [], 0
    gw = len(row)
    while x < gw:
        if row[x]:
            x0 = x
            while x < gw and row[x]:
                x += 1
            out.append((x0, x - 1))
        else:
            x += 1
    return out


def cubes_from(solid):
    """One cube per horizontal run, merged down while the runs stay identical."""
    gh = len(solid)
    rows = [runs_of(r) for r in solid]
    used = [False] * gh
    cubes = []
    for y in range(gh):
        if used[y] or not rows[y]:
            continue
        y2 = y
        while y2 + 1 < gh and rows[y2 + 1] == rows[y]:
            y2 += 1
        for yy in range(y, y2 + 1):
            used[yy] = True
        for (c0, c1) in rows[y]:
            cubes.append({"c0": c0, "c1": c1, "r0": y, "r1": y2})
    return cubes


def build_geometry(cid, cubes, tex_w, tex_h, gh=GRID_H, gw=GRID_W):
    """Bedrock geometry with per-face UVs so art and shape always agree."""
    bones = [{"name": "root", "pivot": [0, 0, 0], "children": ["body"]}]
    body = {"name": "body", "pivot": [0, 0, 0], "cubes": []}

    sb = SOLID["body"]
    sd = SOLID["dark"]

    for c in cubes:
        w = (c["c1"] - c["c0"] + 1) * CELL
        h = (c["r1"] - c["r0"] + 1) * CELL
        # centre horizontally; row 0 is the TOP of the drawing
        ox = (c["c0"] - gw / 2.0) * CELL
        oy = (gh - 1 - c["r1"]) * CELL
        body["cubes"].append({
            "origin": [round(ox, 3), round(oy, 3), -DEPTH / 2.0],
            "size": [round(w, 3), round(h, 3), DEPTH],
            "uv": {
                # front and back sample the drawing itself
                "north": {"uv": [c["c0"], c["r0"]], "uv_size": [c["c1"] - c["c0"] + 1,
                                                                c["r1"] - c["r0"] + 1]},
                "south": {"uv": [c["c0"], c["r0"]], "uv_size": [c["c1"] - c["c0"] + 1,
                                                                c["r1"] - c["r0"] + 1]},
                # the thin sides use flat colour
                "west":  {"uv": list(sd), "uv_size": [1, 1]},
                "east":  {"uv": list(sd), "uv_size": [1, 1]},
                "up":    {"uv": list(sb), "uv_size": [1, 1]},
                "down":  {"uv": list(sb), "uv_size": [1, 1]},
            },
        })

    bones.append(body)
    return {
        "format_version": "1.16.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": f"geometry.{cid}.main",
                "texture_width": tex_w,
                "texture_height": tex_h,
                "visible_bounds_width": 4,
                "visible_bounds_height": 4,
                "visible_bounds_offset": [0, 1, 0],
            },
            "bones": bones,
        }],
    }


def build_texture(crop, bg, thresh, ink_map, solid, primary, dark, accent,
                  tex=64, gw=GRID_W, gh=GRID_H):
    """The drawing itself in the top-left, plus flat swatches for the sides."""
    img = Image.new("RGBA", (tex, tex), tuple(int(v) for v in primary) + (255,))
    p = img.load()
    pr = tuple(int(v) for v in primary)
    dk = tuple(int(v) for v in dark)

    for gy in range(gh):
        for gx in range(gw):
            if ink_map[gy][gx]:
                p[gx, gy] = dk + (255,)
            elif solid[gy][gx]:
                p[gx, gy] = pr + (255,)
            else:
                p[gx, gy] = pr + (255,)      # never sampled, kept opaque

    for name, col in (("body", primary), ("dark", dark), ("accent", accent)):
        x, y = SOLID[name]
        c = tuple(int(v) for v in col) + (255,)
        for dy in range(2):
            for dx in range(2):
                if x + dx < tex and y + dy < tex:
                    p[x + dx, y + dy] = c

    for y in range(tex):
        for x in range(tex):
            r, g, b, _ = p[x, y]
            p[x, y] = (r, g, b, 255)
    return img


def model_height_units(cubes, gh=GRID_H):
    top = min(c["r0"] for c in cubes)
    bot = max(c["r1"] for c in cubes)
    return (bot - top + 1) * CELL
