from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from f1se.format.raw_inspection import inspect_raw_blocks
from f1se.format.save_dat import SaveDat

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "SLOT01"
SAVE = FIXTURE / "SAVE.DAT"


class RawBlockInspectionTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {"PYTHONPATH": str(ROOT / "src")}
        return subprocess.run(
            [sys.executable, "-m", "f1se", *args],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_raw_block_inspection_contains_stable_raw_blocks(self) -> None:
        sd = SaveDat.from_path(SAVE)
        docs = {item.index: item.to_dict() for item in inspect_raw_blocks(sd.data, sd.blocks)}
        self.assertEqual(docs[2]["name"], "scripts_game_save_1")
        self.assertEqual(docs[2]["start"], 0x7567)
        self.assertEqual(docs[2]["end"], 0x7BDE)
        self.assertEqual(docs[3]["start"], 0x7BDE)
        self.assertEqual(docs[4]["end"], 0x88CC)
        self.assertEqual(docs[20]["start"], 0x9009)
        self.assertEqual(docs[20]["end"], 0x94FB)
        self.assertEqual(len(docs[20]["sha256"]), 64)
        self.assertIn("entropy_hint", docs[20])

    def test_raw_blocks_cli_json_is_read_only(self) -> None:
        before = SAVE.read_bytes()
        cp = self.run_cli("raw-blocks", str(FIXTURE), "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        by_index = {item["index"]: item for item in payload["raw_blocks"]}
        self.assertIn(2, by_index)
        self.assertIn(3, by_index)
        self.assertIn(4, by_index)
        self.assertIn(20, by_index)
        self.assertEqual(by_index[2]["start"], 0x7567)
        self.assertEqual(SAVE.read_bytes(), before)
        self.assertEqual(SaveDat.from_path(SAVE).verify(), [])


if __name__ == "__main__":
    unittest.main()
