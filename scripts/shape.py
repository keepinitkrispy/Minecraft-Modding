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
SOLID = {"body": (40, 0), "dark": (42, 0), "accent": (44, 0), "limb": (46, 0)}


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


def clean_profile(solid, gw=GRID_W, gh=GRID_H):
    """Turn a ragged trace into a clean, symmetric silhouette.

    A pencil outline scanned to a grid is lopsided and lumpy. We keep what the
    drawing actually says - how wide the character is at each height - then
    centre and smooth it. The result is the same creature, drawn cleanly.
    Arm spikes are removed here; limbs are added back as their own parts.
    """
    widths = []
    for row in solid:
        n = sum(1 for v in row if v)
        widths.append(n)

    rows = [i for i, w in enumerate(widths) if w > 0]
    if not rows:
        return []
    top, bot = rows[0], rows[-1]

    core = widths[top:bot + 1]
    # median filter kills the outstretched-arm spikes
    med = []
    for i in range(len(core)):
        lo = max(0, i - 2); hi = min(len(core), i + 3)
        win = sorted(core[lo:hi])
        med.append(win[len(win) // 2])
    # then a mean pass for a smooth curve
    prof = []
    for i in range(len(med)):
        lo = max(0, i - 1); hi = min(len(med), i + 2)
        prof.append(sum(med[lo:hi]) / (hi - lo))

    prof = [max(1, int(round(w))) for w in prof]

    # A hand-drawn outline rarely closes to a point, so the raw profile starts
    # and ends blunt. Re-cast it as a pointed oval that keeps the drawing's own
    # widest measurement and height - the creature it was drawn as, drawn well.
    import math
    n = len(prof)
    peak = max(prof)
    fullness = sum(prof) / float(peak * n)          # how round vs how pointed
    power = 1.15 - 0.75 * min(1.0, max(0.0, fullness))
    shaped = []
    for i in range(n):
        t = (i + 0.5) / n
        shaped.append(max(1, int(round(peak * (math.sin(math.pi * t) ** power)))))
    return shaped


def stylised_cubes(profile, gw=GRID_W, gh=GRID_H):
    """Body from the cleaned profile, plus the stick limbs and stem
    that every Junk Bunch character is drawn with."""
    if not profile:
        return []

    body_top = 2                       # rows reserved for the stem
    leg_rows = 3                       # rows reserved for the legs
    room = gh - body_top - leg_rows
    if len(profile) > room:            # squeeze the profile to fit
        step = len(profile) / float(room)
        profile = [profile[min(len(profile) - 1, int(i * step))] for i in range(room)]
    n = len(profile)

    cubes = []
    for i, w in enumerate(profile):
        r = body_top + i
        if r >= gh:
            break
        half = max(1, w // 2)
        c0 = gw // 2 - half
        c1 = gw // 2 + half - (0 if w % 2 else 1)
        c0 = max(0, c0); c1 = min(gw - 1, c1)
        cubes.append({"c0": c0, "c1": c1, "r0": r, "r1": r, "part": "body"})

    # merge identical neighbouring rows so the model stays light
    merged = []
    for c in cubes:
        if merged and merged[-1]["c0"] == c["c0"] and merged[-1]["c1"] == c["c1"] \
           and merged[-1]["r1"] == c["r0"] - 1 and merged[-1]["part"] == "body":
            merged[-1]["r1"] = c["r1"]
        else:
            merged.append(dict(c))

    body_bottom = merged[-1]["r1"]
    widest_i = max(range(n), key=lambda i: profile[i])
    arm_r = body_top + widest_i
    arm_len = 3

    def edge_at(r):
        for c in merged:
            if c["r0"] <= r <= c["r1"]:
                return c["c0"], c["c1"]
        return gw // 2, gw // 2

    l, rgt = edge_at(arm_r)
    merged.append({"c0": max(0, l - arm_len), "c1": max(0, l - 1),
                   "r0": arm_r, "r1": arm_r, "part": "limb"})
    merged.append({"c0": min(gw - 1, rgt + 1), "c1": min(gw - 1, rgt + arm_len),
                   "r0": arm_r, "r1": arm_r, "part": "limb"})

    # two legs under the body
    leg_top = body_bottom + 1
    leg_bot = min(gh - 1, leg_top + 2)
    if leg_top < gh:
        bl, br = edge_at(body_bottom)
        span = br - bl
        lx = bl + max(1, span // 4)
        rx = br - max(1, span // 4)
        merged.append({"c0": lx, "c1": lx, "r0": leg_top, "r1": leg_bot, "part": "limb"})
        merged.append({"c0": rx, "c1": rx, "r0": leg_top, "r1": leg_bot, "part": "limb"})

    # stem on top
    merged.append({"c0": gw // 2, "c1": gw // 2,
                   "r0": max(0, body_top - 2), "r1": max(0, body_top - 1), "part": "stem"})
    return merged


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


PART_UV = {"body": None, "limb": (46, 0), "stem": (46, 0)}


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
        part = c.get("part", "body")
        depth = DEPTH if part == "body" else DEPTH * 0.5
        flat = PART_UV.get(part)
        if flat:
            face = {"uv": list(flat), "uv_size": [1, 1]}
            uv = {k: face for k in ("north", "south", "west", "east", "up", "down")}
        else:
            uv = {
                "north": {"uv": [c["c0"], c["r0"]],
                          "uv_size": [c["c1"] - c["c0"] + 1, c["r1"] - c["r0"] + 1]},
                "south": {"uv": [c["c0"], c["r0"]],
                          "uv_size": [c["c1"] - c["c0"] + 1, c["r1"] - c["r0"] + 1]},
                "west":  {"uv": list(sd), "uv_size": [1, 1]},
                "east":  {"uv": list(sd), "uv_size": [1, 1]},
                "up":    {"uv": list(sb), "uv_size": [1, 1]},
                "down":  {"uv": list(sb), "uv_size": [1, 1]},
            }
        body["cubes"].append({
            "origin": [round(ox, 3), round(oy, 3), round(-depth / 2.0, 3)],
            "size": [round(w, 3), round(h, 3), round(depth, 3)],
            "uv": uv,
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
                  tex=64, gw=GRID_W, gh=GRID_H, cubes=None, limb=None):
    """Leaf body with a centre vein, the drawn face on top, and side swatches."""
    img = Image.new("RGBA", (tex, tex), tuple(int(v) for v in primary) + (255,))
    p = img.load()
    pr = tuple(int(v) for v in primary)
    dk = tuple(int(v) for v in dark)
    vein = tuple(int(v) for v in [(a * 2 + b) / 3 for a, b in zip(primary, dark)])

    for gy in range(gh):
        for gx in range(gw):
            p[gx, gy] = pr + (255,)

    # centre vein and side veins, like a real leaf
    mid = gw // 2
    rows = [c for c in (cubes or []) if c.get("part") == "body"]
    if rows:
        top = min(c["r0"] for c in rows)
        bot = max(c["r1"] for c in rows)
        for r in range(top, bot + 1):
            p[mid, r] = vein + (255,)
        step = max(2, (bot - top) // 6)
        for i, r in enumerate(range(top + step, bot - step + 1, step)):
            reach = 2 + (i % 2)
            for k in range(1, reach + 1):
                if mid - k >= 0 and r + k < gh:
                    p[mid - k, r + k] = vein + (255,)
                if mid + k < gw and r + k < gh:
                    p[mid + k, r + k] = vein + (255,)

    # a clean face, placed on the widest part of the leaf
    if rows:
        widest = max(rows, key=lambda c: c["c1"] - c["c0"])
        fy = max(top + 2, (top + bot) // 2 - 3)
        halfspan = max(2, (widest["c1"] - widest["c0"]) // 5)
        eye_l, eye_r = mid - halfspan, mid + halfspan
        for ex in (eye_l, eye_r):
            for dy in range(2):
                for dx in range(2):
                    if 0 <= ex + dx < gw and 0 <= fy + dy < gh:
                        p[ex + dx, fy + dy] = (18, 22, 18, 255)
        smile_y = fy + 4
        for k in range(-halfspan, halfspan + 1):
            x = mid + k
            y = smile_y + (1 if abs(k) <= 1 else 0)
            if 0 <= x < gw and 0 <= y < gh:
                p[x, y] = (18, 22, 18, 255)
        for x, y in ((mid - halfspan - 1, smile_y - 1), (mid + halfspan + 1, smile_y - 1)):
            if 0 <= x < gw and 0 <= y < gh:
                p[x, y] = (18, 22, 18, 255)

    for name, col in (("body", primary), ("dark", dark), ("accent", accent),
                      ("limb", limb if limb is not None else dark)):
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
