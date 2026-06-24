from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from f1se.format.fallout2.save_dat import Fallout2SaveDat
from f1se.format.fallout2.synthetic import build_minimal_fallout2_save
from f1se.project.fallout2_write import set_field, writable_fields_payload
from f1se.project.json_contracts import validate_payload_keys, validate_payload_types

ROOT = Path(__file__).resolve().parents[1]


class Fallout2WriteTests(unittest.TestCase):
    def write_slot(self, root: Path) -> Path:
        slot = root / "SLOT01"
        slot.mkdir()
        (slot / "SAVE.DAT").write_bytes(build_minimal_fallout2_save())
        return slot

    def run_cli_json(self, *args: str, expected: set[int] = {0}) -> dict:
        env = {"PYTHONPATH": str(ROOT / "src")}
        cp = subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertIn(cp.returncode, expected, cp.stderr)
        return json.loads(cp.stdout)

    def test_writable_fields_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slot = self.write_slot(Path(tmp))
            payload = writable_fields_payload(slot)
            self.assertEqual(validate_payload_keys(payload, "fallout2_writable_fields"), [])
            self.assertEqual(validate_payload_types(payload, "fallout2_writable_fields"), [])
            self.assertTrue(payload["fields"]["player.current_hp"]["writable"])
            self.assertFalse(payload["fields"]["inventory.0.quantity"]["writable"] if "inventory.0.quantity" in payload["fields"] else False)

    def test_dry_run_set_does_not_modify_save(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slot = self.write_slot(Path(tmp))
            before = Fallout2SaveDat.from_path(slot / "SAVE.DAT").sha256
            payload = set_field(slot, "player.current_hp", 44)
            after = Fallout2SaveDat.from_path(slot / "SAVE.DAT").sha256
            self.assertEqual(validate_payload_keys(payload, "fallout2_set"), [])
            self.assertEqual(validate_payload_types(payload, "fallout2_set"), [])
            self.assertFalse(payload["written"])
            self.assertTrue(payload["write_required"])
            self.assertEqual(before, after)

    def test_write_set_modifies_save_and_creates_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slot = self.write_slot(Path(tmp))
            payload = set_field(slot, "player.current_hp", 45, write=True)
            save = Fallout2SaveDat.from_path(slot / "SAVE.DAT")
            self.assertTrue(payload["written"])
            self.assertFalse(payload["write_required"])
            self.assertEqual(save.fields["player.current_hp"].value, 45)
            self.assertTrue(Path(payload["backup_path"]).is_dir())

    def test_unsupported_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slot = self.write_slot(Path(tmp))
            with self.assertRaises(ValueError):
                set_field(slot, "header.player_name", 1)

    def test_cli_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slot = self.write_slot(Path(tmp))
            payload = self.run_cli_json("set", str(slot), "player.current_hp", "46", "--game", "fallout2", "--json")
            self.assertFalse(payload["written"])
            self.assertEqual(payload["diff"]["new_value"], 46)

    def test_cli_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slot = self.write_slot(Path(tmp))
            payload = self.run_cli_json("set", str(slot), "player.current_hp", "47", "--game", "fallout2", "--write", "--json")
            self.assertTrue(payload["written"])
            save = Fallout2SaveDat.from_path(slot / "SAVE.DAT")
            self.assertEqual(save.fields["player.current_hp"].value, 47)


if __name__ == "__main__":
    unittest.main()
