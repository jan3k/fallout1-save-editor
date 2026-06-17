from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from f1se.format.save_dat import SaveDat
from f1se.format.slot import SaveSlot
from f1se.io.backup import backup_slot

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "SLOT01"
SAVE = FIXTURE / "SAVE.DAT"


class SaveDatTests(unittest.TestCase):
    def parse(self) -> SaveDat:
        return SaveDat.from_path(SAVE)

    def test_parse_save_dat_header(self) -> None:
        sd = self.parse()
        self.assertEqual(sd.header.signature, "FALLOUT SAVE FILE")
        self.assertEqual(sd.header.version, "1.02R")
        self.assertEqual(sd.header.player_name, "yay")
        self.assertEqual(sd.header.current_map_file, "V13ENT.sav")
        self.assertEqual(sd.header.real_day, 17)
        self.assertEqual(sd.header.real_month, 6)
        self.assertEqual(sd.header.real_year, 2026)

    def test_parse_function_5_player_object(self) -> None:
        sd = self.parse()
        p = sd.player_object
        self.assertEqual(p.start, 0x88CC)
        self.assertEqual(p.coordinates, 19090)
        self.assertEqual(p.facing, 2)
        self.assertEqual(p.fid, 0x0100000B)
        self.assertEqual(p.map_level, 0)
        self.assertEqual(p.inventory_count, 5)
        self.assertEqual(p.current_hp, 28)
        self.assertEqual(p.radiation, 0)
        self.assertEqual(p.poison, 0)

    def test_parse_function_5_inventory_dynamic(self) -> None:
        sd = self.parse()
        items = sd.player_object.inventory
        self.assertEqual(len(items), 5)
        self.assertEqual([(i.start, i.quantity, i.pid, i.type_name) for i in items], [
            (0x894C, 1, 4, "weapon"),
            (0x89B0, 1, 8, "weapon"),
            (0x8A14, 3, 29, "ammo"),
            (0x8A74, 6, 40, "drug"),
            (0x8AD0, 2, 79, "weapon"),
        ])
        self.assertEqual([i.size for i in items], [0x64, 0x64, 0x60, 0x5C, 0x64])

    def test_parse_function_6_player_stats(self) -> None:
        sd = self.parse()
        self.assertEqual(sd.critter_stats.start, 0x8B38)
        self.assertEqual(sd.critter_stats.end, 0x8CB0)
        # The uploaded fixture currently has already-maxed SPECIAL values.
        self.assertEqual([sd.fields[f"player.base_{s}"].value for s in ["strength", "perception", "endurance", "charisma", "intelligence", "agility", "luck"]], [10, 10, 10, 10, 10, 10, 10])
        self.assertEqual(sd.fields["player.base_hitpoints"].value, 28)
        self.assertEqual(sd.fields["player.base_carry_weight"].value, 100)
        self.assertEqual([sd.fields[f"skills.{name}"].value for name in sd.critter_stats.skills.keys()], [0] * 18)

    def test_roundtrip_no_changes_is_byte_identical(self) -> None:
        original = SAVE.read_bytes()
        sd = self.parse()
        self.assertEqual(bytes(sd.data), original)
        self.assertEqual(SaveDat.from_bytes(bytes(sd.data)).data, sd.data)

    def test_set_special_strength_changes_only_4_bytes(self) -> None:
        sd = self.parse()
        before = bytes(sd.data)
        diffs = sd.set_field("player.base_strength", 9)
        after = bytes(sd.data)
        changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0].offset, 0x8B40)
        self.assertEqual(changed, [0x8B43])
        self.assertEqual(after[0x8B40:0x8B44], b"\x00\x00\x00\x09")

    def test_set_all_special_to_10(self) -> None:
        sd = self.parse()
        # First push down, then patch back up to prove all fields write BE i32.
        for stat in ["strength", "perception", "endurance", "charisma", "intelligence", "agility", "luck"]:
            sd.set_field(f"player.base_{stat}", 9)
        patch = {f"player.base_{stat}": 10 for stat in ["strength", "perception", "endurance", "charisma", "intelligence", "agility", "luck"]}
        diffs = sd.apply_patch(patch)
        self.assertEqual(len(diffs), 7)
        self.assertEqual([sd.fields[f"player.base_{stat}"].value for stat in ["strength", "perception", "endurance", "charisma", "intelligence", "agility", "luck"]], [10] * 7)

    def test_validate_big_endian_write(self) -> None:
        sd = self.parse()
        sd.set_field("pc.experience", 190000)
        off = sd.fields["pc.experience"].abs_offset
        self.assertEqual(sd.data[off:off + 4], (190000).to_bytes(4, "big", signed=True))

    def test_reject_invalid_special_without_allow_out_of_range(self) -> None:
        sd = self.parse()
        with self.assertRaises(ValueError):
            sd.set_field("player.base_strength", 99)
        diffs = sd.set_field("player.base_strength", 99, allow_out_of_range=True)
        self.assertEqual(len(diffs), 1)

    def test_backup_created_before_write(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            slot = Path(td) / "SLOT01"
            shutil.copytree(FIXTURE, slot)
            dst = backup_slot(slot)
            self.assertTrue((dst / "SAVE.DAT").is_file())
            self.assertEqual((dst / "SAVE.DAT").read_bytes(), (slot / "SAVE.DAT").read_bytes())

    def test_dry_run_does_not_modify_files(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            slot = Path(td) / "SLOT01"
            shutil.copytree(FIXTURE, slot)
            before = (slot / "SAVE.DAT").read_bytes()
            env = {"PYTHONPATH": str(ROOT / "src")}
            cp = subprocess.run([sys.executable, "-m", "f1se", "set", str(slot), "player.base_strength", "9", "--dry-run"], cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            self.assertEqual((slot / "SAVE.DAT").read_bytes(), before)
            self.assertFalse((slot / ".f1se-backups").exists())

    def test_raw_write_requires_experimental(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            slot = Path(td) / "SLOT01"
            shutil.copytree(FIXTURE, slot)
            env = {"PYTHONPATH": str(ROOT / "src")}
            cp = subprocess.run([sys.executable, "-m", "f1se", "raw-write", str(slot), "SAVE.DAT:0x8B40:00000009", "--dry-run"], cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertNotEqual(cp.returncode, 0)
            self.assertIn("requires --experimental", cp.stderr)

    def test_unknown_fields_preserved(self) -> None:
        sd = self.parse()
        before = bytes(sd.data)
        sd.set_field("player.base_strength", 9)
        for block in sd.blocks:
            if block.index != 6:
                self.assertEqual(sd.data[block.start:block.end], before[block.start:block.end])


    def test_kill_count_fields_detected_and_editable(self) -> None:
        sd = self.parse()
        fields = [name for name in sd.fields if name.startswith("kill_counts.")]
        self.assertEqual(sd.kill_count_count, 15)
        self.assertEqual(len(fields), 15)
        first = min(fields, key=lambda name: sd.fields[name].abs_offset)
        self.assertEqual(sd.fields[first].abs_offset, 0x8CB0)
        before = bytes(sd.data)
        diffs = sd.set_field(first, 1)
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0].offset, 0x8CB0)
        self.assertEqual(sd.data[0x8CB0:0x8CB4], b"\x00\x00\x00\x01")
        self.assertEqual(sd.data[:0x8CB0], before[:0x8CB0])
        self.assertEqual(sd.data[0x8CB4:], before[0x8CB4:])

    def test_effective_special_uses_source_trait_static_adjustments(self) -> None:
        sd = self.parse()
        # Fixture traits are Bloody Mess and Jinxed; neither changes static SPECIAL.
        effective = sd.effective_special()
        self.assertEqual(effective["strength"]["effective_static"], 10)
        sd.set_field("traits.trait_0", 15)  # Gifted: +1 to all primary stats in fallout1-ce trait_adjust_stat.
        effective = sd.effective_special()
        self.assertEqual(effective["strength"]["static_trait"], 1)
        self.assertIn("gifted", "\n".join(sd.trait_effect_notes()))

    def test_preset_patches_are_conservative_field_patches(self) -> None:
        sd = self.parse()
        heal = sd.preset_patch("heal")
        self.assertEqual(heal["player.radiation"], 0)
        self.assertEqual(heal["player.poison"], 0)
        self.assertIn("player.current_hp", heal)
        max_special = sd.preset_patch("max-special")
        self.assertEqual(len(max_special), 7)
        self.assertTrue(all(value == 10 for value in max_special.values()))

    def test_slot_artifacts_fingerprinted(self) -> None:
        slot = SaveSlot.open(FIXTURE)
        self.assertEqual({a.name for a in slot.artifacts}, {"AUTOMAP.SAV", "V13ENT.SAV"})

    def test_dump_json_contains_fields(self) -> None:
        sd = self.parse()
        doc = sd.to_dict()
        self.assertIn("player.base_strength", doc["fields"])
        self.assertIn("blocks", doc)
        self.assertEqual(len(doc["blocks"]), 27)


if __name__ == "__main__":
    unittest.main()
