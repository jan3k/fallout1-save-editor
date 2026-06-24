from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from f1se.format.fallout2.save_dat import Fallout2SaveDat
from f1se.format.fallout2.synthetic import build_minimal_fallout2_save
from f1se.format.slot import SaveSlot
from f1se.project.json_contracts import validate_payload_keys, validate_payload_types
from f1se.project.skill_write import normalize_skill_name, set_skill
from f1se.project.special_write import normalize_special_name, set_special

ROOT = Path(__file__).resolve().parents[1]
F1_SLOT = ROOT / "tests" / "fixtures" / "SLOT01"


class SpecialSkillWriteTests(unittest.TestCase):
    def copy_f1_slot(self, root: Path) -> Path:
        slot = root / "SLOT01"
        shutil.copytree(F1_SLOT, slot)
        return slot

    def write_f2_slot(self, root: Path) -> Path:
        slot = root / "SLOT02"
        slot.mkdir()
        (slot / "SAVE.DAT").write_bytes(build_minimal_fallout2_save())
        return slot

    def run_cli_json(self, *args: str) -> dict:
        env = {"PYTHONPATH": str(ROOT / "src")}
        cp = subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        return json.loads(cp.stdout)

    def test_aliases(self) -> None:
        self.assertEqual(normalize_special_name("str"), "strength")
        self.assertEqual(normalize_skill_name("retoryka"), "speech")
        self.assertEqual(normalize_skill_name("retoryki"), "speech")

    def test_f1_skill_retoryka_dry_run_and_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slot = self.copy_f1_slot(Path(tmp))
            before = SaveSlot.open(slot).save_dat.fields["skills.speech"].value
            dry = set_skill(slot, "retoryka", 77)
            self.assertEqual(validate_payload_keys(dry, "skill_set"), [])
            self.assertEqual(validate_payload_types(dry, "skill_set"), [])
            self.assertFalse(dry["written"])
            self.assertEqual(SaveSlot.open(slot).save_dat.fields["skills.speech"].value, before)
            written = set_skill(slot, "retoryka", 78, write=True)
            self.assertTrue(written["written"])
            self.assertEqual(SaveSlot.open(slot).save_dat.fields["skills.speech"].value, 78)
            self.assertTrue(Path(written["backup_path"]).is_dir())

    def test_f1_special_set_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slot = self.copy_f1_slot(Path(tmp))
            payload = set_special(slot, "str", 9, write=True)
            self.assertEqual(validate_payload_keys(payload, "special_set"), [])
            self.assertEqual(validate_payload_types(payload, "special_set"), [])
            self.assertTrue(payload["written"])
            self.assertEqual(SaveSlot.open(slot).save_dat.fields["player.base_strength"].value, 9)

    def test_f2_skill_retoryka_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slot = self.write_f2_slot(Path(tmp))
            dry = set_skill(slot, "retoryka", 88, game="fallout2")
            self.assertEqual(validate_payload_keys(dry, "skill_set"), [])
            self.assertEqual(validate_payload_types(dry, "skill_set"), [])
            self.assertFalse(dry["written"])
            written = set_skill(slot, "retoryka", 89, game="fallout2", write=True)
            self.assertTrue(written["written"])
            save = Fallout2SaveDat.from_path(slot / "SAVE.DAT")
            self.assertEqual(save.fields["skills.speech"].value, 89)

    def test_cli_skill_set_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slot = self.write_f2_slot(Path(tmp))
            payload = self.run_cli_json("skill-set", str(slot), "retoryka", "90", "--game", "fallout2", "--json")
            self.assertEqual(validate_payload_keys(payload, "skill_set"), [])
            self.assertEqual(validate_payload_types(payload, "skill_set"), [])
            self.assertFalse(payload["written"])
            self.assertEqual(payload["skill"], "speech")


if __name__ == "__main__":
    unittest.main()
