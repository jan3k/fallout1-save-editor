from __future__ import annotations

import unittest
from pathlib import Path

from f1se.format.header import HEADER_SIZE
from f1se.format.save_dat import SaveDat
from f1se.io.endian import put_i32be

ROOT = Path(__file__).resolve().parents[1]
SAVE = ROOT / "tests" / "fixtures" / "SLOT01" / "SAVE.DAT"


class VerifyNegativeTests(unittest.TestCase):
    def parse(self) -> SaveDat:
        return SaveDat.from_path(SAVE)

    def assertIssueContains(self, issues: list[str], text: str) -> None:
        self.assertTrue(any(text in issue for issue in issues), issues)

    def test_verify_reports_damaged_function5_signature(self) -> None:
        sd = self.parse()
        sd.data[sd.player_object.start:sd.player_object.start + 4] = b"\x00\x00XX"
        issues = sd.verify()
        self.assertIssueContains(issues, "Function 5 FP signature mismatch")

    def test_verify_reports_bad_block_bounds(self) -> None:
        sd = self.parse()
        sd.blocks[1].start = HEADER_SIZE - 1
        issues = sd.verify()
        self.assertIssueContains(issues, "block 1 overlaps previous block")

    def test_verify_reports_duplicate_tag_skills(self) -> None:
        sd = self.parse()
        put_i32be(sd.data, sd.tag_skills_start, 1)
        put_i32be(sd.data, sd.tag_skills_start + 4, 1)
        issues = sd.verify()
        self.assertIssueContains(issues, "duplicate tag skill ids")

    def test_verify_reports_duplicate_traits(self) -> None:
        sd = self.parse()
        put_i32be(sd.data, sd.traits_start, 8)
        put_i32be(sd.data, sd.traits_start + 4, 8)
        issues = sd.verify()
        self.assertIssueContains(issues, "duplicate trait ids")

    def test_verify_reports_invalid_options_anchor(self) -> None:
        sd = self.parse()
        put_i32be(sd.data, sd.options_start, 2)
        issues = sd.verify()
        self.assertIssueContains(issues, "options block anchor failed plausibility checks")

    def test_verify_reports_inventory_bounds_mismatch(self) -> None:
        sd = self.parse()
        sd.player_object.inventory[0].end = sd.critter_stats.start + 4
        issues = sd.verify()
        self.assertIssueContains(issues, "inventory item 0 has invalid bounds")


if __name__ == "__main__":
    unittest.main()
