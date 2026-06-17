from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from f1se.project.fixture_doctor import fixture_doctor
from f1se.project.save_diff import diff_slots
from f1se.project.smoke import smoke_payload

ROOT = Path(__file__).resolve().parents[1]
SLOT = ROOT / "tests" / "fixtures" / "SLOT01"
FIXTURES = ROOT / "tests" / "fixtures"


class FinalDiagnosticsTests(unittest.TestCase):
    def run_cli_json(self, *args: str) -> dict:
        env = {"PYTHONPATH": str(ROOT / "src")}
        cp = subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        return json.loads(cp.stdout)

    def test_fixture_doctor_and_smoke(self) -> None:
        doctor = fixture_doctor(FIXTURES)
        self.assertIn("ok", doctor)
        self.assertIn("checked_slots", doctor)
        smoke = smoke_payload()
        self.assertTrue(smoke["ok"])
        self.run_cli_json("smoke", "--json")

    def test_diff_read_only(self) -> None:
        before = (SLOT / "SAVE.DAT").read_bytes()
        payload = diff_slots(SLOT, SLOT)
        self.assertEqual(payload["summary"]["field_diff_count"], 0)
        self.assertTrue(payload["read_only"])
        self.assertEqual((SLOT / "SAVE.DAT").read_bytes(), before)
        cli_payload = self.run_cli_json("diff", str(SLOT), str(SLOT), "--json")
        self.assertEqual(cli_payload["summary"]["field_diff_count"], 0)


if __name__ == "__main__":
    unittest.main()
