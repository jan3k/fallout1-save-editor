from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from f1se.format.global_state import discover_global_state_candidates
from f1se.format.save_dat import SaveDat

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "SLOT01"
SAVE = FIXTURE / "SAVE.DAT"


class GlobalsScanTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {"PYTHONPATH": str(ROOT / "src")}
        return subprocess.run(
            [sys.executable, "-m", "f1se", *args],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_discover_global_state_candidates(self) -> None:
        sd = SaveDat.from_path(SAVE)
        candidates = {item.block_index: item for item in discover_global_state_candidates(sd.data, sd.blocks)}
        self.assertEqual(set(candidates), {2, 4, 20})
        self.assertEqual(candidates[2].block_name, "scripts_game_save_1")
        self.assertEqual(candidates[4].block_name, "scripts_game_save_2")
        self.assertEqual(candidates[20].block_name, "worldmap")
        self.assertGreater(candidates[2].i32_count, 0)
        self.assertIn(candidates[2].confidence, {"low", "medium", "unknown"})

    def test_globals_scan_cli_json_is_read_only(self) -> None:
        before = SAVE.read_bytes()
        cp = self.run_cli("globals-scan", str(FIXTURE), "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        by_index = {item["block_index"]: item for item in payload["candidates"]}
        self.assertEqual(set(by_index), {2, 4, 20})
        self.assertEqual(by_index[2]["block_name"], "scripts_game_save_1")
        self.assertIn("confidence", by_index[2])
        self.assertIn("notes", by_index[2])
        self.assertEqual(SAVE.read_bytes(), before)
        self.assertEqual(SaveDat.from_path(SAVE).verify(), [])


if __name__ == "__main__":
    unittest.main()
