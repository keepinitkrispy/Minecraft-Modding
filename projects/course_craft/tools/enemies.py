"""Course Craft enemy geometry source (model units: 16 = 1 block; front faces north / -Z).

Each cube: (origin xyz, size xyz, colour, optional north-face paint).
Integer origins/sizes only so box-UV maps cleanly. Paint rects are in face texels
(x from the face's left as seen from the front, y from its top).
"""

STONE, STONE_D, STONE_L = (128, 124, 120), (92, 88, 86), (160, 156, 150)
WHITE, BLACK, PINK, YEL = (245, 245, 240), (25, 22, 30), (240, 110, 170), (250, 215, 60)
CACTUS, CACTUS_D, SPIKE = (70, 160, 80), (45, 115, 55), (235, 225, 190)
TEAL, TEAL_D, STEEL, STEEL_D = (60, 170, 170), (35, 110, 115), (190, 195, 200), (120, 125, 135)
CAKE, CAKE_L, BUTTER, WING = (205, 140, 60), (225, 170, 90), (255, 230, 120), (120, 70, 150)

ENEMIES = {
    "trundle": {
        "name": "Trundle", "role": "walker", "stompable": True,
        "concept": "Stone pill-bug: arched three-segment shell, one big eye, six stubby legs.",
        "collision": [0.8, 0.6],
        "bones": [
            {"name": "body", "pivot": [0, 0, 0], "cubes": [
                ([-6, 2, -6], [12, 7, 4], STONE),
                ([-7, 2, -2], [14, 8, 5], STONE_L),
                ([-6, 2, 3], [12, 7, 4], STONE),
                ([-5, 9, -6], [10, 1, 4], STONE_D),
                ([-6, 10, -2], [12, 1, 5], STONE),
                ([-5, 9, 3], [10, 1, 4], STONE_D),
            ]},
            {"name": "head", "pivot": [0, 4, -6], "cubes": [
                ([-4, 2, -9], [8, 6, 3], STONE_D, [(2, 1, 4, 4, WHITE), (3, 2, 2, 2, BLACK)]),
                ([-3, 7, -10], [1, 1, 3], STONE_D),
                ([2, 7, -10], [1, 1, 3], STONE_D),
            ]},
            {"name": "legs", "pivot": [0, 2, 0], "cubes": [
                ([-8, 0, -5], [2, 2, 2], STONE_D), ([6, 0, -5], [2, 2, 2], STONE_D),
                ([-8, 0, 0], [2, 2, 2], STONE_D), ([6, 0, 0], [2, 2, 2], STONE_D),
                ([-8, 0, 4], [2, 2, 2], STONE_D), ([6, 0, 4], [2, 2, 2], STONE_D),
            ]},
        ],
    },
    "bristle": {
        "name": "Bristle", "role": "spiky_walker", "stompable": False,
        "concept": "Round cactus ball with a pink flower on top; spines everywhere so it can't be stomped.",
        "collision": [0.75, 0.85],
        "bones": [
            {"name": "body", "pivot": [0, 0, 0], "cubes": [
                ([-5, 1, -5], [10, 10, 10], CACTUS),
                ([-4, 11, -4], [8, 1, 8], CACTUS_D),
                ([-6, 2, -4], [1, 8, 8], CACTUS_D), ([5, 2, -4], [1, 8, 8], CACTUS_D),
                # Front slab is the visible face (it sits in front of the core): paint the face here.
                ([-4, 2, -6], [8, 8, 1], CACTUS_D, [(1, 2, 2, 2, WHITE), (2, 3, 1, 1, BLACK), (5, 2, 2, 2, WHITE), (5, 3, 1, 1, BLACK), (3, 5, 2, 1, PINK)]),
                ([-4, 2, 5], [8, 8, 1], CACTUS_D),
                ([-4, 0, -2], [3, 1, 4], CACTUS_D), ([1, 0, -2], [3, 1, 4], CACTUS_D),
            ]},
            {"name": "spines", "pivot": [0, 6, 0], "cubes": [
                ([-8, 5, -1], [2, 1, 1], SPIKE), ([6, 5, -1], [2, 1, 1], SPIKE),
                ([-8, 8, 2], [2, 1, 1], SPIKE), ([6, 8, 2], [2, 1, 1], SPIKE),
                ([-6, 10, -7], [1, 1, 2], SPIKE), ([5, 2, -7], [1, 1, 2], SPIKE),
                ([-2, 5, 6], [1, 1, 2], SPIKE), ([2, 8, 6], [1, 1, 2], SPIKE),
                ([-3, 12, 2], [1, 2, 1], SPIKE), ([3, 12, -3], [1, 2, 1], SPIKE),
            ]},
            {"name": "flower", "pivot": [0, 12, 0], "cubes": [
                ([-2, 12, -2], [4, 2, 4], PINK),
                ([-1, 14, -1], [2, 1, 2], YEL),
            ]},
        ],
    },
    "boing": {
        "name": "Boing", "role": "hopper", "stompable": True,
        "concept": "Tin-can robot riding a coil spring; one visor eye; hops in place and forward.",
        "collision": [0.6, 1.1],
        "bones": [
            {"name": "spring", "pivot": [0, 0, 0], "cubes": [
                ([-4, 0, -4], [8, 1, 8], STEEL_D),
                ([-3, 1, -3], [6, 1, 6], STEEL), ([-2, 2, -2], [4, 1, 4], STEEL_D),
                ([-3, 3, -3], [6, 1, 6], STEEL), ([-2, 4, -2], [4, 1, 4], STEEL_D),
                ([-3, 5, -3], [6, 1, 6], STEEL),
            ]},
            {"name": "can", "pivot": [0, 6, 0], "cubes": [
                ([-4, 6, -4], [8, 9, 8], TEAL, [(0, 2, 8, 3, BLACK), (3, 3, 2, 1, YEL)]),
                ([-5, 15, -5], [10, 1, 10], TEAL_D),
                ([-1, 16, -1], [2, 2, 2], STEEL),
                ([-6, 9, -1], [2, 3, 2], STEEL_D), ([4, 9, -1], [2, 3, 2], STEEL_D),
            ]},
        ],
    },
    "flapjack": {
        "name": "Flapjack", "role": "flyer", "stompable": True,
        "concept": "Flying stack of two pancakes with a butter pat, sleepy eyes and purple wings; bobs in the air.",
        "collision": [0.7, 0.6],
        "bones": [
            {"name": "body", "pivot": [0, 4, 0], "cubes": [
                ([-5, 4, -5], [10, 2, 10], CAKE, [(2, 0, 2, 1, BLACK), (6, 0, 2, 1, BLACK)]),
                ([-5, 6, -5], [10, 2, 10], CAKE_L),
                ([-2, 8, -2], [4, 1, 4], BUTTER),
                ([-6, 3, -1], [1, 2, 2], CAKE),
            ]},
            {"name": "wing_left", "pivot": [-5, 5, 0], "cubes": [
                ([-13, 5, -3], [8, 1, 6], WING), ([-15, 5, -2], [2, 1, 4], WING),
            ]},
            {"name": "wing_right", "pivot": [5, 5, 0], "cubes": [
                ([5, 5, -3], [8, 1, 6], WING), ([13, 5, -2], [2, 1, 4], WING),
            ]},
        ],
    },
}
