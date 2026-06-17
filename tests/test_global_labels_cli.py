from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "SLOT01"
SAVE = FIXTURE / "SAVE.DAT"


class GlobalLabelsCliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {"PYTHONPATH": str(ROOT / "src")}
        return subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)

    def test_global_labels_json(self) -> None:
        cp = self.run_cli("global-labels", "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertTrue(payload["read_only"])
        self.assertGreaterEqual(payload["count"], 3)
        self.assertTrue(all("confidence" in row for row in payload["labels"]))

    def test_global_labels_block_filter_json(self) -> None:
        cp = self.run_cli("global-labels", "--block", "2", "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertEqual(payload["block_index"], 2)
        self.assertTrue(payload["labels"])
        self.assertTrue(all(row["block_index"] == 2 for row in payload["labels"]))

    def test_globals_scan_includes_labels_and_is_read_only(self) -> None:
        before = SAVE.read_bytes()
        cp = self.run_cli("globals-scan", str(FIXTURE), "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        by_index = {row["block_index"]: row for row in payload["candidates"]}
        self.assertIn(2, by_index)
        self.assertIn("labels", by_index[2])
        self.assertTrue(by_index[2]["labels"])
        self.assertEqual(SAVE.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
