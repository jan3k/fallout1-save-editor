from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from f1se.project.compatibility import compatibility_payload
from f1se.project.derived_stats import derived_stats_report
from f1se.project.json_contracts import validate_payload_keys, validate_payload_types

ROOT = Path(__file__).resolve().parents[1]
SLOT = ROOT / "tests" / "fixtures" / "SLOT01"


class DerivedStatsTests(unittest.TestCase):
    def run_cli_json(self, *args: str, expected: set[int] = {0}) -> dict:
        env = {"PYTHONPATH": str(ROOT / "src")}
        cp = subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertIn(cp.returncode, expected, cp.stderr)
        return json.loads(cp.stdout)

    def test_payload_contract(self) -> None:
        payload = derived_stats_report(SLOT)
        self.assertEqual(payload["game_kind"], "fallout1")
        self.assertTrue(payload["read_only"])
        self.assertEqual(validate_payload_keys(payload, "derived_stats"), [])
        self.assertEqual(validate_payload_types(payload, "derived_stats"), [])
        self.assertIn("strength", payload["source_special"])
        self.assertIn("player.base_hitpoints", payload["derived_stats"])
        self.assertIn("checked_count", payload["summary"])

    def test_cli_json_contract(self) -> None:
        payload = self.run_cli_json("derived-stats", str(SLOT), "--json")
        self.assertEqual(validate_payload_keys(payload, "derived_stats"), [])
        self.assertEqual(validate_payload_types(payload, "derived_stats"), [])
        self.assertEqual(payload["game_kind"], "fallout1")

    def test_cli_auto_accepts_fallout1(self) -> None:
        payload = self.run_cli_json("derived-stats", str(SLOT), "--game", "auto", "--json")
        self.assertEqual(payload["game_kind"], "fallout1")
        self.assertIn("formula_scope", payload)

    def test_compatibility_matrix_tracks_command(self) -> None:
        matrix = compatibility_payload()
        self.assertEqual(matrix["games"]["fallout1"]["derived-stats"]["status"], "read_only")
        self.assertEqual(matrix["games"]["fallout2"]["derived-stats"]["status"], "not_supported")


if __name__ == "__main__":
    unittest.main()
