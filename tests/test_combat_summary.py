from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from f1se.project.combat import combat_summary
from f1se.project.compatibility import compatibility_payload
from f1se.project.json_contracts import validate_payload_keys, validate_payload_types

ROOT = Path(__file__).resolve().parents[1]
SLOT = ROOT / "tests" / "fixtures" / "SLOT01"


class CombatSummaryTests(unittest.TestCase):
    def run_cli_json(self, *args: str) -> dict:
        env = {"PYTHONPATH": str(ROOT / "src")}
        cp = subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        return json.loads(cp.stdout)

    def test_payload_contract(self) -> None:
        payload = combat_summary(SLOT)
        self.assertEqual(payload["game_kind"], "fallout1")
        self.assertTrue(payload["read_only"])
        self.assertEqual(validate_payload_keys(payload, "combat_summary"), [])
        self.assertEqual(validate_payload_types(payload, "combat_summary"), [])
        self.assertIn("current", payload["hp"])
        self.assertIn("radiation", payload["resistances"])
        self.assertIn("crippled_body_parts", payload["status_effects"])
        self.assertIn("player.current_hp", payload["fields"])

    def test_cli_json_contract(self) -> None:
        payload = self.run_cli_json("combat-summary", str(SLOT), "--json")
        self.assertEqual(validate_payload_keys(payload, "combat_summary"), [])
        self.assertEqual(validate_payload_types(payload, "combat_summary"), [])
        self.assertEqual(payload["game_kind"], "fallout1")

    def test_cli_auto_accepts_fallout1(self) -> None:
        payload = self.run_cli_json("combat-summary", str(SLOT), "--game", "auto", "--json")
        self.assertEqual(payload["game_kind"], "fallout1")
        self.assertIn("action_points", payload)

    def test_compatibility_matrix_tracks_command(self) -> None:
        matrix = compatibility_payload()
        self.assertEqual(matrix["games"]["fallout1"]["combat-summary"]["status"], "read_only")
        self.assertEqual(matrix["games"]["fallout2"]["combat-summary"]["status"], "not_supported")


if __name__ == "__main__":
    unittest.main()
