from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "SLOT01"
SAVE = FIXTURE / "SAVE.DAT"
MAP_FILE = FIXTURE / "V13ENT.SAV"


class MapScanCliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {"PYTHONPATH": str(ROOT / "src")}
        return subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)

    def test_map_scan_json_all_maps(self) -> None:
        before_save = SAVE.read_bytes()
        before_map = MAP_FILE.read_bytes()
        cp = self.run_cli("map-scan", str(FIXTURE), "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        maps = {row["file_name"]: row for row in payload["maps"]}
        self.assertIn("V13ENT.SAV", maps)
        row = maps["V13ENT.SAV"]
        self.assertGreater(row["size"], 0)
        self.assertEqual(len(row["sha256"]), 64)
        self.assertIn("candidates", row)
        self.assertEqual(SAVE.read_bytes(), before_save)
        self.assertEqual(MAP_FILE.read_bytes(), before_map)

    def test_map_scan_json_single_file(self) -> None:
        cp = self.run_cli("map-scan", str(FIXTURE), "--file", "V13ENT.SAV", "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertEqual([row["file_name"] for row in payload["maps"]], ["V13ENT.SAV"])

    def test_fixture_check_accepts_expected_map_artifacts(self) -> None:
        cp = self.run_cli("fixture-check", str(ROOT / "tests" / "fixtures"), "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["slots"]["SLOT01"]["ok"])


if __name__ == "__main__":
    unittest.main()
