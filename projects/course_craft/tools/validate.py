#!/usr/bin/env python3
"""Static validation (ladder levels 1-2) for Course Craft. Exit 0 = pass."""
import json
import os
import re
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def run(root=ROOT):
    errors = []
    bp = os.path.join(root, "packs", spec.BP)
    rp = os.path.join(root, "packs", spec.RP)

    def load(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"bad JSON {os.path.relpath(p, root)}: {exc}")
            return None

    for base in (bp, rp):
        for dp, _d, fs in os.walk(base):
            for f in fs:
                if f.endswith(".json"):
                    load(os.path.join(dp, f))

    bpm, rpm = load(os.path.join(bp, "manifest.json")), load(os.path.join(rp, "manifest.json"))
    if bpm and rpm:
        uuids = [bpm["header"]["uuid"], rpm["header"]["uuid"]] + [m["uuid"] for m in bpm["modules"] + rpm["modules"]]
        if len(set(uuids)) != len(uuids):
            errors.append("duplicate UUIDs across manifests")
        errors += [f"invalid UUID {u}" for u in uuids if not UUID_RE.match(u)]
        deps = bpm.get("dependencies", [])
        if not any(d.get("uuid") == rpm["header"]["uuid"] and d.get("version") == rpm["header"]["version"] for d in deps):
            errors.append("BP does not depend on RP header uuid+version")
        scripts = [m for m in bpm["modules"] if m["type"] == "script"]
        if len(scripts) != 1 or not os.path.isfile(os.path.join(bp, scripts[0].get("entry", ""))):
            errors.append("script module entry missing")
        names = {d.get("module_name") for d in deps}
        for m, _v in spec.SCRIPT_DEPS:
            if m not in names:
                errors.append(f"missing script dependency {m}")

    terrain = load(os.path.join(rp, "textures", "terrain_texture.json")) or {}
    tdata = terrain.get("texture_data", {})
    items_atlas = (load(os.path.join(rp, "textures", "item_texture.json")) or {}).get("texture_data", {})
    lang = open(os.path.join(rp, "texts", "en_US.lang"), encoding="utf-8").read() if os.path.exists(os.path.join(rp, "texts", "en_US.lang")) else ""

    block_ids = set()
    bdir = os.path.join(bp, "blocks")
    for f in sorted(os.listdir(bdir)) if os.path.isdir(bdir) else []:
        b = load(os.path.join(bdir, f))
        if not b:
            continue
        ident = b["minecraft:block"]["description"]["identifier"]
        block_ids.add(ident)
        for face, mi in b["minecraft:block"]["components"]["minecraft:material_instances"].items():
            if mi["texture"] not in tdata:
                errors.append(f"{ident} face {face}: texture key {mi['texture']} not in terrain_texture.json")
        if f"tile.{ident}.name=" not in lang:
            errors.append(f"{ident}: no lang name")

    for key, entry in list(tdata.items()) + list(items_atlas.items()):
        png = os.path.join(rp, entry["textures"] + ".png")
        if not os.path.isfile(png):
            errors.append(f"texture file missing for {key}: {entry['textures']}.png")
            continue
        im = Image.open(png)
        if im.format != "PNG" or im.size[0] != im.size[1] or im.size[0] not in spec.ALLOWED_SIZES:
            errors.append(f"{key}: bad image {im.format} {im.size}")

    for f in os.listdir(os.path.join(bp, "items")):
        it = load(os.path.join(bp, "items", f))
        if it and it["minecraft:item"]["components"]["minecraft:icon"] not in items_atlas:
            errors.append(f"item {f}: icon not in item_texture.json")

    # Script <-> content agreement: every cc: block id the script references must exist.
    js = open(os.path.join(bp, "scripts", "course.js"), encoding="utf-8").read()
    for ref in sorted(set(re.findall(r'"(cc:[a-z_]+)"', js))):
        if ref not in block_ids and ref != "cc:maker_wand":
            errors.append(f"script references unknown block {ref}")
    if "cc:maker_wand" in js and not os.path.isfile(os.path.join(bp, "items", "maker_wand.json")):
        errors.append("script references cc:maker_wand but item file is missing")

    for e in errors:
        print(f"  FAIL {e}")
    print(f"Static validation: {'PASS' if not errors else 'FAIL'} ({len(errors)} error(s); {len(block_ids)} blocks, {len(tdata)} terrain textures)")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(run())
