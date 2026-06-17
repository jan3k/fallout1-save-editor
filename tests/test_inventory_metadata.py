from __future__ import annotations

import unittest
from pathlib import Path

from f1se.format.save_dat import SaveDat
from f1se.io.endian import put_i32be
from f1se.schema.items import get_item_meta, item_size_options

ROOT = Path(__file__).resolve().parents[1]
SAVE = ROOT / "tests" / "fixtures" / "SLOT01" / "SAVE.DAT"
UNKNOWN_TEST_ITEM_ID = 123456


class InventoryMetadataTests(unittest.TestCase):
    def parse(self) -> SaveDat:
        return SaveDat.from_path(SAVE)

    def test_known_fixture_items_keep_offsets_sizes_and_metadata(self) -> None:
        sd = self.parse()
        items = sd.player_object.inventory
        self.assertEqual([(i.start, i.quantity, i.pid, i.type_name) for i in items], [
            (0x894C, 1, 4, "weapon"),
            (0x89B0, 1, 8, "weapon"),
            (0x8A14, 3, 29, "ammo"),
            (0x8A74, 6, 40, "drug"),
            (0x8AD0, 2, 79, "weapon"),
        ])
        self.assertEqual([i.size for i in items], [0x64, 0x64, 0x60, 0x5C, 0x64])
        self.assertTrue(all(item.known_pid for item in items))
        self.assertTrue(all(item.size_source == "known_pid" for item in items))
        self.assertTrue(all(item.confidence == "high" for item in items))
        self.assertTrue(all(item.item_meta is not None for item in items))

    def test_inventory_item_to_dict_contains_metadata_fields(self) -> None:
        item = self.parse().player_object.inventory[0]
        doc = item.to_dict()
        self.assertIn("known_pid", doc)
        self.assertIn("size_source", doc)
        self.assertIn("confidence", doc)
        self.assertIn("item_meta", doc)
        self.assertEqual(doc["known_pid"], True)
        self.assertEqual(doc["item_meta"]["pid"], 4)

    def test_unlisted_item_id_still_uses_heuristic_path(self) -> None:
        sd = self.parse()
        data = bytearray(sd.data)
        first = sd.player_object.inventory[0]
        put_i32be(data, first.start + 0x30, UNKNOWN_TEST_ITEM_ID)
        mutated = SaveDat.from_bytes(bytes(data), SAVE)
        item = mutated.player_object.inventory[0]
        self.assertEqual(item.pid, UNKNOWN_TEST_ITEM_ID)
        self.assertFalse(item.known_pid)
        self.assertEqual(item.size_source, "heuristic")
        self.assertEqual(item.confidence, "medium")
        self.assertEqual(item.size, 0x64)

    def test_item_metadata_helpers_preserve_known_and_unknown_size_options(self) -> None:
        meta = get_item_meta(40)
        self.assertIsNotNone(meta)
        assert meta is not None
        self.assertEqual(meta.name, "Stimpak")
        self.assertEqual(item_size_options(40), [0x5C])
        self.assertEqual(item_size_options(UNKNOWN_TEST_ITEM_ID), [0x64, 0x60, 0x5C])


if __name__ == "__main__":
    unittest.main()
