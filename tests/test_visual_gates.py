#!/usr/bin/env python3

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "scripts" / "check_visual_gates.py"
spec = importlib.util.spec_from_file_location("check_visual_gates", MODULE_PATH)
visual_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(visual_gate)


class VisualGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        (self.repo / "packs/JunkBunch_BP/entities").mkdir(parents=True)
        (self.repo / "packs/JunkBunch_RP/models/entity").mkdir(parents=True)
        (self.repo / "characters/visual_gates").mkdir(parents=True)

        self.entity = {
            "format_version": "1.20.50",
            "minecraft:entity": {
                "description": {"identifier": "junkbunch:test_character"}
            },
        }
        self.geometry = {
            "format_version": "1.16.0",
            "minecraft:geometry": [
                {
                    "description": {"identifier": "geometry.test_character.main"},
                    "bones": [],
                }
            ],
        }
        self.character = {
            "name": "Test Character",
            "identifier": "junkbunch:test_character",
            "model": {"geometry": "geometry.test_character.main"},
        }

        self.entity_path = self.repo / "packs/JunkBunch_BP/entities/test_character.json"
        self.geometry_path = self.repo / "packs/JunkBunch_RP/models/entity/test_character.geo.json"
        self.character_path = self.repo / "characters/test_character.json"

        self.entity_path.write_text(json.dumps(self.entity), encoding="utf-8")
        self.geometry_path.write_text(json.dumps(self.geometry), encoding="utf-8")
        self.character_path.write_text(json.dumps(self.character), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def write_approved_gate(self):
        views = {}
        for view in visual_gate.REQUIRED_VIEWS:
            path = self.repo / f"characters/test_character_{view}.png"
            path.write_bytes(b"render evidence")
            views[view] = str(path.relative_to(self.repo))

        gate = {
            "status": "approved",
            "entity_identifier": "junkbunch:test_character",
            "geometry_identifier": "geometry.test_character.main",
            "geometry_sha256": visual_gate.sha256_file(self.geometry_path),
            "creator_approved": True,
            "source_fidelity_checked": True,
            "scale_checked": True,
            "material_read_checked": True,
            "views": views,
        }
        gate_path = self.repo / "characters/visual_gates/test_character.json"
        gate_path.write_text(json.dumps(gate), encoding="utf-8")

    def test_missing_approval_blocks_build(self):
        errors = visual_gate.check_visual_gates(self.repo)
        self.assertTrue(errors)
        self.assertTrue(any("VISUAL GATE NOT APPROVED" in error for error in errors))

    def test_exact_approved_geometry_passes(self):
        self.write_approved_gate()
        self.assertEqual([], visual_gate.check_visual_gates(self.repo))

    def test_geometry_change_invalidates_old_approval(self):
        self.write_approved_gate()
        data = json.loads(self.geometry_path.read_text(encoding="utf-8"))
        data["minecraft:geometry"][0]["description"]["visible_bounds_width"] = 3
        self.geometry_path.write_text(json.dumps(data), encoding="utf-8")

        errors = visual_gate.check_visual_gates(self.repo)
        self.assertTrue(any("STALE VISUAL APPROVAL" in error for error in errors))

    def test_missing_required_render_blocks_build(self):
        self.write_approved_gate()
        (self.repo / "characters/test_character_side.png").unlink()
        errors = visual_gate.check_visual_gates(self.repo)
        self.assertTrue(any("required 'side' render does not exist" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
