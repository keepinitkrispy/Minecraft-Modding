#!/usr/bin/env python3
"""
Validate the Junk Bunch Bedrock add-on.

Checks every manifest, UUID, dependency, JSON file and cross-reference so a broken
pack is caught here instead of failing to import on a console.

Usage:
    python3 scripts/validate_packs.py [root]

`root` is the directory containing JunkBunch_BP/ and JunkBunch_RP/.
Defaults to <repo>/packs. Exits 0 when everything passes, 1 otherwise.
"""

import json
import os
import re
import sys

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
)

BP_NAME = "JunkBunch_BP"
RP_NAME = "JunkBunch_RP"

VALID_MODULE_TYPES = {"data", "resources", "script", "world_template", "skin_pack"}

errors = []
warnings = []
checks_run = 0


def check(condition, message):
    """Record a failure when condition is falsy."""
    global checks_run
    checks_run += 1
    if not condition:
        errors.append(message)
    return bool(condition)


def warn(condition, message):
    if not condition:
        warnings.append(message)


def load_json(path):
    """Parse a JSON file, recording an error on failure. Returns None on failure."""
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        errors.append(f"INVALID JSON: {path} -> line {exc.lineno} col {exc.colno}: {exc.msg}")
    except OSError as exc:
        errors.append(f"UNREADABLE: {path} -> {exc}")
    return None


def walk_json(root):
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in sorted(filenames):
            if name.lower().endswith(".json"):
                yield os.path.join(dirpath, name)


def rel(root, path):
    return os.path.relpath(path, root)


# --------------------------------------------------------------------------
# 1. locate packs
# --------------------------------------------------------------------------
def main():
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(repo, "packs")
    root = os.path.abspath(root)

    bp = os.path.join(root, BP_NAME)
    rp = os.path.join(root, RP_NAME)

    print(f"Validating add-on in: {root}")
    print("-" * 68)

    if not check(os.path.isdir(bp), f"Missing behavior pack folder: {BP_NAME}/"):
        report()
        return 1
    if not check(os.path.isdir(rp), f"Missing resource pack folder: {RP_NAME}/"):
        report()
        return 1

    # ----------------------------------------------------------------------
    # 2. every JSON file parses
    # ----------------------------------------------------------------------
    parsed = {}
    for pack_root in (bp, rp):
        for path in walk_json(pack_root):
            data = load_json(path)
            if data is not None:
                parsed[path] = data
    print(f"[ok] parsed {len(parsed)} JSON files")

    # ----------------------------------------------------------------------
    # 3. manifests
    # ----------------------------------------------------------------------
    bp_manifest_path = os.path.join(bp, "manifest.json")
    rp_manifest_path = os.path.join(rp, "manifest.json")

    check(os.path.isfile(bp_manifest_path), f"{BP_NAME}/manifest.json is missing")
    check(os.path.isfile(rp_manifest_path), f"{RP_NAME}/manifest.json is missing")

    bp_manifest = parsed.get(bp_manifest_path)
    rp_manifest = parsed.get(rp_manifest_path)

    seen_uuids = {}

    def validate_manifest(manifest, label, expected_module_type):
        """Returns (header_uuid, dependency_uuids)."""
        if manifest is None:
            return None, []

        check(manifest.get("format_version") == 2,
              f"{label}: format_version must be 2")

        header = manifest.get("header")
        if not check(isinstance(header, dict), f"{label}: missing 'header' object"):
            return None, []

        header_uuid = header.get("uuid")
        check(isinstance(header_uuid, str) and UUID_RE.match(header_uuid or ""),
              f"{label}: header.uuid missing or not a valid UUID (got {header_uuid!r})")
        check(isinstance(header.get("version"), list) and len(header["version"]) == 3,
              f"{label}: header.version must be a 3-number array")
        mev = header.get("min_engine_version")
        check(isinstance(mev, list) and len(mev) == 3,
              f"{label}: header.min_engine_version must be a 3-number array")
        check(isinstance(header.get("name"), str) and header.get("name"),
              f"{label}: header.name missing")

        if header_uuid:
            if header_uuid in seen_uuids:
                errors.append(
                    f"DUPLICATE UUID {header_uuid}: used by both "
                    f"{seen_uuids[header_uuid]} and {label} header"
                )
            seen_uuids[header_uuid] = f"{label} header"

        modules = manifest.get("modules")
        check(isinstance(modules, list) and len(modules) >= 1,
              f"{label}: must declare at least one module")
        if isinstance(modules, list):
            for idx, module in enumerate(modules):
                mlabel = f"{label} modules[{idx}]"
                mtype = module.get("type")
                check(mtype in VALID_MODULE_TYPES,
                      f"{mlabel}: invalid module type {mtype!r} "
                      f"(valid: {sorted(VALID_MODULE_TYPES)})")
                check(mtype == expected_module_type,
                      f"{mlabel}: expected module type {expected_module_type!r}, got {mtype!r}")
                muuid = module.get("uuid")
                check(isinstance(muuid, str) and UUID_RE.match(muuid or ""),
                      f"{mlabel}: uuid missing or not a valid UUID (got {muuid!r})")
                check(isinstance(module.get("version"), list) and len(module["version"]) == 3,
                      f"{mlabel}: version must be a 3-number array")
                if muuid:
                    if muuid in seen_uuids:
                        errors.append(
                            f"DUPLICATE UUID {muuid}: used by both "
                            f"{seen_uuids[muuid]} and {mlabel}"
                        )
                    seen_uuids[muuid] = mlabel

        deps = manifest.get("dependencies", [])
        dep_uuids = []
        if deps:
            check(isinstance(deps, list), f"{label}: dependencies must be an array")
            for idx, dep in enumerate(deps or []):
                dlabel = f"{label} dependencies[{idx}]"
                duuid = dep.get("uuid")
                # module_name dependencies (script API) have no uuid
                if duuid is None and dep.get("module_name"):
                    continue
                check(isinstance(duuid, str) and UUID_RE.match(duuid or ""),
                      f"{dlabel}: uuid missing or not a valid UUID (got {duuid!r})")
                check(isinstance(dep.get("version"), list) and len(dep["version"]) == 3,
                      f"{dlabel}: version must be a 3-number array")
                if duuid:
                    dep_uuids.append((duuid, dlabel))
        return header_uuid, dep_uuids

    bp_header_uuid, bp_deps = validate_manifest(bp_manifest, BP_NAME, "data")
    rp_header_uuid, rp_deps = validate_manifest(rp_manifest, RP_NAME, "resources")

    # ----------------------------------------------------------------------
    # 4. dependency resolution + no circular dependency
    # ----------------------------------------------------------------------
    known_headers = {u for u in (bp_header_uuid, rp_header_uuid) if u}
    for duuid, dlabel in bp_deps + rp_deps:
        check(duuid in known_headers,
              f"{dlabel}: dependency uuid {duuid} does not match any pack header uuid "
              f"in this add-on")

    bp_dep_uuids = {u for u, _ in bp_deps}
    rp_dep_uuids = {u for u, _ in rp_deps}
    circular = (rp_header_uuid in bp_dep_uuids) and (bp_header_uuid in rp_dep_uuids)
    check(not circular,
          "CIRCULAR DEPENDENCY: behavior pack and resource pack depend on each other")

    for duuid, dlabel in bp_deps:
        check(duuid != bp_header_uuid, f"{dlabel}: pack depends on itself")
    for duuid, dlabel in rp_deps:
        check(duuid != rp_header_uuid, f"{dlabel}: pack depends on itself")

    print(f"[ok] manifests validated, {len(seen_uuids)} unique UUIDs")

    # ----------------------------------------------------------------------
    # 5. collect definitions from the resource pack
    # ----------------------------------------------------------------------
    geometries = set()
    animations = set()
    anim_controllers = set()
    render_controllers = set()
    item_texture_keys = set()

    for path, data in parsed.items():
        if not path.startswith(rp):
            continue
        if "minecraft:geometry" in data:
            for geo in data["minecraft:geometry"]:
                ident = geo.get("description", {}).get("identifier")
                if ident:
                    geometries.add(ident)
        # legacy geometry format: {"geometry.name": {...}}
        for key in data:
            if key.startswith("geometry."):
                geometries.add(key)
        if "animations" in data and "animation_controllers" not in data:
            for key in data["animations"]:
                if key.startswith("animation."):
                    animations.add(key)
        if "animation_controllers" in data:
            for key in data["animation_controllers"]:
                anim_controllers.add(key)
        if "render_controllers" in data:
            for key in data["render_controllers"]:
                render_controllers.add(key)
        if "texture_data" in data and os.path.basename(path) == "item_texture.json":
            item_texture_keys.update(data["texture_data"].keys())

    # Vanilla render controller is always available.
    render_controllers.add("controller.render.default")

    # ----------------------------------------------------------------------
    # 6. behaviour-pack entities and items
    # ----------------------------------------------------------------------
    bp_entities = set()
    bp_items = set()

    # pass 1: collect entity identifiers so item references can be resolved
    for path, data in parsed.items():
        if not path.startswith(bp):
            continue
        if "minecraft:entity" in data:
            ident = data["minecraft:entity"].get("description", {}).get("identifier")
            if check(ident, f"{rel(root, path)}: entity has no description.identifier"):
                bp_entities.add(ident)
            fmt = data.get("format_version")
            check(isinstance(fmt, str),
                  f"{rel(root, path)}: format_version must be a string for entities")

    # pass 2: items (may reference entities collected above)
    for path, data in parsed.items():
        if not path.startswith(bp):
            continue
        if "minecraft:item" in data:
            desc = data["minecraft:item"].get("description", {})
            ident = desc.get("identifier")
            if check(ident, f"{rel(root, path)}: item has no description.identifier"):
                bp_items.add(ident)
            check("category" not in desc,
                  f"{rel(root, path)}: legacy 'category' in item description; "
                  f"use 'menu_category' instead")
            comps = data["minecraft:item"].get("components", {})
            for bad in ("minecraft:on_use", "minecraft:on_use_on", "minecraft:on_place"):
                check(bad not in comps,
                      f"{rel(root, path)}: '{bad}' is not a valid stable item component")
            icon = comps.get("minecraft:icon")
            if isinstance(icon, dict):
                tex = icon.get("texture")
                check(tex in item_texture_keys,
                      f"{rel(root, path)}: icon texture key {tex!r} is not defined in "
                      f"{RP_NAME}/textures/item_texture.json")
            placer = comps.get("minecraft:entity_placer")
            if isinstance(placer, dict) and placer.get("entity"):
                check(placer["entity"] in bp_entities or placer["entity"].startswith("minecraft:"),
                      f"{rel(root, path)}: entity_placer references unknown entity "
                      f"{placer['entity']!r}")

    # entity events must not use invalid responses
    INVALID_EVENT_KEYS = {"run_command"}
    for path, data in parsed.items():
        if not path.startswith(bp) or "minecraft:entity" not in data:
            continue
        for ev_name, ev_body in (data["minecraft:entity"].get("events") or {}).items():
            bodies = ev_body if isinstance(ev_body, list) else [ev_body]
            for body in bodies:
                if not isinstance(body, dict):
                    continue
                for key in body:
                    check(key not in INVALID_EVENT_KEYS,
                          f"{rel(root, path)}: event {ev_name!r} uses invalid response "
                          f"{key!r}")
        # component groups referenced by events must exist
        groups = set((data["minecraft:entity"].get("component_groups") or {}).keys())
        for ev_name, ev_body in (data["minecraft:entity"].get("events") or {}).items():
            bodies = ev_body if isinstance(ev_body, list) else [ev_body]
            for body in bodies:
                if not isinstance(body, dict):
                    continue
                for action in ("add", "remove"):
                    for grp in (body.get(action) or {}).get("component_groups", []):
                        check(grp in groups,
                              f"{rel(root, path)}: event {ev_name!r} {action}s unknown "
                              f"component group {grp!r}")

    print(f"[ok] behavior pack: {len(bp_entities)} entities, {len(bp_items)} items")

    # ----------------------------------------------------------------------
    # 7. client entities: every reference must resolve
    # ----------------------------------------------------------------------
    rp_client_entities = set()
    for path, data in parsed.items():
        if "minecraft:client_entity" not in data:
            continue
        label = rel(root, path)
        desc = data["minecraft:client_entity"].get("description", {})
        ident = desc.get("identifier")
        if check(ident, f"{label}: client entity has no identifier"):
            rp_client_entities.add(ident)
            check(ident in bp_entities,
                  f"{label}: client entity {ident!r} has no matching behavior-pack entity")

        check("animation_controllers" not in desc,
              f"{label}: 'animation_controllers' is not a valid client_entity field; "
              f"list controllers in 'animations' and run them via 'scripts.animate'")

        # geometry
        geo_map = desc.get("geometry") or desc.get("geometries") or {}
        check("geometry" in desc,
              f"{label}: client entity should use 'geometry' (not 'geometries')")
        for key, geo_id in geo_map.items():
            check(geo_id in geometries,
                  f"{label}: geometry {geo_id!r} (key {key!r}) is not defined in any "
                  f"model file")

        # textures
        for key, tex in (desc.get("textures") or {}).items():
            tex_path = os.path.join(rp, tex)
            found = any(os.path.isfile(tex_path + ext) for ext in (".png", ".tga", ".jpg"))
            check(found,
                  f"{label}: texture {tex!r} (key {key!r}) not found at "
                  f"{RP_NAME}/{tex}.png")

        # animations + controllers
        anim_map = desc.get("animations") or {}
        for key, anim_id in anim_map.items():
            if anim_id.startswith("controller."):
                check(anim_id in anim_controllers,
                      f"{label}: animation controller {anim_id!r} (key {key!r}) is not "
                      f"defined in {RP_NAME}/animation_controllers/")
            else:
                check(anim_id in animations,
                      f"{label}: animation {anim_id!r} (key {key!r}) is not defined in "
                      f"{RP_NAME}/animations/")

        # scripts.animate entries must exist in the animations map
        for entry in (desc.get("scripts") or {}).get("animate", []):
            name = entry if isinstance(entry, str) else list(entry.keys())[0]
            check(name in anim_map,
                  f"{label}: scripts.animate references {name!r}, which is not a key in "
                  f"'animations'")

        # render controllers
        for rc in desc.get("render_controllers", []):
            name = rc if isinstance(rc, str) else list(rc.keys())[0]
            check(name in render_controllers,
                  f"{label}: render controller {name!r} is not defined in "
                  f"{RP_NAME}/render_controllers/")

    for ident in bp_entities:
        warn(ident in rp_client_entities,
             f"entity {ident!r} has no client entity in {RP_NAME}/entity/ "
             f"(it will render as a white box)")

    # ----------------------------------------------------------------------
    # 8. animation controllers must reference animations the entity knows
    # ----------------------------------------------------------------------
    for path, data in parsed.items():
        if "animation_controllers" not in data:
            continue
        label = rel(root, path)
        for ctrl_name, ctrl in data["animation_controllers"].items():
            states = ctrl.get("states") or {}
            initial = ctrl.get("initial_state")
            if initial:
                check(initial in states,
                      f"{label}: {ctrl_name} initial_state {initial!r} is not a defined state")
            for state_name, state in states.items():
                for tr in state.get("transitions", []):
                    for target in tr:
                        check(target in states,
                              f"{label}: {ctrl_name} state {state_name!r} transitions to "
                              f"unknown state {target!r}")

    # ----------------------------------------------------------------------
    # 9. texture files referenced by item_texture.json exist
    # ----------------------------------------------------------------------
    for path, data in parsed.items():
        if os.path.basename(path) != "item_texture.json":
            continue
        label = rel(root, path)
        for key, entry in (data.get("texture_data") or {}).items():
            textures = entry.get("textures")
            paths = [textures] if isinstance(textures, str) else (textures or [])
            for tex in paths:
                full = os.path.join(rp, tex)
                found = any(os.path.isfile(full + ext) for ext in (".png", ".tga", ".jpg"))
                check(found, f"{label}: key {key!r} points at missing texture "
                             f"{RP_NAME}/{tex}.png")

    # ----------------------------------------------------------------------
    # 10. folder structure sanity
    # ----------------------------------------------------------------------
    KNOWN_BP_DIRS = {
        "entities", "items", "recipes", "loot_tables", "functions", "blocks",
        "spawn_rules", "trading", "animations", "animation_controllers", "scripts",
        "features", "feature_rules", "biomes", "dialogue", "structures",
    }
    KNOWN_RP_DIRS = {
        "entity", "models", "textures", "animations", "animation_controllers",
        "render_controllers", "particles", "sounds", "texts", "ui", "fogs",
        "attachables", "items", "materials", "font", "blocks", "biomes",
    }

    for name in sorted(os.listdir(bp)):
        full = os.path.join(bp, name)
        if os.path.isdir(full):
            warn(name in KNOWN_BP_DIRS,
                 f"{BP_NAME}/{name}/ is not a recognised behavior pack folder")
    for name in sorted(os.listdir(rp)):
        full = os.path.join(rp, name)
        if os.path.isdir(full):
            warn(name in KNOWN_RP_DIRS,
                 f"{RP_NAME}/{name}/ is not a recognised resource pack folder")

    # render controllers must reference valid arrays
    check(len(render_controllers) > 1,
          f"{RP_NAME}/render_controllers/ defines no render controllers")

    print(f"[ok] resource pack: {len(geometries)} geometries, {len(animations)} animations, "
          f"{len(anim_controllers)} animation controllers, "
          f"{len(render_controllers) - 1} render controllers")

    return report()


def report():
    print("-" * 68)
    for w in warnings:
        print(f"  warning: {w}")
    if errors:
        print(f"FAILED - {len(errors)} problem(s) found in {checks_run} checks:\n")
        for e in errors:
            print(f"  ERROR: {e}")
        print()
        return 1
    print(f"PASSED - {checks_run} checks, 0 errors, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
