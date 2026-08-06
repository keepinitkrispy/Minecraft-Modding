#!/usr/bin/env python3
"""
Generate a complete Bedrock .mcaddon from a child's drawing.

This is the same pipeline the phone web app (web/index.html) runs in the
browser, mirrored here so the output can be checked by validate_packs.py.
Any change to one must be made in the other.

    python3 scripts/generate_character.py <drawing.jpg> <Name> [--trait friendly]
"""

import argparse
import json
import os
import struct
import sys
import zipfile

from PIL import Image, ImageFilter

import shape as S

TEX = 64
MODEL_SCALE = 0.5

# name, origin, size (w,h,d), uv, role
BOXES = [
    ("body",      (-8.0,  6.0, -4.0), (16, 20, 8), (0, 0),   "body"),
    ("left_arm",  (-10.0, 14.0, -1.0), (2, 8, 2),  (48, 0),  "limb"),
    ("right_arm", (8.0,  14.0, -1.0), (2, 8, 2),   (56, 0),  "limb"),
    ("left_leg",  (-4.5,  0.0, -1.0), (2, 6, 2),   (48, 10), "limb"),
    ("right_leg", (2.5,   0.0, -1.0), (2, 6, 2),   (56, 10), "limb"),
    ("topper",    (-1.0, 26.0, -1.0), (2, 4, 2),   (48, 18), "top"),
]

PIVOTS = {
    "root": [0, 0, 0], "body": [0, 6, 0],
    "left_arm": [-8, 22, 0], "right_arm": [8, 22, 0],
    "left_leg": [-3.5, 6, 0], "right_leg": [3.5, 6, 0],
    "topper": [0, 26, 0],
}

TRAITS = {
    "friendly": dict(speed=0.22, stroll=0.9,  look=0.10, scale_adj=0.0),
    "shy":      dict(speed=0.18, stroll=0.6,  look=0.04, scale_adj=-0.05),
    "bouncy":   dict(speed=0.28, stroll=1.15, look=0.08, scale_adj=-0.02),
    "sneaky":   dict(speed=0.26, stroll=1.0,  look=0.05, scale_adj=-0.08),
    "brave":    dict(speed=0.24, stroll=0.85, look=0.12, scale_adj=0.06),
}


def face_rects(u, v, w, h, d):
    return {
        "up":    (u + d,         v,     w, d),
        "down":  (u + d + w,     v,     w, d),
        "west":  (u,             v + d, d, h),
        "north": (u + d,         v + d, w, h),
        "east":  (u + d + w,     v + d, d, h),
        "south": (u + 2 * d + w, v + d, w, h),
    }


def slug(name):
    s = "".join(c.lower() if c.isalnum() else "_" for c in name)
    s = "_".join(p for p in s.split("_") if p)
    if not s or s[0].isdigit():
        s = "jb_" + s
    return s[:24] or "friend"


def uuid_from(seed):
    """Deterministic UUID so regenerating the same character updates it."""
    h1, h2, h3, h4 = 0x811C9DC5, 0x01000193, 0x9E3779B9, 0x85EBCA6B
    M = 0xFFFFFFFF
    for i, ch in enumerate(seed):
        c = ord(ch)
        h1 = ((h1 ^ c) * 16777619) & M
        h2 = ((h2 + c + i) * 2246822519) & M
        h3 = ((h3 ^ (c + i * 7)) * 3266489917) & M
        h4 = ((h4 + c * 31) * 668265263) & M
    s = "%08x%08x%08x%08x" % (h1, h2, h3, h4)
    s = s[:12] + "4" + s[13:]
    s = s[:16] + "89ab"[(h2 >> 28) & 3] + s[17:]
    return f"{s[0:8]}-{s[8:12]}-{s[12:16]}-{s[16:20]}-{s[20:32]}"


def clamp(v, a, b):
    return max(a, min(b, v))


def to_hex(c):
    return "#%02x%02x%02x" % tuple(int(clamp(round(x), 0, 255)) for x in c)


def shade(c, amt):
    return [clamp(x + amt, 0, 255) for x in c]


def mix(a, b, t):
    return [a[i] + (b[i] - a[i]) * t for i in range(3)]


def luma(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def dist(a, b):
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) ** 0.5


def saturation(c):
    mx, mn = max(c), min(c)
    return 0.0 if mx <= 0 else (mx - mn) / mx


def hsl_rgb(h, s, l):
    """h 0-360, s/l 0-1 -> [r,g,b] 0-255"""
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs(((h / 60.0) % 2) - 1))
    m = l - c / 2
    r, g, b = [(c, x, 0), (x, c, 0), (0, c, x),
               (0, x, c), (x, 0, c), (c, 0, x)][int(h // 60) % 6]
    return [(r + m) * 255, (g + m) * 255, (b + m) * 255]


def palette_from_name(seed):
    """A vivid, stable palette for drawings that have no colour of their own."""
    h = 2166136261
    for ch in seed:
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    hue = h % 360
    return (hsl_rgb(hue, 0.52, 0.46),
            hsl_rgb((hue + 28) % 360, 0.45, 0.32),
            hsl_rgb((hue + 165) % 360, 0.62, 0.58))


def analyse(path, crop_frac=None, rotate=0):
    im = Image.open(path).convert("RGB")
    if rotate:
        im = im.rotate(-rotate, expand=True)
    W = 300
    H = max(1, round(im.height / im.width * W))
    im = im.resize((W, H), Image.LANCZOS)

    if crop_frac:
        fx, fy, fw, fh = crop_frac
        box = (int(fx * W), int(fy * H),
               min(W, int((fx + fw) * W)), min(H, int((fy + fh) * H)))
        im = im.crop(box)
        W, H = im.size
    px = im.load()

    ring = []
    for x in range(0, W, 2):
        ring.append(px[x, 0]); ring.append(px[x, H - 1])
    for y in range(0, H, 2):
        ring.append(px[0, y]); ring.append(px[W - 1, y])
    bg = [sorted(c[ch] for c in ring)[len(ring) // 2] for ch in range(3)]

    thresh = 46
    mask = bytearray(W * H)
    for y in range(H):
        for x in range(W):
            if dist(px[x, y], bg) > thresh:
                mask[y * W + x] = 1

    # A page usually holds several drawings. Dilate so a sketch's strokes join
    # into one blob, then keep only the largest blob: that is the character.
    grown = bytearray(mask)
    R = 1
    for y in range(H):
        for x in range(W):
            if not mask[y * W + x]:
                continue
            for dy in range(-R, R + 1):
                for dx in range(-R, R + 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= nx < W and 0 <= ny < H:
                        grown[ny * W + nx] = 1

    best, seen = None, bytearray(W * H)
    for sy in range(H):
        for sx in range(W):
            if grown[sy * W + sx] and not seen[sy * W + sx]:
                stack = [(sx, sy)]
                seen[sy * W + sx] = 1
                ink = 0
                x0 = x1 = sx
                y0 = y1 = sy
                while stack:
                    cx, cy = stack.pop()
                    if mask[cy * W + cx]:
                        ink += 1                      # score by real ink, not blur
                    if cx < x0: x0 = cx
                    if cx > x1: x1 = cx
                    if cy < y0: y0 = cy
                    if cy > y1: y1 = cy
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            nx, ny = cx + dx, cy + dy
                            if 0 <= nx < W and 0 <= ny < H \
                               and grown[ny * W + nx] and not seen[ny * W + nx]:
                                seen[ny * W + nx] = 1
                                stack.append((nx, ny))
                bw, bh = x1 - x0 + 1, y1 - y0 + 1
                if bw < 12 or bh < 12:
                    continue                          # ignore stray marks / numbers
                if best is None or ink > best[0]:
                    best = (ink, x0, y0, x1, y1)

    if best is None:
        minx, miny, maxx, maxy = 0, 0, W - 1, H - 1
    else:
        _, minx, miny, maxx, maxy = best

    padx = round((maxx - minx) * 0.06) + 1
    pady = round((maxy - miny) * 0.06) + 1
    cx0 = clamp(minx - padx, 0, W - 1); cy0 = clamp(miny - pady, 0, H - 1)
    cx1 = clamp(maxx + padx, 0, W - 1); cy1 = clamp(maxy + pady, 0, H - 1)

    buckets = {}
    for y in range(miny, maxy + 1):
        for x in range(minx, maxx + 1):
            c = px[x, y]
            if dist(c, bg) <= thresh or luma(c) < 42:
                continue
            k = (c[0] >> 5, c[1] >> 5, c[2] >> 5)
            e = buckets.setdefault(k, [0, 0, 0, 0])
            e[0] += 1; e[1] += c[0]; e[2] += c[1]; e[3] += c[2]

    pal = sorted((e for e in buckets.values() if e[0] > 8), key=lambda e: -e[0])[:5]
    pal = [[e[1]/e[0], e[2]/e[0], e[3]/e[0]] for e in pal] or [[86, 158, 92]]

    primary = pal[0]
    secondary = next((c for c in pal if dist(c, primary) > 70), None) \
        or shade(primary, -52 if luma(primary) > 128 else 58)
    accent = next((c for c in pal if dist(c, primary) > 70 and dist(c, secondary) > 60), None) \
        or shade(secondary, -40 if luma(secondary) > 128 else 46)

    low_colour = saturation(primary) < 0.18

    crop = im.crop((cx0, cy0, cx1 + 1, cy1 + 1))
    # measure the silhouette now, while the crop still holds the real photo
    ink = S.occupancy(crop, bg, thresh, cover=0.10)          # silhouette: catch faint edges
    ink_strong = S.occupancy(crop, bg, thresh, cover=0.30)    # detail: only real strokes
    solid = S.smooth(S.largest_component(S.solidify(ink)))
    return dict(crop=crop, ink=ink, ink_strong=ink_strong, solid=solid,
                bg=bg, thresh=thresh,
                low_colour=low_colour,
                primary=[int(v) for v in primary],
                secondary=[int(v) for v in secondary],
                accent=[int(v) for v in accent])


def finalise_palette(a, seed):
    """Pick the final colours, then knock the paper out of the crop.

    A pencil drawing has no colour of its own, so we give it a vivid palette
    derived from its name and keep the pencil lines on top - the art still
    shows, it just is not grey.
    """
    if a["low_colour"]:
        p, s, ac = palette_from_name(seed)
        a["primary"] = [int(v) for v in p]
        a["secondary"] = [int(v) for v in s]
        a["accent"] = [int(v) for v in ac]

    crop = a["crop"].convert("RGB")
    cp = crop.load()
    bg, thresh = a["bg"], a["thresh"]
    prim = tuple(a["primary"])
    ink = tuple(int(v) for v in shade(a["primary"], -95))
    for y in range(crop.height):
        for x in range(crop.width):
            c = cp[x, y]
            if dist(c, bg) <= thresh:
                cp[x, y] = prim                     # paper -> body colour
            elif a["low_colour"] and luma(c) < 110:
                cp[x, y] = ink                      # pencil line -> dark tint
            elif a["low_colour"]:
                cp[x, y] = prim
    a["crop"] = crop
    return a


def ink_preserving_resize(src, tw, th, ink_rgb=None, body_rgb=None, coverage=0.16):
    """Downscale line art to skin resolution.

    Averaging erases pencil lines; taking the darkest pixel turns everything
    black once lines are dense. Instead a cell becomes ink only when enough of
    it is actually dark, which yields a clean two-tone silhouette that still
    reads at 12x16 - the way a real Minecraft skin is drawn.
    """
    src = src.convert("RGB")
    # paper grain reads as ink at this scale; a median pass removes the speckle
    # while leaving pencil strokes intact
    if min(src.size) >= 5:
        src = src.filter(ImageFilter.MedianFilter(3))
    sp = src.load()
    out = Image.new("RGB", (tw, th))
    op = out.load()

    # ink threshold from the crop's own tone range
    vals = [luma(sp[x, y]) for y in range(0, src.height, 2) for x in range(0, src.width, 2)]
    vals.sort()
    lo = vals[int(len(vals) * 0.06)]
    hi = vals[int(len(vals) * 0.94)]
    cut = lo + (hi - lo) * 0.45

    for ty in range(th):
        for tx in range(tw):
            x0 = int(tx * src.width / tw); x1 = max(x0 + 1, int((tx + 1) * src.width / tw))
            y0 = int(ty * src.height / th); y1 = max(y0 + 1, int((ty + 1) * src.height / th))
            dark = tot = 0
            acc = [0, 0, 0]
            for yy in range(y0, min(y1, src.height)):
                for xx in range(x0, min(x1, src.width)):
                    c = sp[xx, yy]
                    tot += 1
                    if luma(c) < cut:
                        dark += 1
                        acc[0] += c[0]; acc[1] += c[1]; acc[2] += c[2]
            if tot and dark / tot >= coverage:
                op[tx, ty] = tuple(ink_rgb) if ink_rgb else tuple(v // dark for v in acc)
            else:
                op[tx, ty] = tuple(body_rgb) if body_rgb else (255, 255, 255)

    # drop lone ink pixels: at this scale they are grain, not drawing
    if ink_rgb and body_rgb:
        ink_t, body_t = tuple(ink_rgb), tuple(body_rgb)
        keep = [[op[x, y] == ink_t for y in range(th)] for x in range(tw)]
        for ty in range(th):
            for tx in range(tw):
                if not keep[tx][ty]:
                    continue
                n = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = tx + dx, ty + dy
                        if 0 <= nx < tw and 0 <= ny < th and keep[nx][ny]:
                            n += 1
                if n < 1:
                    op[tx, ty] = body_t
    return out


def build_texture(a):
    img = Image.new("RGBA", (TEX, TEX), tuple(a["primary"]) + (255,))
    limb = tuple(int(v) for v in shade(a["secondary"], -18)) + (255,)
    limb_dark = tuple(int(v) for v in shade(a["secondary"], -60)) + (255,)
    top = tuple(a["accent"]) + (255,)
    side = tuple(int(v) for v in shade(a["primary"], -26)) + (255,)
    back = tuple(int(v) for v in shade(a["primary"], -12)) + (255,)

    for name, origin, size, uv, role in BOXES:
        w, h, d = size
        f = face_rects(uv[0], uv[1], w, h, d)
        if role == "body":
            for k in ("up", "down", "west", "east", "south"):
                x, y, fw, fh = f[k]
                img.paste(back if k == "south" else side, (x, y, x + fw, y + fh))
            # The child's drawing IS the face - do not paint eyes over it.
            x, y, fw, fh = f["north"]
            ink = [int(v) for v in shade(a["primary"], -105)]
            art = ink_preserving_resize(a["crop"], fw, fh, ink_rgb=ink, body_rgb=a["primary"])
            img.paste(art.convert("RGBA"), (x, y))
        else:
            col = top if role == "top" else limb
            for k in ("up", "down", "west", "north", "east", "south"):
                x, y, fw, fh = f[k]
                img.paste(col, (x, y, x + fw, y + fh))
            nx, ny, _, nh = f["north"]
            img.paste(limb_dark, (nx, ny, nx + 1, ny + nh))

    # force full opacity
    px = img.load()
    for y in range(TEX):
        for x in range(TEX):
            r, g, b, _ = px[x, y]
            px[x, y] = (r, g, b, 255)
    return img


def build_item_icon(a):
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = img.load()
    body = tuple(a["primary"]) + (255,)
    edge = tuple(int(v) for v in shade(a["primary"], -70)) + (255,)
    glow = tuple(int(v) for v in mix(a["accent"], [255, 255, 255], 0.45)) + (255,)
    rows = [(5,10),(3,12),(2,13),(2,13),(2,13),(2,13),(2,13),(3,12),(3,12),(4,11),(5,10),(6,9)]
    for i, (x0, x1) in enumerate(rows):
        y = i + 2
        for x in range(x0, x1 + 1):
            d[x, y] = body
        d[x0, y] = edge
        d[x1, y] = edge
    for x in range(5, 7):
        for y in range(4, 6):
            d[x, y] = glow
    for x in range(7, 9):
        for y in range(9, 11):
            d[x, y] = tuple(a["accent"]) + (255,)
    return img


def build_pack_icon(a):
    S = 128
    img = Image.new("RGBA", (S, S), tuple(int(v) for v in mix(a["primary"], [255, 255, 255], 0.12)) + (255,))
    s = min(a["crop"].width, a["crop"].height)
    sx = (a["crop"].width - s) // 2
    sy = (a["crop"].height - s) // 2
    sq = a["crop"].crop((sx, sy, sx + s, sy + s)).resize((S - 12, S - 12), Image.LANCZOS)
    img.paste(sq.convert("RGBA"), (6, 6))
    return img


def build_pack(out_dir, cid, display, trait, version, analysis):
    t = TRAITS.get(trait, TRAITS["friendly"])

    # the drawing's own outline becomes the model's shape
    ink = analysis["ink"]
    solid = analysis["solid"]
    cubes = S.cubes_from(solid)
    if not cubes:
        raise SystemExit("no drawing found in that crop")
    geo = S.build_geometry(cid, cubes, TEX, TEX)
    height_units = S.model_height_units(cubes)

    # aim for about half a player, adjusted by personality
    target_blocks = 0.95 + t["scale_adj"]
    scale = round(max(0.2, min(2.0, target_blocks * 16.0 / height_units)), 3)
    width_cells = max(c["c1"] for c in cubes) - min(c["c0"] for c in cubes) + 1
    entity = f"junkbunch:{cid}"
    item = f"junkbunch:{cid}_charm"

    bp_h, bp_m = uuid_from(cid + "|bp|header"), uuid_from(cid + "|bp|module")
    rp_h, rp_m = uuid_from(cid + "|rp|header"), uuid_from(cid + "|rp|module")

    BP = os.path.join(out_dir, "JunkBunch_BP")
    RP = os.path.join(out_dir, "JunkBunch_RP")
    for sub in ["entities", "items", "recipes"]:
        os.makedirs(os.path.join(BP, sub), exist_ok=True)
    for sub in ["entity", "models/entity", "render_controllers", "animation_controllers",
                "animations", "texts", "textures/entity/junkbunch", "textures/items"]:
        os.makedirs(os.path.join(RP, sub), exist_ok=True)

    def w(path, obj):
        with open(path, "w") as fh:
            json.dump(obj, fh, indent=2)
            fh.write("\n")

    w(os.path.join(BP, "manifest.json"), {
        "format_version": 2,
        "header": {"name": f"{display} (Junk Bunch)", "description": f"{display} - behaviour",
                   "uuid": bp_h, "version": version, "min_engine_version": [1, 20, 50]},
        "modules": [{"type": "data", "description": f"{display} entity, item and recipe",
                     "uuid": bp_m, "version": version}],
        "dependencies": [{"uuid": rp_h, "version": version}],
    })
    w(os.path.join(RP, "manifest.json"), {
        "format_version": 2,
        "header": {"name": f"{display} (Junk Bunch)", "description": f"{display} - looks",
                   "uuid": rp_h, "version": version, "min_engine_version": [1, 20, 50]},
        "modules": [{"type": "resources", "description": f"{display} model and texture",
                     "uuid": rp_m, "version": version}],
    })

    w(os.path.join(BP, "entities", f"{cid}.json"), {
        "format_version": "1.20.50",
        "minecraft:entity": {
            "description": {"identifier": entity, "is_spawnable": True,
                            "is_summonable": True, "is_experimental": False},
            "component_groups": {
                "junkbunch:wild": {
                    "minecraft:tameable": {
                        "probability": 1.0, "tame_items": [item],
                        "tame_event": {"event": "junkbunch:on_tamed", "target": "self"},
                    }
                },
                "junkbunch:tamed": {
                    "minecraft:is_tamed": {},
                    "minecraft:behavior.follow_owner": {
                        "priority": 3, "speed_multiplier": 1.1,
                        "start_distance": 4.0, "stop_distance": 1.5},
                    "minecraft:persistent": {},
                },
            },
            "components": {
                "minecraft:type_family": {"family": [cid, "junkbunch", "mob"]},
                "minecraft:health": {"value": 12, "max": 12},
                "minecraft:scale": {"value": scale},
                "minecraft:collision_box": {
                    "width": round(max(0.4, min(1.6, width_cells * S.CELL * scale / 16)), 2),
                    "height": round(max(0.4, height_units * scale / 16), 2)},
                "minecraft:breathable": {"total_supply": 15, "suffocate_time": 0},
                "minecraft:physics": {"has_gravity": True, "has_collision": True},
                "minecraft:movement": {"value": t["speed"]},
                "minecraft:movement.basic": {},
                "minecraft:navigation.walk": {"can_path_over_water": True, "avoid_water": True,
                                              "avoid_damage_blocks": True},
                "minecraft:jump.static": {},
                "minecraft:can_climb": {},
                "minecraft:nameable": {},
                "minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True},
                "minecraft:leashable": {"soft_distance": 4.0, "hard_distance": 6.0, "max_distance": 10.0},
                "minecraft:damage_sensor": {"triggers": [{"cause": "fall", "deals_damage": False}]},
                "minecraft:behavior.float": {"priority": 0},
                "minecraft:behavior.panic": {"priority": 1, "speed_multiplier": 1.25},
                "minecraft:behavior.look_at_player": {"priority": 6, "look_distance": 8.0,
                                                      "probability": t["look"]},
                "minecraft:behavior.random_stroll": {"priority": 7, "speed_multiplier": t["stroll"]},
                "minecraft:behavior.random_look_around": {"priority": 8},
            },
            "events": {
                "minecraft:entity_spawned": {"add": {"component_groups": ["junkbunch:wild"]}},
                "junkbunch:on_tamed": {"remove": {"component_groups": ["junkbunch:wild"]},
                                       "add": {"component_groups": ["junkbunch:tamed"]}},
            },
        },
    })

    w(os.path.join(BP, "items", f"{cid}_charm.json"), {
        "format_version": "1.20.50",
        "minecraft:item": {
            "description": {"identifier": item, "menu_category": {"category": "equipment"}},
            "components": {
                "minecraft:max_stack_size": 1,
                "minecraft:icon": {"texture": f"{cid}_charm"},
                "minecraft:hand_equipped": True,
                "minecraft:allow_off_hand": True,
                "minecraft:entity_placer": {"entity": entity},
            },
        },
    })

    w(os.path.join(BP, "recipes", f"{cid}_charm.json"), {
        "format_version": "1.20.50",
        "minecraft:recipe_shaped": {
            "description": {"identifier": item},
            "tags": ["crafting_table"],
            "pattern": [" A ", "ABA", " A "],
            "key": {"A": {"item": "minecraft:stick"}, "B": {"item": "minecraft:emerald"}},
            "unlock": [{"item": "minecraft:stick"}],
            "result": {"item": item, "count": 1},
        },
    })

    w(os.path.join(RP, "entity", f"{cid}.json"), {
        "format_version": "1.10.0",
        "minecraft:client_entity": {
            "description": {
                "identifier": entity,
                "materials": {"default": "entity_alphatest"},
                "geometry": {"default": f"geometry.{cid}.main"},
                "textures": {"default": f"textures/entity/junkbunch/{cid}"},
                "animations": {
                    "idle": f"animation.{cid}.idle",
                    "walk": f"animation.{cid}.walk",
                    "move_controller": f"controller.animation.{cid}.move",
                },
                "scripts": {"animate": ["move_controller"]},
                "render_controllers": [f"controller.render.{cid}"],
                "spawn_egg": {"base_color": to_hex(analysis["primary"]),
                              "overlay_color": to_hex(analysis["accent"])},
            }
        },
    })

    w(os.path.join(RP, "models/entity", f"{cid}.geo.json"), geo)

    w(os.path.join(RP, "render_controllers", f"{cid}.json"), {
        "format_version": "1.10.0",
        "render_controllers": {
            f"controller.render.{cid}": {
                "geometry": "Geometry.default",
                "materials": [{"*": "Material.default"}],
                "textures": ["Texture.default"],
            }
        },
    })

    w(os.path.join(RP, "animation_controllers", f"{cid}.json"), {
        "format_version": "1.10.0",
        "animation_controllers": {
            f"controller.animation.{cid}.move": {
                "initial_state": "idle",
                "states": {
                    "idle": {"animations": ["idle"],
                             "transitions": [{"walk": "query.modified_move_speed > 0.1"}]},
                    "walk": {"animations": ["walk"],
                             "transitions": [{"idle": "query.modified_move_speed <= 0.1"}]},
                },
            }
        },
    })

    bob = 0.9 if trait == "bouncy" else 0.35
    w(os.path.join(RP, "animations", f"{cid}.animation.json"), {
        "format_version": "1.8.0",
        "animations": {
            f"animation.{cid}.idle": {
                "loop": True, "animation_length": 3.0,
                "bones": {"body": {
                    "position": [0, f"math.sin(query.anim_time * 120) * {bob}", 0],
                    "rotation": [0, 0, "math.sin(query.anim_time * 90) * 2"]}},
            },
            f"animation.{cid}.walk": {
                "loop": True, "animation_length": 0.8,
                "bones": {"body": {
                    "position": [0, f"math.abs(math.sin(query.anim_time * 720)) * {round(bob*1.6,3)}", 0],
                    "rotation": [0, 0, "math.sin(query.anim_time * 720) * 6"]}},
            },
        },
    })

    w(os.path.join(RP, "textures", "item_texture.json"), {
        "resource_pack_name": "JunkBunch",
        "texture_name": "atlas.items",
        "texture_data": {f"{cid}_charm": {"textures": f"textures/items/{cid}_charm"}},
    })

    w(os.path.join(RP, "texts", "languages.json"), ["en_US"])
    with open(os.path.join(RP, "texts", "en_US.lang"), "w") as fh:
        fh.write(f"item.{item}={display}'s Charm\n"
                 f"entity.{entity}.name={display}\n"
                 f"item.spawn_egg.entity.{entity}.name=Spawn {display}\n"
                 f"pack.name={display} (Junk Bunch)\n"
                 f"pack.description={display} - a Junk Bunch character\n")

    S.build_texture(analysis["crop"], analysis["bg"], analysis["thresh"],
                    analysis["ink_strong"], solid,
                    analysis["primary"], shade(analysis["primary"], -105),
                    analysis["accent"], tex=TEX
                    ).save(os.path.join(RP, "textures/entity/junkbunch", f"{cid}.png"))
    build_item_icon(analysis).save(os.path.join(RP, "textures/items", f"{cid}_charm.png"))
    icon = build_pack_icon(analysis)
    icon.save(os.path.join(RP, "pack_icon.png"))
    icon.save(os.path.join(BP, "pack_icon.png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("drawing")
    ap.add_argument("name")
    ap.add_argument("--trait", default="friendly", choices=sorted(TRAITS))
    ap.add_argument("--out", default=None)
    ap.add_argument("--crop", default=None,
                    help="x,y,w,h as fractions of the photo (e.g. 0.30,0.40,0.45,0.22) "
                         "to pick one character off a page holding several")
    ap.add_argument("--rotate", type=int, default=0, choices=[0, 90, 180, 270],
                    help="rotate the photo clockwise before cropping")
    args = ap.parse_args()

    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cid = slug(args.name)
    display = args.name.strip().title()
    work = args.out or os.path.join(repo, "build", cid)
    os.makedirs(work, exist_ok=True)

    print(f"analysing {args.drawing} ...")
    cf = [float(v) for v in args.crop.split(",")] if args.crop else None
    a = finalise_palette(analyse(args.drawing, cf, args.rotate), cid)
    note = " (from name - drawing has no colour)" if a["low_colour"] else " (from the drawing)"
    print(f"  colours: {to_hex(a['primary'])} {to_hex(a['secondary'])} {to_hex(a['accent'])}{note}")

    build_pack(work, cid, display, args.trait, [1, 0, 1], a)
    print(f"  pack written to {os.path.relpath(work, repo)}")

    out = os.path.join(repo, f"{display.replace(' ', '')}.mcaddon")
    if os.path.exists(out):
        os.remove(out)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for pack in ("JunkBunch_BP", "JunkBunch_RP"):
            root = os.path.join(work, pack)
            for dp, _dn, fn in os.walk(root):
                for f in sorted(fn):
                    full = os.path.join(dp, f)
                    z.write(full, os.path.relpath(full, work))
    print(f"  built {os.path.relpath(out, repo)}")
    return work


if __name__ == "__main__":
    main()
