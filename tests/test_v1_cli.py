from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from f1se.project.json_contracts import validate_payload_keys

ROOT = Path(__file__).resolve().parents[1]
SLOT = ROOT / "tests" / "fixtures" / "SLOT01"
FIXTURES = ROOT / "tests" / "fixtures"


class V1CliTests(unittest.TestCase):
    def run_cli_json(self, *args: str, expected: set[int] = {0}) -> dict:
        env = {"PYTHONPATH": str(ROOT / "src")}
        cp = subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertIn(cp.returncode, expected, cp.stderr)
        return json.loads(cp.stdout)

    def test_new_read_only_commands(self) -> None:
        cases = [
            ("smoke", ("smoke", "--json"), None),
            ("fixture_doctor", ("fixture-doctor", str(FIXTURES), "--json"), None),
            ("save_diff", ("diff", str(SLOT), str(SLOT), "--json"), None),
        ]
        for contract_id, args, expected in cases:
            with self.subTest(args=args):
                payload = self.run_cli_json(*args)
                self.assertEqual(validate_payload_keys(payload, contract_id), [])

    def test_release_audit_strict_command(self) -> None:
        payload = self.run_cli_json("release-audit", "--strict", "--json", expected={0, 1})
        self.assertTrue(payload["strict"])
        self.assertIn(payload["status"], {"OK", "WARN", "FAIL"})

    def test_command_index_contains_new_diagnostics(self) -> None:
        payload = self.run_cli_json("commands", "--json")
        names = {row["name"] for row in payload["commands"]}
        self.assertIn("smoke", names)
        self.assertIn("fixture-doctor", names)
        self.assertIn("diff", names)


if __name__ == "__main__":
    unittest.main()
