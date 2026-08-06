#!/usr/bin/env python3
"""
Baloney, built to the reference sheet: a pink balloon head with a big cartoon
face, a knot underneath, thin string arms ending in square hands, and string
legs with small feet. One block tall - half a player.

Everything is authored in Bedrock model units where 16 units = 1 block, so the
model is exactly 16 units from feet to the top of the balloon.
"""

from PIL import Image

TEX = 64
DEPTH_BALLOON = 9
DEPTH_STRING = 1

# --- palette taken from the reference render ---------------------------
PINK        = (226, 122, 128)
PINK_LIT    = (242, 160, 164)
PINK_SHADE  = (196,  96, 104)
STRING      = (206, 104, 112)
INK         = ( 26,  22,  24)
WHITE       = (255, 255, 255)

# balloon: 10 rows tall, 11 wide at the middle, corners rounded off
BALLOON_ROWS = [5, 9, 11, 11, 11, 11, 11, 11, 9, 5]
BALLOON_W = max(BALLOON_ROWS)
BALLOON_H = len(BALLOON_ROWS)

# texture regions
UV_FACE   = (0, 0)                     # BALLOON_W x BALLOON_H, the balloon front
UV_SIDE   = (16, 0)
UV_LIT    = (18, 0)
UV_STRING = (20, 0)
UV_SHADE  = (22, 0)
UV_PINK_HAND = (24, 0)


def _swatch(uv):
    return {"uv": list(uv), "uv_size": [1, 1]}


def build_geometry(cid="baloney"):
    """Balloon rows + knot + arms + legs, feet sitting on y=0."""
    cubes = []

    leg_h = 5          # string legs
    knot_y = leg_h     # knot sits on top of the legs
    bal_y0 = knot_y + 1

    # ---- balloon -------------------------------------------------------
    for i, w in enumerate(BALLOON_ROWS):
        r = BALLOON_H - 1 - i               # texture row 0 is the top
        y = bal_y0 + i                      # model y grows upward
        x0 = -w / 2.0
        u = UV_FACE[0] + (BALLOON_W - w) // 2
        v = UV_FACE[1] + r
        depth = DEPTH_BALLOON if w >= BALLOON_W - 2 else DEPTH_BALLOON - 2
        cubes.append({
            "origin": [x0, y, -depth / 2.0],
            "size": [w, 1, depth],
            "uv": {
                "north": {"uv": [u, v], "uv_size": [w, 1]},
                "south": {"uv": [u, v], "uv_size": [w, 1]},
                "west": _swatch(UV_SIDE), "east": _swatch(UV_SIDE),
                "up": _swatch(UV_LIT), "down": _swatch(UV_SHADE),
            },
        })

    # ---- knot ----------------------------------------------------------
    cubes.append({
        "origin": [-1, knot_y, -1],
        "size": [2, 1, 2],
        "uv": {k: _swatch(UV_SHADE) for k in
               ("north", "south", "west", "east", "up", "down")},
    })

    def string(x, y, w, h, d=DEPTH_STRING, uv=UV_STRING):
        cubes.append({
            "origin": [x, y, -d / 2.0],
            "size": [w, h, d],
            "uv": {k: _swatch(uv) for k in
                   ("north", "south", "west", "east", "up", "down")},
        })

    # ---- legs: two strings with small feet -----------------------------
    string(-2.5, 0, 1, leg_h)
    string(1.5, 0, 1, leg_h)
    string(-3.5, 0, 3, 1)          # left foot
    string(0.5, 0, 3, 1)           # right foot

    # ---- arms: out from the balloon, curving down, square hands --------
    arm_y = bal_y0 + 1
    # left arm
    string(-BALLOON_W / 2.0 - 3, arm_y + 2, 3, 1)
    string(-BALLOON_W / 2.0 - 3, arm_y - 1, 1, 3)
    string(-BALLOON_W / 2.0 - 4, arm_y - 2, 2, 2, uv=UV_PINK_HAND)
    # right arm, raised like the reference
    string(BALLOON_W / 2.0, arm_y + 2, 3, 1)
    string(BALLOON_W / 2.0 + 2, arm_y + 2, 1, 3)
    string(BALLOON_W / 2.0 + 1, arm_y + 5, 2, 2, uv=UV_PINK_HAND)

    return {
        "format_version": "1.16.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": f"geometry.{cid}.main",
                "texture_width": TEX, "texture_height": TEX,
                "visible_bounds_width": 3, "visible_bounds_height": 3,
                "visible_bounds_offset": [0, 1, 0],
            },
            "bones": [
                {"name": "root", "pivot": [0, 0, 0], "children": ["body"]},
                {"name": "body", "pivot": [0, 0, 0], "cubes": cubes},
            ],
        }],
    }


def build_texture():
    """Balloon front with the cartoon face, plus flat swatches."""
    img = Image.new("RGBA", (TEX, TEX), PINK + (255,))
    p = img.load()

    W, H = BALLOON_W, BALLOON_H
    for y in range(H):
        for x in range(W):
            p[x, y] = PINK + (255,)

    # soft highlight down the upper left, like an inflated balloon
    for x, y in ((1, 1), (2, 1), (1, 2), (2, 2), (3, 1), (2, 3)):
        if x < W and y < H:
            p[x, y] = PINK_LIT + (255,)
    for x in range(W):
        if x < W:
            p[x, H - 1] = PINK_SHADE + (255,)

    # eyes: tall ovals with a white glint, as drawn on the sheet
    for ex in (2, 7):
        for dy in range(3):
            p[ex, 2 + dy] = INK + (255,)
            p[ex + 1, 2 + dy] = INK + (255,)
        p[ex, 2] = WHITE + (255,)

    # wide open smile: dark mouth, curling up at the corners, light lower lip
    for x in range(3, 8):
        p[x, 6] = INK + (255,)
    for x in range(2, 9):
        p[x, 7] = INK + (255,)
    p[2, 6] = INK + (255,)
    p[8, 6] = INK + (255,)
    p[1, 5] = INK + (255,)
    p[9, 5] = INK + (255,)
    for x in range(4, 7):
        p[x, 8] = WHITE + (255,)

    for uv, col in ((UV_SIDE, PINK), (UV_LIT, PINK_LIT), (UV_STRING, STRING),
                    (UV_SHADE, PINK_SHADE), (UV_PINK_HAND, PINK)):
        for dy in range(2):
            for dx in range(2):
                p[uv[0] + dx, uv[1] + dy] = col + (255,)

    for y in range(TEX):
        for x in range(TEX):
            r, g, b, _ = p[x, y]
            p[x, y] = (r, g, b, 255)
    return img


def build_item_icon():
    """The spawn balloon thumbnail."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = img.load()
    rows = [(6, 9), (5, 10), (4, 11), (4, 11), (4, 11), (4, 11), (5, 10), (6, 9), (7, 8)]
    for i, (a, b) in enumerate(rows):
        for x in range(a, b + 1):
            p[x, i + 1] = PINK + (255,)
    for x, y in ((5, 2), (6, 2), (5, 3)):
        p[x, y] = PINK_LIT + (255,)
    for ex in (6, 9):
        p[ex, 4] = INK + (255,)
    for x in range(6, 10):
        p[x, 6] = INK + (255,)
    p[7, 10] = PINK_SHADE + (255,)
    for i, y in enumerate(range(11, 15)):
        p[7 + (i % 2), y] = STRING + (255,)
    return img


def dims():
    return BALLOON_W, 16
