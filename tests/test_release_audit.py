from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from f1se.project.release_audit import run_release_audit

ROOT = Path(__file__).resolve().parents[1]
SLOT = ROOT / "tests" / "fixtures" / "SLOT01"


class ReleaseAuditTests(unittest.TestCase):
    def run_cli_json(self, *args: str) -> dict:
        env = {"PYTHONPATH": str(ROOT / "src")}
        cp = subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        return json.loads(cp.stdout)

    def test_audit_payload(self) -> None:
        payload = run_release_audit()
        self.assertIn(payload["status"], {"OK", "WARN"})
        self.assertTrue(payload["read_only"])
        self.assertGreaterEqual(len(payload["checks"]), 4)
        check_ids = {check["id"] for check in payload["checks"]}
        self.assertIn("cli.command_index", check_ids)
        self.assertIn("json.contracts", check_ids)

    def test_audit_cli_json_is_read_only(self) -> None:
        before = (SLOT / "SAVE.DAT").read_bytes()
        payload = self.run_cli_json("release-audit", "--json")
        self.assertIn(payload["status"], {"OK", "WARN"})
        self.assertEqual((SLOT / "SAVE.DAT").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
