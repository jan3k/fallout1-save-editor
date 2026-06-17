from __future__ import annotations

import unittest
from pathlib import Path

from f1se.format.map_objects import scan_map_objects
from f1se.format.map_sav import parse_map_sav
from f1se.format.slot import SaveSlot

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "SLOT01"
MAP_FILE = FIXTURE / "V13ENT.SAV"
SAVE = FIXTURE / "SAVE.DAT"


class MapObjectScanTests(unittest.TestCase):
    def test_scan_map_objects_is_read_only_and_serializable(self) -> None:
        before_map = MAP_FILE.read_bytes()
        before_save = SAVE.read_bytes()
        scan = scan_map_objects(MAP_FILE)
        doc = scan.to_dict()
        self.assertEqual(doc["file_name"], "V13ENT.SAV")
        self.assertGreater(doc["size"], 0)
        self.assertEqual(len(doc["sha256"]), 64)
        self.assertEqual(doc["parser_status"], "heuristic-read-only")
        self.assertIn("candidate_count", doc)
        self.assertIn("candidates", doc)
        self.assertEqual(MAP_FILE.read_bytes(), before_map)
        self.assertEqual(SAVE.read_bytes(), before_save)

    def test_map_sav_to_dict_includes_object_scan(self) -> None:
        info = parse_map_sav(MAP_FILE)
        doc = info.to_dict()
        self.assertEqual(doc["name"], "V13ENT.SAV")
        self.assertEqual(doc["parser_status"], "raw-fingerprint")
        self.assertIsNotNone(doc["object_scan"])
        self.assertEqual(doc["object_scan"]["parser_status"], "heuristic-read-only")
        self.assertIn("candidates", doc["object_scan"])

    def test_slot_artifact_details_include_object_scan(self) -> None:
        slot = SaveSlot.open(FIXTURE)
        artifacts = {artifact.name: artifact.to_dict() for artifact in slot.artifacts}
        self.assertEqual(artifacts["V13ENT.SAV"]["kind"], "MAP_SAV")
        self.assertIn("object_scan", artifacts["V13ENT.SAV"]["details"])


if __name__ == "__main__":
    unittest.main()
