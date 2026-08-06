#!/usr/bin/env python3
"""Build the Baloney add-on from the reference sheet."""

import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import baloney as B
from generate_character import uuid_from, to_hex

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CID = "baloney"
DISPLAY = "Baloney"
ENTITY = f"junkbunch:{CID}"
ITEM = f"junkbunch:spawn_balloon"
VERSION = [1, 0, 1]


def w(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=2)
        fh.write("\n")


def build(out_dir):
    BP = os.path.join(out_dir, "JunkBunch_BP")
    RP = os.path.join(out_dir, "JunkBunch_RP")

    bp_h, bp_m = uuid_from(CID + "|bp|header"), uuid_from(CID + "|bp|module")
    rp_h, rp_m = uuid_from(CID + "|rp|header"), uuid_from(CID + "|rp|module")

    w(os.path.join(BP, "manifest.json"), {
        "format_version": 2,
        "header": {"name": f"{DISPLAY} (Junk Bunch)", "description": f"{DISPLAY} - behaviour",
                   "uuid": bp_h, "version": VERSION, "min_engine_version": [1, 20, 50]},
        "modules": [{"type": "data", "description": f"{DISPLAY} entity and spawn balloon",
                     "uuid": bp_m, "version": VERSION}],
        "dependencies": [{"uuid": rp_h, "version": VERSION}],
    })
    w(os.path.join(RP, "manifest.json"), {
        "format_version": 2,
        "header": {"name": f"{DISPLAY} (Junk Bunch)", "description": f"{DISPLAY} - looks",
                   "uuid": rp_h, "version": VERSION, "min_engine_version": [1, 20, 50]},
        "modules": [{"type": "resources", "description": f"{DISPLAY} model and texture",
                     "uuid": rp_m, "version": VERSION}],
    })

    # ---- entity: a balloon drifts, never takes fall damage --------------
    w(os.path.join(BP, "entities", f"{CID}.json"), {
        "format_version": "1.20.50",
        "minecraft:entity": {
            "description": {"identifier": ENTITY, "is_spawnable": True,
                            "is_summonable": True, "is_experimental": False},
            "component_groups": {
                "junkbunch:wild": {
                    "minecraft:tameable": {
                        "probability": 1.0, "tame_items": [ITEM],
                        "tame_event": {"event": "junkbunch:on_tamed", "target": "self"}}
                },
                "junkbunch:tamed": {
                    "minecraft:is_tamed": {},
                    "minecraft:behavior.follow_owner": {
                        "priority": 3, "speed_multiplier": 1.2,
                        "start_distance": 4.0, "stop_distance": 2.0},
                    "minecraft:persistent": {},
                },
            },
            "components": {
                "minecraft:type_family": {"family": [CID, "junkbunch", "mob"]},
                "minecraft:health": {"value": 10, "max": 10},
                "minecraft:collision_box": {"width": 0.7, "height": 1.0},
                "minecraft:breathable": {"total_supply": 15, "suffocate_time": 0},
                "minecraft:physics": {"has_gravity": True, "has_collision": True},
                "minecraft:movement": {"value": 0.24},
                "minecraft:movement.basic": {},
                "minecraft:navigation.walk": {"can_path_over_water": True,
                                              "avoid_water": True,
                                              "avoid_damage_blocks": True},
                "minecraft:jump.static": {},
                "minecraft:can_climb": {},
                "minecraft:nameable": {},
                "minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True},
                "minecraft:leashable": {"soft_distance": 4.0, "hard_distance": 6.0,
                                        "max_distance": 10.0},
                # he is full of air: he drifts down instead of falling
                "minecraft:damage_sensor": {"triggers": [{"cause": "fall",
                                                          "deals_damage": False}]},
                "minecraft:behavior.float": {"priority": 0},
                "minecraft:behavior.panic": {"priority": 1, "speed_multiplier": 1.3},
                "minecraft:behavior.look_at_player": {"priority": 6, "look_distance": 8.0,
                                                      "probability": 0.10},
                "minecraft:behavior.random_stroll": {"priority": 7, "speed_multiplier": 0.9},
                "minecraft:behavior.random_look_around": {"priority": 8},
            },
            "events": {
                "minecraft:entity_spawned": {"add": {"component_groups": ["junkbunch:wild"]}},
                "junkbunch:on_tamed": {"remove": {"component_groups": ["junkbunch:wild"]},
                                       "add": {"component_groups": ["junkbunch:tamed"]}},
            },
        },
    })

    w(os.path.join(BP, "items", "spawn_balloon.json"), {
        "format_version": "1.20.50",
        "minecraft:item": {
            "description": {"identifier": ITEM, "menu_category": {"category": "equipment"}},
            "components": {
                "minecraft:max_stack_size": 1,
                "minecraft:icon": {"texture": "spawn_balloon"},
                "minecraft:hand_equipped": True,
                "minecraft:allow_off_hand": True,
                "minecraft:entity_placer": {"entity": ENTITY},
            },
        },
    })

    w(os.path.join(BP, "recipes", "spawn_balloon.json"), {
        "format_version": "1.20.50",
        "minecraft:recipe_shaped": {
            "description": {"identifier": ITEM},
            "tags": ["crafting_table"],
            "pattern": [" A ", "ABA", " C "],
            "key": {"A": {"item": "minecraft:pink_dye"},
                    "B": {"item": "minecraft:slime_ball"},
                    "C": {"item": "minecraft:string"}},
            "unlock": [{"item": "minecraft:slime_ball"}],
            "result": {"item": ITEM, "count": 1},
        },
    })

    w(os.path.join(RP, "entity", f"{CID}.json"), {
        "format_version": "1.10.0",
        "minecraft:client_entity": {
            "description": {
                "identifier": ENTITY,
                "materials": {"default": "entity_alphatest"},
                "geometry": {"default": f"geometry.{CID}.main"},
                "textures": {"default": f"textures/entity/junkbunch/{CID}"},
                "animations": {
                    "idle": f"animation.{CID}.idle",
                    "walk": f"animation.{CID}.walk",
                    "move_controller": f"controller.animation.{CID}.move",
                },
                "scripts": {"animate": ["move_controller"]},
                "render_controllers": [f"controller.render.{CID}"],
                "spawn_egg": {"base_color": to_hex(B.PINK),
                              "overlay_color": to_hex(B.PINK_LIT)},
            }
        },
    })

    w(os.path.join(RP, "models/entity", f"{CID}.geo.json"), B.build_geometry(CID))

    w(os.path.join(RP, "render_controllers", f"{CID}.json"), {
        "format_version": "1.10.0",
        "render_controllers": {
            f"controller.render.{CID}": {
                "geometry": "Geometry.default",
                "materials": [{"*": "Material.default"}],
                "textures": ["Texture.default"]}
        },
    })

    w(os.path.join(RP, "animation_controllers", f"{CID}.json"), {
        "format_version": "1.10.0",
        "animation_controllers": {
            f"controller.animation.{CID}.move": {
                "initial_state": "idle",
                "states": {
                    "idle": {"animations": ["idle"],
                             "transitions": [{"walk": "query.modified_move_speed > 0.1"}]},
                    "walk": {"animations": ["walk"],
                             "transitions": [{"idle": "query.modified_move_speed <= 0.1"}]},
                }}
        },
    })

    # a balloon bobs and sways on its string
    w(os.path.join(RP, "animations", f"{CID}.animation.json"), {
        "format_version": "1.8.0",
        "animations": {
            f"animation.{CID}.idle": {
                "loop": True, "animation_length": 3.5,
                "bones": {"body": {
                    "position": [0, "math.sin(query.anim_time * 100) * 0.7", 0],
                    "rotation": [0, 0, "math.sin(query.anim_time * 70) * 4"]}},
            },
            f"animation.{CID}.walk": {
                "loop": True, "animation_length": 1.0,
                "bones": {"body": {
                    "position": ["math.sin(query.anim_time * 360) * 0.4",
                                 "math.abs(math.sin(query.anim_time * 720)) * 1.1", 0],
                    "rotation": [0, 0, "math.sin(query.anim_time * 360) * 9"]}},
            },
        },
    })

    w(os.path.join(RP, "textures", "item_texture.json"), {
        "resource_pack_name": "JunkBunch",
        "texture_name": "atlas.items",
        "texture_data": {"spawn_balloon": {"textures": "textures/items/spawn_balloon"}},
    })
    w(os.path.join(RP, "texts", "languages.json"), ["en_US"])
    os.makedirs(os.path.join(RP, "texts"), exist_ok=True)
    with open(os.path.join(RP, "texts", "en_US.lang"), "w") as fh:
        fh.write(f"item.{ITEM}=Spawn Balloon\n"
                 f"entity.{ENTITY}.name={DISPLAY}\n"
                 f"item.spawn_egg.entity.{ENTITY}.name=Spawn {DISPLAY}\n"
                 f"pack.name={DISPLAY} (Junk Bunch)\n"
                 f"pack.description={DISPLAY} - a Junk Bunch character\n")

    for d in ("textures/entity/junkbunch", "textures/items"):
        os.makedirs(os.path.join(RP, d), exist_ok=True)
    B.build_texture().save(os.path.join(RP, "textures/entity/junkbunch", f"{CID}.png"))
    icon = B.build_item_icon()
    icon.save(os.path.join(RP, "textures/items", "spawn_balloon.png"))

    # pack thumbnail: the balloon, big
    thumb = icon.resize((128, 128), 0)
    thumb.save(os.path.join(RP, "pack_icon.png"))
    thumb.save(os.path.join(BP, "pack_icon.png"))


if __name__ == "__main__":
    out = os.path.join(REPO, "build", CID)
    if os.path.exists(out):
        import shutil
        shutil.rmtree(out)
    build(out)
    print(f"pack written to build/{CID}")

    mca = os.path.join(REPO, "Baloney.mcaddon")
    if os.path.exists(mca):
        os.remove(mca)
    with zipfile.ZipFile(mca, "w", zipfile.ZIP_DEFLATED) as z:
        for pack in ("JunkBunch_BP", "JunkBunch_RP"):
            root = os.path.join(out, pack)
            for dp, _dn, fn in os.walk(root):
                for f in sorted(fn):
                    full = os.path.join(dp, f)
                    z.write(full, os.path.relpath(full, out))
    print("built Baloney.mcaddon")
