#!/usr/bin/env python3
"""Build a Bedrock .mcworld that physically contains Rich & Shorty's BP/RP.

The source world must already be a valid Bedrock world (level.dat + db/). CI
creates that source using the current official Bedrock Dedicated Server without
loading the experimental Rich & Shorty pack. This script then embeds the tested
behavior/resource packs and writes the world-level pack references.

Realm is only the courier for this artifact. The embedded pack still requires
Beta APIs when the downloaded world is played locally.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


def read_manifest(pack: Path) -> tuple[str, list[int]]:
    manifest_path = pack / "manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"missing manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    header = manifest.get("header", {})
    uuid = header.get("uuid")
    version = header.get("version")
    if not isinstance(uuid, str) or not uuid:
        raise SystemExit(f"invalid pack uuid in {manifest_path}")
    if not (isinstance(version, list) and len(version) == 3 and all(isinstance(v, int) for v in version)):
        raise SystemExit(f"invalid pack version in {manifest_path}")
    return uuid, version


def safe_copy_pack(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def zip_world(root: Path, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            zf.write(path, path.relative_to(root).as_posix())


def validate_archive(out: Path, bp_uuid: str, bp_ver: list[int], rp_uuid: str, rp_ver: list[int]) -> None:
    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())
        required = {
            "level.dat",
            "world_behavior_packs.json",
            "world_resource_packs.json",
            "behavior_packs/RSBP/manifest.json",
            "resource_packs/RSRP/manifest.json",
        }
        missing = sorted(required - names)
        if missing:
            raise SystemExit(f"carrier archive missing required files: {missing}")
        if not any(n.startswith("db/") for n in names):
            raise SystemExit("carrier archive has no Bedrock db/ contents")
        bad = zf.testzip()
        if bad:
            raise SystemExit(f"carrier archive CRC failure at {bad}")

        world_bp = json.loads(zf.read("world_behavior_packs.json"))
        world_rp = json.loads(zf.read("world_resource_packs.json"))
        if world_bp != [{"pack_id": bp_uuid, "version": bp_ver}]:
            raise SystemExit("world_behavior_packs.json does not exactly match embedded BP")
        if world_rp != [{"pack_id": rp_uuid, "version": rp_ver}]:
            raise SystemExit("world_resource_packs.json does not exactly match embedded RP")

        embedded_bp = json.loads(zf.read("behavior_packs/RSBP/manifest.json"))
        embedded_rp = json.loads(zf.read("resource_packs/RSRP/manifest.json"))
        if embedded_bp.get("header", {}).get("uuid") != bp_uuid:
            raise SystemExit("embedded BP UUID mismatch")
        if embedded_rp.get("header", {}).get("uuid") != rp_uuid:
            raise SystemExit("embedded RP UUID mismatch")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True, type=Path)
    ap.add_argument("--bp", required=True, type=Path)
    ap.add_argument("--rp", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--name", required=True)
    args = ap.parse_args()

    source_world = args.world.resolve()
    bp = args.bp.resolve()
    rp = args.rp.resolve()

    if not (source_world / "level.dat").is_file():
        raise SystemExit(f"source world missing level.dat: {source_world}")
    if not (source_world / "db").is_dir():
        raise SystemExit(f"source world missing db/: {source_world}")

    bp_uuid, bp_ver = read_manifest(bp)
    rp_uuid, rp_ver = read_manifest(rp)

    with tempfile.TemporaryDirectory(prefix="rich-shorty-carrier-") as tmp:
        carrier = Path(tmp) / "world"
        shutil.copytree(source_world, carrier)

        # Xbox/console world-template guidance recommends pack folder names <=10
        # characters. Keep them deliberately tiny even though this is .mcworld.
        bp_dir = carrier / "behavior_packs" / "RSBP"
        rp_dir = carrier / "resource_packs" / "RSRP"
        bp_dir.parent.mkdir(parents=True, exist_ok=True)
        rp_dir.parent.mkdir(parents=True, exist_ok=True)
        safe_copy_pack(bp, bp_dir)
        safe_copy_pack(rp, rp_dir)

        write_json(carrier / "world_behavior_packs.json", [{"pack_id": bp_uuid, "version": bp_ver}])
        write_json(carrier / "world_resource_packs.json", [{"pack_id": rp_uuid, "version": rp_ver}])
        (carrier / "levelname.txt").write_text(args.name + "\n", encoding="utf-8")

        # Small provenance file is harmless world payload and lets us inspect an
        # exported/downloaded carrier later without guessing which build it held.
        write_json(
            carrier / "rich_shorty_carrier.json",
            {
                "name": args.name,
                "behavior_pack": {"uuid": bp_uuid, "version": bp_ver, "folder": "RSBP"},
                "resource_pack": {"uuid": rp_uuid, "version": rp_ver, "folder": "RSRP"},
                "purpose": "embedded-pack Realm transfer carrier; local play requires Beta APIs",
            },
        )

        zip_world(carrier, args.out)

    validate_archive(args.out, bp_uuid, bp_ver, rp_uuid, rp_ver)
    digest = hashlib.sha256(args.out.read_bytes()).hexdigest()
    print(json.dumps({
        "status": "PASS",
        "mcworld": str(args.out),
        "bytes": args.out.stat().st_size,
        "sha256": digest,
        "bp_uuid": bp_uuid,
        "bp_version": bp_ver,
        "rp_uuid": rp_uuid,
        "rp_version": rp_ver,
    }, indent=2))


if __name__ == "__main__":
    main()
