from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "SLOT01"


class FixtureToolsTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {"PYTHONPATH": str(ROOT / "src")}
        return subprocess.run(
            [sys.executable, "-m", "f1se", *args],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_fixture_snapshot_outputs_manifest_entry(self) -> None:
        cp = self.run_cli("fixture-snapshot", str(FIXTURE), "--name", "SLOT01", "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertIn("SLOT01", payload)
        entry = payload["SLOT01"]
        self.assertEqual(entry["save_dat_size"], 38155)
        self.assertEqual(entry["version"], "1.02R")
        self.assertEqual(entry["player_name"], "yay")
        self.assertEqual(entry["current_map_file"], "V13ENT.sav")
        self.assertEqual(entry["function5_start"], "0x88CC")
        self.assertEqual(entry["function6_start"], "0x8B38")
        self.assertEqual(entry["inventory_count"], 5)
        self.assertEqual(entry["kill_count_count"], 15)
        self.assertEqual(set(entry["expected_artifacts"]), {"AUTOMAP.SAV", "V13ENT.SAV"})
        self.assertNotIn("verify_issues", entry)

    def test_inventory_json_command_exposes_metadata(self) -> None:
        cp = self.run_cli("inventory", str(FIXTURE), "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertEqual(payload["inventory_count"], 5)
        self.assertEqual(len(payload["inventory"]), 5)
        first = payload["inventory"][0]
        self.assertEqual(first["pid"], 4)
        self.assertTrue(first["known_pid"])
        self.assertEqual(first["size_source"], "known_pid")
        self.assertEqual(first["confidence"], "high")
        self.assertIsNotNone(first["item_meta"])


if __name__ == "__main__":
    unittest.main()
