from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "fixtures"


class FixtureStatusTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {"PYTHONPATH": str(ROOT / "src")}
        return subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)

    def test_fixture_plan_json(self) -> None:
        cp = self.run_cli("fixture-plan", "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        names = [row["name"] for row in payload["recommended_fixtures"]]
        self.assertIn("SLOT01_BASELINE", names)
        self.assertIn("SLOT02_AFTER_COMBAT", names)
        self.assertIn("SLOT10_CORRUPTION_NEGATIVE", names)

    def test_fixture_status_json(self) -> None:
        cp = self.run_cli("fixture-status", str(FIXTURE_ROOT), "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertTrue(payload["ok"])
        self.assertGreaterEqual(payload["manifest_count"], 1)
        self.assertIn("SLOT01", payload["present"])
        self.assertIn("SLOT02_AFTER_COMBAT", payload["missing_recommended"])
        self.assertIn("baseline", payload["coverage_categories"])


if __name__ == "__main__":
    unittest.main()
