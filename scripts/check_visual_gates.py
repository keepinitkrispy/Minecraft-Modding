#!/usr/bin/env python3
"""Hard visual-fidelity gate for Junk Bunch character builds.

This is intentionally separate from schema/static validation. A Bedrock character
may be perfectly valid JSON and still be visually unacceptable.

For every custom behavior-pack entity, this script requires a matching character
record and a visual-gate record bound to the exact geometry file bytes being
packaged. If geometry changes, its SHA-256 changes and the old approval stops
working automatically.

The gate does not pretend to judge art algorithmically. It enforces that the
actual model was rendered/reviewed and explicitly approved before expensive
engineering/package work can advance.

Exit 0: every packaged custom character has a current visual approval.
Exit 1: one or more characters are unapproved, stale, or incompletely evidenced.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

REQUIRED_VIEWS = ("front", "side", "back", "three_quarter")
APPROVED_STATUS = "approved"


def load_json(path: Path):
    try:
        with path.open("r", encoding="utf-8-sig") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid JSON from {path}: {exc}") from exc


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_geo_records(resource_pack: Path):
    """Yield (geometry_identifier, path) from Bedrock geometry files."""
    models = resource_pack / "models"
    if not models.is_dir():
        return
    for path in sorted(models.rglob("*.json")):
        try:
            data = load_json(path)
        except ValueError:
            continue
        geometries = data.get("minecraft:geometry")
        if isinstance(geometries, list):
            for geo in geometries:
                ident = (geo.get("description") or {}).get("identifier")
                if ident:
                    yield ident, path
        # Legacy geometry format.
        for key in data:
            if isinstance(key, str) and key.startswith("geometry."):
                yield key, path


def collect_bp_entities(behavior_pack: Path):
    entities = []
    entity_dir = behavior_pack / "entities"
    if not entity_dir.is_dir():
        return entities
    for path in sorted(entity_dir.rglob("*.json")):
        try:
            data = load_json(path)
        except ValueError:
            continue
        entity = data.get("minecraft:entity")
        if not isinstance(entity, dict):
            continue
        ident = (entity.get("description") or {}).get("identifier")
        if ident and not ident.startswith("minecraft:"):
            entities.append((ident, path))
    return entities


def check_visual_gates(repo: Path) -> list[str]:
    errors: list[str] = []
    bp = repo / "packs" / "JunkBunch_BP"
    rp = repo / "packs" / "JunkBunch_RP"
    characters = repo / "characters"
    gate_dir = characters / "visual_gates"

    if not bp.is_dir():
        return [f"missing behavior pack: {bp}"]
    if not rp.is_dir():
        return [f"missing resource pack: {rp}"]

    geo_index = {}
    for ident, path in iter_geo_records(rp):
        geo_index.setdefault(ident, []).append(path)

    for entity_id, entity_path in collect_bp_entities(bp):
        short = entity_id.split(":", 1)[-1]
        character_path = characters / f"{short}.json"
        gate_path = gate_dir / f"{short}.json"
        label = f"{entity_id} ({entity_path.relative_to(repo)})"

        if not character_path.is_file():
            errors.append(f"{label}: missing character record {character_path.relative_to(repo)}")
            continue

        try:
            character = load_json(character_path)
        except ValueError as exc:
            errors.append(f"{label}: {exc}")
            continue

        if character.get("identifier") != entity_id:
            errors.append(
                f"{label}: character record identifier is {character.get('identifier')!r}, expected {entity_id!r}"
            )

        geometry_id = (character.get("model") or {}).get("geometry")
        if not geometry_id:
            errors.append(f"{label}: character record has no model.geometry")
            continue

        matches = geo_index.get(geometry_id, [])
        if len(matches) != 1:
            errors.append(
                f"{label}: geometry {geometry_id!r} resolves to {len(matches)} files; expected exactly 1"
            )
            continue
        geometry_path = matches[0]
        actual_hash = sha256_file(geometry_path)

        if not gate_path.is_file():
            errors.append(
                f"{label}: VISUAL GATE NOT APPROVED — missing {gate_path.relative_to(repo)}"
            )
            continue

        try:
            gate = load_json(gate_path)
        except ValueError as exc:
            errors.append(f"{label}: {exc}")
            continue

        if gate.get("status") != APPROVED_STATUS:
            errors.append(
                f"{label}: VISUAL GATE = {gate.get('status')!r}, not {APPROVED_STATUS!r}"
            )
            continue

        if gate.get("entity_identifier") != entity_id:
            errors.append(
                f"{label}: gate entity_identifier {gate.get('entity_identifier')!r} does not match"
            )
        if gate.get("geometry_identifier") != geometry_id:
            errors.append(
                f"{label}: gate geometry_identifier {gate.get('geometry_identifier')!r} does not match {geometry_id!r}"
            )

        approved_hash = gate.get("geometry_sha256")
        if approved_hash != actual_hash:
            errors.append(
                f"{label}: STALE VISUAL APPROVAL — geometry changed after approval\n"
                f"    approved sha256: {approved_hash!r}\n"
                f"    current  sha256: {actual_hash}\n"
                f"    geometry: {geometry_path.relative_to(repo)}"
            )

        if gate.get("creator_approved") is not True:
            errors.append(f"{label}: creator_approved must be true")
        if gate.get("source_fidelity_checked") is not True:
            errors.append(f"{label}: source_fidelity_checked must be true")
        if gate.get("scale_checked") is not True:
            errors.append(f"{label}: scale_checked must be true")
        if gate.get("material_read_checked") is not True:
            errors.append(f"{label}: material_read_checked must be true")

        views = gate.get("views")
        if not isinstance(views, dict):
            errors.append(f"{label}: views must be an object containing {', '.join(REQUIRED_VIEWS)}")
            continue
        for view in REQUIRED_VIEWS:
            rel_path = views.get(view)
            if not isinstance(rel_path, str) or not rel_path.strip():
                errors.append(f"{label}: visual gate is missing required {view!r} render path")
                continue
            render_path = repo / rel_path
            if not render_path.is_file():
                errors.append(f"{label}: required {view!r} render does not exist: {rel_path}")

    return errors


def main() -> int:
    repo = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    print(f"Checking character visual gates in: {repo}")
    print("-" * 68)
    errors = check_visual_gates(repo)
    if errors:
        print(f"FAIL — {len(errors)} visual-gate problem(s):")
        for error in errors:
            print(f"  - {error}")
        print("\nPackaging must not proceed until the exact geometry is visually approved.")
        return 1
    print("PASS — every packaged custom character has current, hash-bound visual approval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
