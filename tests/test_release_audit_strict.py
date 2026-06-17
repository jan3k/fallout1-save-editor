from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from f1se.project.release_audit import audit_exit_code, run_release_audit

ROOT = Path(__file__).resolve().parents[1]


class ReleaseAuditStrictTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {"PYTHONPATH": str(ROOT / "src")}
        return subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)

    def test_exit_code_helper(self) -> None:
        self.assertEqual(audit_exit_code({"status": "OK"}, strict=False), 0)
        self.assertEqual(audit_exit_code({"status": "OK"}, strict=True), 0)
        self.assertEqual(audit_exit_code({"status": "WARN"}, strict=False), 0)
        self.assertEqual(audit_exit_code({"status": "WARN"}, strict=True), 1)
        self.assertEqual(audit_exit_code({"status": "FAIL"}, strict=False), 1)
        self.assertEqual(audit_exit_code({"status": "FAIL"}, strict=True), 1)

    def test_strict_cli_exit_code_matches_payload(self) -> None:
        expected = audit_exit_code(run_release_audit(), strict=True)
        cp = self.run_cli("release-audit", "--strict", "--json")
        self.assertEqual(cp.returncode, expected, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertTrue(payload["strict"])
        self.assertIn(payload["status"], {"OK", "WARN", "FAIL"})


if __name__ == "__main__":
    unittest.main()
