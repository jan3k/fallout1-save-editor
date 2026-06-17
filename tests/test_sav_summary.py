from __future__ import annotations

import unittest
from pathlib import Path

from f1se.project.map_summary import summarize_map

ROOT = Path(__file__).resolve().parents[1]
SLOT = ROOT / "tests" / "fixtures" / "SLOT01"
SAV = SLOT / "V13ENT.SAV"
MAIN = SLOT / "SAVE.DAT"


class SavSummaryTests(unittest.TestCase):
    def test_summary_payload(self) -> None:
        before_sav = SAV.read_bytes()
        before_main = MAIN.read_bytes()
        doc = summarize_map(SAV).to_dict()
        self.assertEqual(doc["file_name"], "V13ENT.SAV")
        self.assertGreater(doc["size"], 0)
        self.assertEqual(len(doc["sha256"]), 64)
        self.assertIn("pids", doc)
        self.assertIn("regions", doc)
        self.assertTrue(doc["read_only"])
        self.assertEqual(SAV.read_bytes(), before_sav)
        self.assertEqual(MAIN.read_bytes(), before_main)


if __name__ == "__main__":
    unittest.main()
