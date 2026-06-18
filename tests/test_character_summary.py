from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from f1se.project.character_summary import character_summary
from f1se.project.compatibility import compatibility_payload
from f1se.project.json_contracts import validate_payload_keys, validate_payload_types

ROOT = Path(__file__).resolve().parents[1]
SLOT = ROOT / "tests" / "fixtures" / "SLOT01"


class CharacterSummaryTests(unittest.TestCase):
    def run_cli_json(self, *args: str) -> dict:
        env = {"PYTHONPATH": str(ROOT / "src")}
        cp = subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        return json.loads(cp.stdout)

    def test_payload_shape(self) -> None:
        payload = character_summary(SLOT)
        self.assertEqual(payload["game_kind"], "fallout1")
        self.assertTrue(payload["read_only"])
        self.assertEqual(validate_payload_keys(payload, "character_summary"), [])
        self.assertEqual(validate_payload_types(payload, "character_summary"), [])
        self.assertIn("player_name", payload["identity"])
        self.assertIn("level", payload["progression"])
        self.assertIn("strength", payload["special"])
        self.assertIn("small_guns", payload["skills"]["skills"])
        self.assertIn("inventory_count", payload["inventory_summary"])

    def test_cli_json_contract(self) -> None:
        payload = self.run_cli_json("character-summary", str(SLOT), "--json")
        self.assertEqual(validate_payload_keys(payload, "character_summary"), [])
        self.assertEqual(validate_payload_types(payload, "character_summary"), [])
        self.assertEqual(payload["game_kind"], "fallout1")
        self.assertTrue(payload["read_only"])

    def test_cli_auto_accepts_fallout1(self) -> None:
        payload = self.run_cli_json("character-summary", str(SLOT), "--game", "auto", "--json")
        self.assertEqual(payload["game_kind"], "fallout1")
        self.assertIn("status_effects", payload)

    def test_compatibility_matrix_tracks_command(self) -> None:
        matrix = compatibility_payload()
        self.assertEqual(matrix["games"]["fallout1"]["character-summary"]["status"], "read_only")
        self.assertEqual(matrix["games"]["fallout2"]["character-summary"]["status"], "not_supported")


if __name__ == "__main__":
    unittest.main()
