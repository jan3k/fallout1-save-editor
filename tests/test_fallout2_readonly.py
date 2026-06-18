from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from f1se.format.fallout2.save_dat import Fallout2SaveDat
from f1se.format.fallout2.synthetic import build_minimal_fallout2_save
from f1se.project.compatibility import compatibility_payload
from f1se.project.game_detection import detect_game
from f1se.project.game_profile import GameKind
from f1se.project.json_contracts import validate_payload_keys, validate_payload_types

ROOT = Path(__file__).resolve().parents[1]


class Fallout2ReadOnlyTests(unittest.TestCase):
    def write_slot(self, root: Path) -> Path:
        slot = root / "SLOT01"
        slot.mkdir()
        (slot / "SAVE.DAT").write_bytes(build_minimal_fallout2_save())
        return slot

    def run_cli_json(self, *args: str) -> dict:
        env = {"PYTHONPATH": str(ROOT / "src")}
        cp = subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        return json.loads(cp.stdout)

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {"PYTHONPATH": str(ROOT / "src")}
        return subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)

    def test_detect_fallout2_from_slot_and_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slot = self.write_slot(Path(tmp))
            by_slot = detect_game(slot)
            by_file = detect_game(slot / "SAVE.DAT")
            self.assertEqual(by_slot.game_kind, GameKind.FALLOUT2)
            self.assertEqual(by_file.game_kind, GameKind.FALLOUT2)
            self.assertTrue(by_slot.read_only)
            self.assertGreaterEqual(by_slot.confidence, 60)

    def test_detect_unknown_corrupt_save(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slot = Path(tmp) / "SLOT01"
            slot.mkdir()
            (slot / "SAVE.DAT").write_bytes(b"not a fallout save")
            result = detect_game(slot)
            self.assertEqual(result.game_kind, GameKind.UNKNOWN)
            self.assertTrue(result.read_only)

    def test_readonly_parser_fields(self) -> None:
        save = Fallout2SaveDat.from_bytes(build_minimal_fallout2_save())
        self.assertEqual(save.header.player_name, "Chosen One")
        self.assertIn("player.base_strength", save.fields)
        self.assertFalse(save.fields["player.base_strength"].writable)
        self.assertEqual(save.fields["player.base_strength"].confidence, "high")
        self.assertEqual(save.fields["pc.skill_points"].value, 12)
        self.assertEqual(save.fields["pc.level"].value, 3)
        self.assertEqual(save.player_object.inventory_count, 0)

    def test_cli_payloads_match_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slot = self.write_slot(Path(tmp))
            cases = [
                ("detect", ("detect", str(slot), "--json")),
                ("fallout2_dump", ("dump", str(slot), "--game", "auto", "--json")),
                ("fallout2_fields", ("fields", str(slot), "--game", "fallout2", "--json")),
                ("fallout2_inventory", ("inventory", str(slot), "--game", "fallout2", "--json")),
                ("compatibility", ("compatibility", "--json")),
            ]
            for contract_id, args in cases:
                with self.subTest(contract_id=contract_id):
                    payload = self.run_cli_json(*args)
                    self.assertEqual(validate_payload_keys(payload, contract_id), [])
                    self.assertEqual(validate_payload_types(payload, contract_id), [])

    def test_cli_get_and_compatibility(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slot = self.write_slot(Path(tmp))
            cp = self.run_cli("get", str(slot), "pc.level", "--game", "fallout2")
            self.assertEqual(cp.returncode, 0, cp.stderr)
            self.assertEqual(cp.stdout.strip(), "3")
        matrix = compatibility_payload()
        self.assertEqual(matrix["games"]["fallout2"]["set"]["status"], "not_supported")
        self.assertEqual(matrix["games"]["fallout2"]["inventory"]["status"], "read_only")


if __name__ == "__main__":
    unittest.main()
