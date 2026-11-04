"""Course Craft enemy geometry source, v2 (model units: 16 = 1 block; front faces north / -Z).

Cube tuple: (origin xyz, size xyz, colour, optional north-face paint, optional material).
Paint rects are face texels (x from the left as seen from the front, y from the top).
Material: "stone" | "plant" | "metal" | "cake" | "membrane" | "plain" — drives texture detail.
v1 failed the creator gate (flat box stacks); v2 adds rounded stepped volume, big eyes,
chunky proportions and shaded materials.
"""

WHITE, BLACK, HI = (250, 250, 246), (22, 20, 28), (255, 255, 255)
STONE, STONE_D, MOSS = (150, 142, 132), (104, 98, 92), (96, 160, 72)
CACTUS, CACTUS_D, SPINE, PINK, PINK_D, YEL = (78, 176, 88), (50, 124, 62), (246, 236, 200), (246, 120, 176), (210, 80, 140), (252, 214, 64)
TEAL, TEAL_D, STEEL, STEEL_D, RED = (54, 182, 186), (32, 120, 128), (200, 206, 214), (128, 134, 146), (236, 70, 60)
CAKE, CAKE_L, BUTTER, SYRUP, WING, WING_D = (212, 146, 66), (234, 178, 98), (255, 234, 120), (150, 70, 30), (132, 82, 178), (92, 54, 132)


def band(cx, y, cz, w, h, d, colour, mat):
    """A rounded slab: two crossed cubes (full w x inset d, inset w x full d) = octagonal footprint."""
    inset = max(1, round(min(w, d) * 0.2))
    x0, z0 = cx - w // 2, cz - d // 2
    return [
        ([x0, y, z0 + inset], [w, h, d - 2 * inset], colour, None, mat),
        ([x0 + inset, y, z0], [w - 2 * inset, h, d], colour, None, mat),
    ]


def blob(cx, y, cz, w, d, profile, colour, mat):
    """Stack of rounded bands: profile = [(height, scale), ...] bottom to top -> ellipsoid-ish volume."""
    out, yy = [], y
    for h, s in profile:
        bw, bd = max(2, round(w * s / 2) * 2), max(2, round(d * s / 2) * 2)
        out += band(cx, yy, cz, bw, h, bd, colour, mat)
        yy += h
    return out


def eye(x, y, z, w=4, h=5, look=0):
    """Protruding eye: white with dark pupil (offset by `look`) and a highlight."""
    px = max(0, min(w - 2, (w - 2) // 2 + look))
    return ([x, y, z], [w, h, 1], WHITE, [(px, h - 3, 2, 3, BLACK), (px, h - 3, 1, 1, HI)], "plain")


ROUND = [(2, 0.70), (2, 0.92), (3, 1.0), (2, 0.92), (1, 0.70)]

ENEMIES = {
    "trundle": {
        "name": "Trundle", "role": "walker", "stompable": True,
        "concept": "Round stone beetle: domed mossy shell, big determined eyes under a heavy brow, four stubby feet.",
        "collision": [0.85, 0.7],
        "bones": [
            {"name": "body", "pivot": [0, 0, 0], "cubes":
                blob(0, 2, 1, 14, 14, ROUND, STONE, "stone")
                + [([-3, 12, -1], [6, 1, 5], MOSS, None, "plant"), ([-2, 12, 4], [3, 1, 2], MOSS, None, "plant")]},
            {"name": "face", "pivot": [0, 6, -6], "cubes": [
                eye(-5, 5, -7, 4, 5, 1), eye(1, 5, -7, 4, 5, -1),
                ([-6, 10, -7], [5, 1, 2], STONE_D, None, "stone"), ([1, 10, -7], [5, 1, 2], STONE_D, None, "stone"),
                ([-1, 4, -7], [2, 1, 1], STONE_D, None, "stone"),
            ]},
            {"name": "legs", "pivot": [0, 2, 0], "cubes": [
                ([-6, 0, -5], [4, 3, 4], STONE_D, None, "stone"), ([2, 0, -5], [4, 3, 4], STONE_D, None, "stone"),
                ([-6, 0, 4], [4, 3, 4], STONE_D, None, "stone"), ([2, 0, 4], [4, 3, 4], STONE_D, None, "stone"),
            ]},
        ],
    },
    "bristle": {
        "name": "Bristle", "role": "spiky_walker", "stompable": False,
        "concept": "Round ribbed cactus with a big pink blossom; spines all over so it can't be stomped; wide nervous eyes.",
        "collision": [0.8, 0.95],
        "bones": [
            {"name": "body", "pivot": [0, 0, 0], "cubes":
                blob(0, 1, 0, 12, 12, [(2, 0.66), (2, 0.9), (4, 1.0), (2, 0.9), (2, 0.66)], CACTUS, "plant")
                + [([-3, 0, -2], [2, 1, 4], CACTUS_D, None, "plant"), ([1, 0, -2], [2, 1, 4], CACTUS_D, None, "plant")]},
            {"name": "face", "pivot": [0, 6, -6], "cubes": [
                eye(-5, 5, -7, 4, 4, 1), eye(1, 5, -7, 4, 4, -1),
                ([-1, 3, -7], [2, 1, 1], PINK_D, None, "plain"),
            ]},
            {"name": "spines", "pivot": [0, 6, 0], "cubes": [
                ([-8, 6, -1], [2, 1, 1], SPINE, None, "plain"), ([6, 6, -1], [2, 1, 1], SPINE, None, "plain"),
                ([-7, 9, 2], [2, 1, 1], SPINE, None, "plain"), ([5, 9, 2], [2, 1, 1], SPINE, None, "plain"),
                ([-7, 3, 3], [2, 1, 1], SPINE, None, "plain"), ([5, 3, -3], [2, 1, 1], SPINE, None, "plain"),
                ([-4, 10, -7], [1, 1, 2], SPINE, None, "plain"), ([3, 10, -7], [1, 1, 2], SPINE, None, "plain"),
                ([-4, 2, -6], [1, 1, 2], SPINE, None, "plain"), ([3, 2, -6], [1, 1, 2], SPINE, None, "plain"),
                ([-2, 6, 6], [1, 1, 2], SPINE, None, "plain"), ([2, 9, 5], [1, 1, 2], SPINE, None, "plain"),
                ([-4, 12, 3], [1, 2, 1], SPINE, None, "plain"), ([4, 12, -4], [1, 2, 1], SPINE, None, "plain"),
            ]},
            {"name": "flower", "pivot": [0, 13, 0], "cubes": [
                ([-4, 13, -1], [8, 2, 2], PINK, None, "plant"), ([-1, 13, -4], [2, 2, 8], PINK, None, "plant"),
                ([-3, 13, -3], [6, 1, 6], PINK_D, None, "plant"),
                ([-1, 15, -1], [2, 1, 2], YEL, None, "plain"),
            ]},
        ],
    },
    "boing": {
        "name": "Boing", "role": "hopper", "stompable": True,
        "concept": "Round tin robot on a chunky coil spring: one big camera eye, riveted belly band, antenna bulb.",
        "collision": [0.7, 1.2],
        "bones": [
            {"name": "spring", "pivot": [0, 0, 0], "cubes":
                band(0, 0, 0, 10, 1, 10, STEEL_D, "metal")
                + band(0, 1, 0, 6, 1, 6, STEEL, "metal") + band(0, 2, 0, 4, 1, 4, STEEL_D, "metal")
                + band(0, 3, 0, 6, 1, 6, STEEL, "metal") + band(0, 4, 0, 4, 1, 4, STEEL_D, "metal")
                + band(0, 5, 0, 6, 1, 6, STEEL, "metal")},
            {"name": "can", "pivot": [0, 6, 0], "cubes":
                blob(0, 6, 0, 12, 12, [(1, 0.84), (8, 1.0), (1, 0.84)], TEAL, "metal")
                + band(0, 8, 0, 14, 1, 14, TEAL_D, "metal")
                + [([-3, 11, -7], [6, 5, 1], STEEL_D, [(1, 1, 4, 3, BLACK), (2, 2, 2, 1, RED), (2, 1, 1, 1, HI)], "metal"),
                   ([-8, 10, -1], [2, 3, 2], STEEL_D, None, "metal"), ([6, 10, -1], [2, 3, 2], STEEL_D, None, "metal"),
                   ([0, 16, 0], [1, 3, 1], STEEL_D, None, "metal"), ([-1, 19, -1], [2, 2, 2], RED, None, "plain")]},
        ],
    },
    "flapjack": {
        "name": "Flapjack", "role": "flyer", "stompable": True,
        "concept": "Flying stack of thick round pancakes with butter and a syrup drip, sleepy eyes, scalloped bat wings.",
        "collision": [0.8, 0.7],
        "bones": [
            {"name": "body", "pivot": [0, 4, 0], "cubes":
                band(0, 3, 0, 12, 3, 12, CAKE, "cake") + band(0, 6, 0, 12, 3, 12, CAKE_L, "cake")
                + [([-2, 9, -2], [4, 1, 4], BUTTER, None, "plain"), ([-6, 4, -2], [1, 4, 2], SYRUP, None, "plain"),
                   ([-6, 2, -1], [1, 2, 1], SYRUP, None, "plain"),
                   ([-4, 3, -7], [8, 3, 1], CAKE, [(0, 0, 3, 1, BLACK), (5, 0, 3, 1, BLACK), (3, 2, 2, 1, SYRUP)], "cake")]},
            {"name": "wing_left", "pivot": [-6, 6, 0], "cubes": [
                ([-14, 6, -3], [8, 1, 6], WING, None, "membrane"), ([-17, 6, -2], [3, 1, 4], WING, None, "membrane"),
                ([-12, 5, -3], [2, 1, 1], WING_D, None, "membrane"), ([-16, 5, -2], [2, 1, 1], WING_D, None, "membrane"),
                ([-14, 7, -1], [8, 1, 1], WING_D, None, "membrane"),
            ]},
            {"name": "wing_right", "pivot": [6, 6, 0], "cubes": [
                ([6, 6, -3], [8, 1, 6], WING, None, "membrane"), ([14, 6, -2], [3, 1, 4], WING, None, "membrane"),
                ([10, 5, -3], [2, 1, 1], WING_D, None, "membrane"), ([14, 5, -2], [2, 1, 1], WING_D, None, "membrane"),
                ([6, 7, -1], [8, 1, 1], WING_D, None, "membrane"),
            ]},
        ],
    },
}
