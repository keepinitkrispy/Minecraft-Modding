#!/usr/bin/env python3
"""Build Teardrop v1.2.1 from the exact reported-failing v1.2.0 fixture.

This script intentionally makes only evidence-driven compatibility/lifecycle fixes:
- bump both pack versions and cross-pack dependency versions to 1.2.1
- make render-controller UV animation fields explicit (zero offset/unit scale)
- correct tame lifecycle so owner/follow/sit/attack logic is activated only after taming
- preserve the v1.2 visual geometry, textures, animations, scripts, and gameplay mechanics
- package canonical nested .mcpack payloads into a .mcaddon
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

VERSION = [1, 2, 1]
CORALS = [
    "minecraft:tube_coral",
    "minecraft:brain_coral",
    "minecraft:bubble_coral",
    "minecraft:fire_coral",
    "minecraft:horn_coral",
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def bump_manifests(project: Path) -> None:
    for side in ("BP", "RP"):
        path = project / side / "manifest.json"
        data = read_json(path)
        data["header"]["version"] = VERSION.copy()
        for module in data.get("modules", []):
            module["version"] = VERSION.copy()
        for dep in data.get("dependencies", []):
            if "uuid" in dep:
                dep["version"] = VERSION.copy()
        write_json(path, data)


def fix_render_controllers(project: Path) -> None:
    path = project / "RP" / "render_controllers" / "teardrop.render_controllers.json"
    data = read_json(path)
    for controller in data["render_controllers"].values():
        controller["uv_anim"] = {
            "offset": [0.0, 0.0],
            "scale": [1.0, 1.0],
        }
    write_json(path, data)


def fix_tame_lifecycle(project: Path) -> None:
    path = project / "BP" / "entities" / "teardrop.json"
    data = read_json(path)
    entity = data["minecraft:entity"]
    components = entity["components"]
    groups = entity["component_groups"]
    events = entity["events"]

    tameable = components.pop(
        "minecraft:tameable",
        {
            "probability": 1.0,
            "tame_items": CORALS,
            "tame_event": {"event": "minecraft:on_tame", "target": "self"},
        },
    )
    components.pop("minecraft:sittable", None)
    components.pop("minecraft:behavior.stay_while_sitting", None)

    # The existing active_companion group already contains shooter, owner defense,
    # follow-owner, and ranged-attack behaviors. Make it the true tamed state.
    active = groups["junk_bunch:active_companion"]
    active["minecraft:is_tamed"] = {}
    active["minecraft:sittable"] = {}
    active["minecraft:behavior.stay_while_sitting"] = {"priority": 0}

    groups["junk_bunch:wild"] = {"minecraft:tameable": tameable}

    events["minecraft:entity_spawned"] = {
        "add": {"component_groups": ["junk_bunch:wild"]}
    }
    events["minecraft:on_tame"] = {
        "remove": {"component_groups": ["junk_bunch:wild"]},
        "add": {"component_groups": ["junk_bunch:active_companion"]},
    }
    events["junk_bunch:become_obsidian"] = {
        "remove": {
            "component_groups": [
                "junk_bunch:wild",
                "junk_bunch:active_companion",
            ]
        },
        "add": {"component_groups": ["junk_bunch:obsidian_form"]},
    }
    write_json(path, data)


def validate_patch(project: Path) -> None:
    # Fail the build before packaging if our intended invariants are absent.
    for path in project.rglob("*.json"):
        read_json(path)

    bp_manifest = read_json(project / "BP" / "manifest.json")
    rp_manifest = read_json(project / "RP" / "manifest.json")
    assert bp_manifest["header"]["version"] == VERSION
    assert rp_manifest["header"]["version"] == VERSION

    rc = read_json(project / "RP" / "render_controllers" / "teardrop.render_controllers.json")
    for controller in rc["render_controllers"].values():
        assert controller["uv_anim"] == {"offset": [0.0, 0.0], "scale": [1.0, 1.0]}

    teardrop = read_json(project / "BP" / "entities" / "teardrop.json")["minecraft:entity"]
    assert "minecraft:tameable" not in teardrop["components"]
    assert teardrop["events"]["minecraft:entity_spawned"]["add"]["component_groups"] == ["junk_bunch:wild"]
    active = teardrop["component_groups"]["junk_bunch:active_companion"]
    assert "minecraft:is_tamed" in active
    assert "minecraft:sittable" in active


def zip_tree(source: Path, output: Path) -> None:
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(source).as_posix())


def package(project: Path, output: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        bp_pack = tmp_path / "Teardrop_BP.mcpack"
        rp_pack = tmp_path / "Teardrop_RP.mcpack"
        zip_tree(project / "BP", bp_pack)
        zip_tree(project / "RP", rp_pack)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(bp_pack, bp_pack.name)
            zf.write(rp_pack, rp_pack.name)

    with zipfile.ZipFile(output) as zf:
        assert set(zf.namelist()) == {"Teardrop_BP.mcpack", "Teardrop_RP.mcpack"}
        assert zf.testzip() is None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path, help="Folder containing BP/ and RP/")
    parser.add_argument("output", type=Path, help="Output .mcaddon")
    args = parser.parse_args()

    project = args.project.resolve()
    output = args.output.resolve()
    bump_manifests(project)
    fix_render_controllers(project)
    fix_tame_lifecycle(project)
    validate_patch(project)
    package(project, output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
