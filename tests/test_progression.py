from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from f1se.project.compatibility import compatibility_payload
from f1se.project.json_contracts import validate_payload_keys, validate_payload_types
from f1se.project.progression import next_perk_level, perk_interval_for_traits, progression_summary, xp_threshold_for_level

ROOT = Path(__file__).resolve().parents[1]
SLOT = ROOT / "tests" / "fixtures" / "SLOT01"


class ProgressionTests(unittest.TestCase):
    def run_cli_json(self, *args: str, expected: set[int] = {0}) -> dict:
        env = {"PYTHONPATH": str(ROOT / "src")}
        cp = subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertIn(cp.returncode, expected, cp.stderr)
        return json.loads(cp.stdout)

    def test_xp_threshold_formula(self) -> None:
        self.assertEqual(xp_threshold_for_level(1), 0)
        self.assertEqual(xp_threshold_for_level(2), 1000)
        self.assertEqual(xp_threshold_for_level(3), 3000)
        self.assertEqual(xp_threshold_for_level(4), 6000)
        self.assertEqual(xp_threshold_for_level(21), 210000)

    def test_perk_cadence(self) -> None:
        self.assertEqual(perk_interval_for_traits([]), 3)
        self.assertEqual(perk_interval_for_traits(["skilled"]), 4)
        self.assertEqual(next_perk_level(1, 3), 3)
        self.assertEqual(next_perk_level(3, 3), 6)
        self.assertEqual(next_perk_level(20, 3), 21)
        self.assertIsNone(next_perk_level(21, 3))

    def test_payload_contract(self) -> None:
        payload = progression_summary(SLOT)
        self.assertEqual(payload["game_kind"], "fallout1")
        self.assertTrue(payload["read_only"])
        self.assertEqual(validate_payload_keys(payload, "progression"), [])
        self.assertEqual(validate_payload_types(payload, "progression"), [])
        self.assertIn("current", payload["level"])
        self.assertIn("xp_to_next", payload["level"])
        self.assertIn("next_perk_level", payload["perk_cadence"])

    def test_cli_json_contract(self) -> None:
        payload = self.run_cli_json("progression", str(SLOT), "--json")
        self.assertEqual(validate_payload_keys(payload, "progression"), [])
        self.assertEqual(validate_payload_types(payload, "progression"), [])
        self.assertEqual(payload["game_kind"], "fallout1")

    def test_cli_auto_accepts_fallout1(self) -> None:
        payload = self.run_cli_json("progression", str(SLOT), "--game", "auto", "--json")
        self.assertEqual(payload["game_kind"], "fallout1")
        self.assertIn("perk_cadence", payload)

    def test_fallout2_mode_is_unsupported(self) -> None:
        payload = self.run_cli_json("progression", str(SLOT), "--game", "fallout2", "--json", expected={2})
        self.assertFalse(payload["supported"])
        self.assertTrue(payload["read_only"])

    def test_compatibility_matrix_tracks_command(self) -> None:
        matrix = compatibility_payload()
        self.assertEqual(matrix["games"]["fallout1"]["progression"]["status"], "read_only")
        self.assertEqual(matrix["games"]["fallout2"]["progression"]["status"], "not_supported")


if __name__ == "__main__":
    unittest.main()
