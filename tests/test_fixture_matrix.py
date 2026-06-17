from __future__ import annotations

import json
import unittest
from pathlib import Path

from f1se.format.header import HEADER_SIZE
from f1se.format.save_dat import SaveDat
from f1se.format.slot import SaveSlot

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "fixtures"
MANIFEST = FIXTURE_ROOT / "fixtures.json"


def _hex_or_int(value: str | int) -> int:
    if isinstance(value, int):
        return value
    return int(value, 0)


class FixtureMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture_specs = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_is_not_empty(self) -> None:
        self.assertGreaterEqual(len(self.fixture_specs), 1)

    def test_all_declared_fixtures_parse_and_round_trip(self) -> None:
        for slot_name, expected in self.fixture_specs.items():
            with self.subTest(slot=slot_name):
                slot_path = FIXTURE_ROOT / slot_name
                save_path = slot_path / "SAVE.DAT"
                self.assertTrue(save_path.is_file(), f"missing SAVE.DAT for fixture {slot_name}")

                original = save_path.read_bytes()
                slot = SaveSlot.open(slot_path)
                sd = slot.save_dat

                self.assertEqual(len(sd.data), expected["save_dat_size"])
                self.assertEqual(sd.header.signature, "FALLOUT SAVE FILE")
                self.assertEqual(sd.header.version, expected["version"])
                self.assertEqual(sd.header.player_name, expected["player_name"])
                self.assertEqual(sd.header.current_map_file, expected["current_map_file"])
                self.assertEqual(sd.player_object.start, _hex_or_int(expected["function5_start"]))
                self.assertEqual(sd.critter_stats.start, _hex_or_int(expected["function6_start"]))
                self.assertEqual(sd.player_object.inventory_count, expected["inventory_count"])
                self.assertEqual(len(sd.player_object.inventory), expected["inventory_count"])
                self.assertEqual(sd.kill_count_count, expected["kill_count_count"])
                self.assertEqual({artifact.name for artifact in slot.artifacts}, set(expected["expected_artifacts"]))
                if "expected_artifact_kinds" in expected:
                    actual_kinds = {artifact.name: artifact.kind for artifact in slot.artifacts}
                    self.assertEqual(actual_kinds, expected["expected_artifact_kinds"])
                if "expected_raw_blocks" in expected:
                    for index, row in expected["expected_raw_blocks"].items():
                        block = sd.blocks[int(index)]
                        self.assertEqual(block.name, row["name"])
                        self.assertEqual(block.start, _hex_or_int(row["start"]))
                        self.assertEqual(block.end, _hex_or_int(row["end"]))
                if "expected_inventory" in expected:
                    for row in expected["expected_inventory"]:
                        item = sd.player_object.inventory[int(row["index"])]
                        self.assertEqual(item.start, _hex_or_int(row["offset"]))
                        self.assertEqual(item.pid, row["pid"])
                        self.assertEqual(item.size, _hex_or_int(row["size"]))
                        self.assertEqual(item.quantity, row["quantity"])
                        self.assertEqual(item.known_pid, row["known_pid"])
                        self.assertEqual(item.type_name, row["type"])

                self.assertEqual(sd.verify(), [])
                self.assertEqual(bytes(sd.data), original)
                self.assertEqual(bytes(SaveDat.from_bytes(bytes(sd.data), save_path).data), original)

                self.assertEqual(len(sd.blocks), 27)
                previous_end = HEADER_SIZE
                for expected_index, block in enumerate(sd.blocks):
                    self.assertEqual(block.index, expected_index)
                    self.assertGreaterEqual(block.start, previous_end)
                    self.assertGreaterEqual(block.end, block.start)
                    self.assertLessEqual(block.end, len(sd.data))
                    previous_end = max(previous_end, block.end)
                self.assertEqual(sd.blocks[-1].end, len(sd.data))

    def test_function_block_dicts_expose_source_handlers(self) -> None:
        slot_name = next(iter(self.fixture_specs))
        sd = SaveSlot.open(FIXTURE_ROOT / slot_name).save_dat
        first = sd.blocks[0].to_dict()
        dude = sd.blocks[5].to_dict()
        self.assertEqual(first["save_handler"], "DummyFunc")
        self.assertEqual(first["load_handler"], "PrepLoad")
        self.assertEqual(dude["save_handler"], "obj_save_dude")
        self.assertEqual(dude["load_handler"], "obj_load_dude")
        self.assertIn("writable_policy", dude)


if __name__ == "__main__":
    unittest.main()
