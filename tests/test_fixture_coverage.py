from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from f1se.project.fixture_coverage import fixture_coverage
from f1se.project.fixture_doctor import fixture_doctor
from f1se.project.json_contracts import validate_payload_keys

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class FixtureCoverageTests(unittest.TestCase):
    def run_cli_json(self, *args: str, expected: set[int] = {0}) -> dict:
        env = {"PYTHONPATH": str(ROOT / "src")}
        cp = subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertIn(cp.returncode, expected, cp.stderr)
        return json.loads(cp.stdout)

    def test_fixture_coverage_payload(self) -> None:
        payload = fixture_coverage(FIXTURES)
        self.assertTrue(payload["read_only"])
        self.assertIn("expansion_plan", payload)
        self.assertIn("missing_categories", payload)
        self.assertEqual(validate_payload_keys(payload, "fixture_coverage"), [])
        self.assertGreaterEqual(payload["summary"]["recommended_count"], 10)

    def test_fixture_coverage_cli_json(self) -> None:
        payload = self.run_cli_json("fixture-coverage", str(FIXTURES), "--json")
        self.assertEqual(validate_payload_keys(payload, "fixture_coverage"), [])
        self.assertIn("baseline", payload["coverage_categories"])

    def test_fixture_doctor_findings_have_severity(self) -> None:
        payload = fixture_doctor(FIXTURES)
        self.assertIn("findings", payload)
        for row in payload["findings"]:
            self.assertIn(row["severity"], {"error", "warning", "info"})
            self.assertIn("code", row)
            self.assertIn("message", row)
        self.assertEqual(validate_payload_keys(payload, "fixture_doctor"), [])


if __name__ == "__main__":
    unittest.main()
