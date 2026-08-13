#!/usr/bin/env python3
"""Create temporary Teardrop entity variants for real-Bedrock spawn diagnosis.

These files are for CI only and are added *after* the release .mcaddon is built
and statically validated. They let one BDS boot identify the smallest Teardrop
state that fails to instantiate.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


def dump(path: Path, entity: dict) -> None:
    path.write_text(json.dumps(entity, indent=2) + "\n", encoding="utf-8")


def with_id(source: dict, ident: str) -> dict:
    out = copy.deepcopy(source)
    out["minecraft:entity"]["description"]["identifier"] = ident
    return out


def main() -> int:
    project = Path(sys.argv[1]).resolve()
    entity_dir = project / "BP" / "entities"
    source = json.loads((entity_dir / "teardrop.json").read_text(encoding="utf-8"))
    full = source["minecraft:entity"]
    desc = copy.deepcopy(full["description"])
    base_components = copy.deepcopy(full["components"])
    wild = copy.deepcopy(full["component_groups"]["junk_bunch:wild"])

    # Minimal registration/summon sanity check.
    minimal = {
        "format_version": source["format_version"],
        "minecraft:entity": {
            "description": {**desc, "identifier": "junk_bunch:td_diag_min"},
            "components": {
                "minecraft:type_family": {"family": ["td_diag", "mob"]},
                "minecraft:health": {"value": 20, "max": 20},
                "minecraft:collision_box": {"width": 0.6, "height": 0.9},
                "minecraft:physics": {},
            },
        },
    }
    dump(entity_dir / "td_diag_min.json", minimal)

    # Exact base components from Teardrop, no groups or events.
    base = {
        "format_version": source["format_version"],
        "minecraft:entity": {
            "description": {**desc, "identifier": "junk_bunch:td_diag_base"},
            "components": copy.deepcopy(base_components),
        },
    }
    dump(entity_dir / "td_diag_base.json", base)

    # Wild tameable group defined but never activated.
    group_only = copy.deepcopy(base)
    group_only["minecraft:entity"]["description"]["identifier"] = "junk_bunch:td_diag_group_only"
    group_only["minecraft:entity"]["component_groups"] = {"junk_bunch:wild": copy.deepcopy(wild)}
    dump(entity_dir / "td_diag_group_only.json", group_only)

    # Wild group activated by spawn event, matching release v1.2.1 startup state.
    spawn_wild = copy.deepcopy(group_only)
    spawn_wild["minecraft:entity"]["description"]["identifier"] = "junk_bunch:td_diag_spawn_wild"
    spawn_wild["minecraft:entity"]["events"] = {
        "minecraft:entity_spawned": {
            "add": {"component_groups": ["junk_bunch:wild"]}
        }
    }
    dump(entity_dir / "td_diag_spawn_wild.json", spawn_wild)

    # Same tameable component placed directly in base components. This mirrors
    # the older v1.2.0 lifecycle closely enough to identify tameable factory issues.
    tame_base = copy.deepcopy(base)
    tame_base["minecraft:entity"]["description"]["identifier"] = "junk_bunch:td_diag_tame_base"
    tame_base["minecraft:entity"]["components"].update(copy.deepcopy(wild))
    dump(entity_dir / "td_diag_tame_base.json", tame_base)

    print("Created diagnostic entities:")
    for name in (
        "td_diag_min",
        "td_diag_base",
        "td_diag_group_only",
        "td_diag_spawn_wild",
        "td_diag_tame_base",
    ):
        print(f"  junk_bunch:{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
