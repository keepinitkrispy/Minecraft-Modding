"""Single source of truth for Course Craft content and texture slots."""

NS = "cc"
BP = "CourseCraft_BP"
RP = "CourseCraft_RP"
MIN_ENGINE = [1, 21, 90]
SCRIPT_DEPS = [("@minecraft/server", "2.0.0"), ("@minecraft/server-ui", "2.0.0")]

# Stable UUIDs: never change these, or Bedrock treats it as a different pack.
UUIDS = {
    "bp_header": "6a1f3c2e-8b4d-4e7a-9c15-2d8e7f6a0b31",
    "bp_data": "c4e2a9d1-5f37-4b8c-a6e0-91d3b7f2c845",
    "bp_script": "0f8b6d24-3a9e-4c71-b5d2-7e4f1a6c9b03",
    "rp_header": "9d3e7b15-2c6a-4f84-8e1b-5a0c3d7f2e96",
    "rp_resources": "e7b1c0f4-6d29-4a53-9f8e-3c2b5d1a7e40",
}

# Block id -> lang name, textures per face ("*" = all faces), extras.
BLOCKS = {
    "start_pad":    {"name": "Start Pad",    "faces": {"*": "cc_start_pad_side", "up": "cc_start_pad_top"}, "light": 6, "sound": "stone"},
    "goal_block":   {"name": "Goal Block",   "faces": {"*": "cc_goal_side", "up": "cc_goal_top"}, "light": 10, "sound": "metal"},
    "checkpoint":   {"name": "Checkpoint",   "faces": {"*": "cc_checkpoint"}, "light": 8, "sound": "stone"},
    "spring_pad":   {"name": "Spring Pad",   "faces": {"*": "cc_spring_side", "up": "cc_spring_top"}, "sound": "metal"},
    "dash_pad":     {"name": "Dash Pad",     "faces": {"*": "cc_dash_side", "up": "cc_dash_top"}, "light": 4, "sound": "metal"},
    "spike_block":  {"name": "Spike Block",  "faces": {"*": "cc_spike_side", "up": "cc_spike_top"}, "sound": "metal"},
    "shard":        {"name": "Shard",        "faces": {"*": "cc_shard"}, "light": 12, "passable": True, "sound": "glass"},
    "bright_brick": {"name": "Bright Brick", "faces": {"*": "cc_bright_brick"}, "sound": "stone"},
    "toon_grass":   {"name": "Toon Grass",   "faces": {"*": "cc_toon_grass_side", "up": "cc_toon_grass_top", "down": "cc_toon_dirt"}, "sound": "grass"},
    "cloud_block":  {"name": "Cloud Block",  "faces": {"*": "cc_cloud"}, "sound": "cloth"},
}

ITEMS = {
    "maker_wand": {"name": "Maker Wand", "icon": "cc_maker_wand"},
}

# Texture slot -> human description (what the art should show). Used by the
# import tool, the slot guide, and the validator.
SLOT_HINTS = {
    "cc_start_pad_top": "Start Pad top: 'begin here' marker",
    "cc_start_pad_side": "Start Pad sides",
    "cc_goal_top": "Goal Block top: finish marker",
    "cc_goal_side": "Goal Block sides",
    "cc_checkpoint": "Checkpoint (all faces)",
    "cc_spring_top": "Spring Pad top: bounce surface",
    "cc_spring_side": "Spring Pad sides",
    "cc_dash_top": "Dash Pad top: speed arrows",
    "cc_dash_side": "Dash Pad sides",
    "cc_spike_top": "Spike Block top: hazard",
    "cc_spike_side": "Spike Block sides",
    "cc_shard": "Shard collectible (transparent background allowed)",
    "cc_bright_brick": "Bright Brick (all faces)",
    "cc_toon_grass_top": "Toon Grass top",
    "cc_toon_grass_side": "Toon Grass sides",
    "cc_toon_dirt": "Toon Grass bottom",
    "cc_cloud": "Cloud Block (all faces)",
    "cc_maker_wand": "Maker Wand inventory icon (item)",
}

ITEM_SLOTS = {"cc_maker_wand"}
ALLOWED_SIZES = {16, 32, 64, 128}


def block_slots():
    out = []
    for b in BLOCKS.values():
        for tex in b["faces"].values():
            if tex not in out:
                out.append(tex)
    return out


def all_slots():
    return block_slots() + [i["icon"] for i in ITEMS.values()]
