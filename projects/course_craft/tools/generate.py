#!/usr/bin/env python3
"""Generate Course Craft pack JSON from tools/spec.py.

Writes manifests, blocks, item, recipe, lang and texture atlases. Writes a
placeholder PNG only for a texture slot that has no PNG yet, so imported art
is never overwritten. Usage: python3 tools/generate.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec  # noqa: E402
import placeholders  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "packs", spec.BP)
RP = os.path.join(ROOT, "packs", spec.RP)


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def read_version(path):
    try:
        return json.load(open(path))["header"]["version"]
    except (OSError, KeyError, ValueError):
        return [1, 0, 0]


def manifests():
    v = read_version(os.path.join(BP, "manifest.json"))
    write(os.path.join(BP, "manifest.json"), {
        "format_version": 2,
        "header": {"name": "Course Craft", "description": "Build and play platformer courses anywhere in your world.",
                   "uuid": spec.UUIDS["bp_header"], "version": v, "min_engine_version": spec.MIN_ENGINE},
        "modules": [
            {"type": "data", "uuid": spec.UUIDS["bp_data"], "version": v},
            {"type": "script", "language": "javascript", "entry": "scripts/main.js",
             "uuid": spec.UUIDS["bp_script"], "version": v},
        ],
        "dependencies": [{"uuid": spec.UUIDS["rp_header"], "version": v}]
        + [{"module_name": m, "version": ver} for m, ver in spec.SCRIPT_DEPS],
    })
    write(os.path.join(RP, "manifest.json"), {
        "format_version": 2,
        "header": {"name": "Course Craft", "description": "Course Craft textures.",
                   "uuid": spec.UUIDS["rp_header"], "version": v, "min_engine_version": spec.MIN_ENGINE},
        "modules": [{"type": "resources", "uuid": spec.UUIDS["rp_resources"], "version": v}],
    })


def blocks():
    sounds = {"format_version": "1.1.0"}
    for bid, b in spec.BLOCKS.items():
        full = f"{spec.NS}:{bid}"
        passable = b.get("passable", False)
        render = "alpha_test" if passable else "opaque"
        comps = {
            "minecraft:geometry": "minecraft:geometry.full_block",
            "minecraft:material_instances": {
                face: {"texture": tex, "render_method": render} for face, tex in b["faces"].items()
            },
            "minecraft:destructible_by_mining": {"seconds_to_destroy": 0.4},
            "minecraft:destructible_by_explosion": False,
        }
        if b.get("light"):
            comps["minecraft:light_emission"] = b["light"]
        if passable:
            comps["minecraft:collision_box"] = False
            comps["minecraft:light_dampening"] = 0
        write(os.path.join(BP, "blocks", f"{bid}.json"), {
            "format_version": "1.21.60",
            "minecraft:block": {
                "description": {"identifier": full, "menu_category": {"category": "construction"}},
                "components": comps,
            },
        })
        sounds[full] = {"sound": b["sound"]}
    write(os.path.join(RP, "blocks.json"), sounds)


def items():
    for iid, it in spec.ITEMS.items():
        write(os.path.join(BP, "items", f"{iid}.json"), {
            "format_version": "1.21.60",
            "minecraft:item": {
                "description": {"identifier": f"{spec.NS}:{iid}", "menu_category": {"category": "equipment"}},
                "components": {
                    "minecraft:icon": it["icon"],
                    "minecraft:display_name": {"value": it["name"]},
                    "minecraft:max_stack_size": 1,
                    "minecraft:hand_equipped": True,
                },
            },
        })
    write(os.path.join(BP, "recipes", "maker_wand.json"), {
        "format_version": "1.20.10",
        "minecraft:recipe_shaped": {
            "description": {"identifier": "cc:maker_wand_recipe"},
            "tags": ["crafting_table"],
            "pattern": [" G ", " S ", " S "],
            "key": {"G": {"item": "minecraft:gold_ingot"}, "S": {"item": "minecraft:stick"}},
            "unlock": [{"item": "minecraft:gold_ingot"}],
            "result": {"item": "cc:maker_wand", "count": 1},
        },
    })


def resources():
    terrain = {s: {"textures": f"textures/blocks/{s}"} for s in spec.block_slots()}
    write(os.path.join(RP, "textures", "terrain_texture.json"), {
        "resource_pack_name": "course_craft", "texture_name": "atlas.terrain",
        "padding": 8, "num_mip_levels": 4, "texture_data": terrain,
    })
    write(os.path.join(RP, "textures", "item_texture.json"), {
        "resource_pack_name": "course_craft", "texture_name": "atlas.items",
        "texture_data": {i["icon"]: {"textures": f"textures/items/{i['icon']}"} for i in spec.ITEMS.values()},
    })
    lines = [f"tile.{spec.NS}:{bid}.name={b['name']}" for bid, b in spec.BLOCKS.items()]
    lines += [f"item.{spec.NS}:{iid}={it['name']}" for iid, it in spec.ITEMS.items()]
    lines += ["pack.name=Course Craft", "pack.description=Build and play platformer courses anywhere."]
    os.makedirs(os.path.join(RP, "texts"), exist_ok=True)
    with open(os.path.join(RP, "texts", "en_US.lang"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    write(os.path.join(RP, "texts", "languages.json"), ["en_US"])


def texture_path(slot):
    sub = "items" if slot in spec.ITEM_SLOTS else "blocks"
    return os.path.join(RP, "textures", sub, f"{slot}.png")


def textures():
    made = 0
    for slot in spec.all_slots():
        path = texture_path(slot)
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            placeholders.draw(slot).save(path)
            made += 1
    return made


def main():
    manifests(); blocks(); items(); resources()
    made = textures()
    print(f"Generated pack JSON; {made} placeholder texture(s) written (existing art untouched).")


if __name__ == "__main__":
    main()
