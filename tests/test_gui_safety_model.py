from __future__ import annotations

import unittest
from pathlib import Path

from f1se.gui.model import SaveEditorSession

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "SLOT01"
SAVE = FIXTURE / "SAVE.DAT"


class GuiSafetyModelTests(unittest.TestCase):
    def test_read_only_diagnostic_payloads(self) -> None:
        session = SaveEditorSession(FIXTURE)
        artifacts = {item["name"]: item for item in session.artifacts_payload()["artifacts"]}
        self.assertEqual(artifacts["AUTOMAP.SAV"]["kind"], "AUTOMAP_SAV")
        self.assertEqual(artifacts["V13ENT.SAV"]["kind"], "MAP_SAV")

        raw_blocks = {item["index"]: item for item in session.raw_blocks_payload()["raw_blocks"]}
        self.assertIn(2, raw_blocks)
        self.assertIn(3, raw_blocks)
        self.assertIn(4, raw_blocks)
        self.assertIn(20, raw_blocks)

        globals_scan = {item["block_index"]: item for item in session.globals_scan_payload()["candidates"]}
        self.assertEqual(set(globals_scan), {2, 4, 20})

        maps = {item["file_name"]: item for item in session.map_scan_payload()["maps"]}
        self.assertIn("V13ENT.SAV", maps)
        self.assertIn("candidates", maps["V13ENT.SAV"])

    def test_safe_patch_does_not_require_advanced_confirmation(self) -> None:
        session = SaveEditorSession(FIXTURE)
        old = int(session.fields()["player.current_hp"].value)
        patch = {"player.current_hp": old + 1}
        summary = session.patch_risk_summary(patch).to_dict()
        self.assertEqual(summary["changed_field_count"], 1)
        self.assertEqual(summary["risks"], ["SAFE"])
        self.assertFalse(summary["requires_advanced_confirmation"])
        self.assertTrue(session.dirty_state(patch).dirty)

    def test_advanced_patch_requires_confirmation(self) -> None:
        session = SaveEditorSession(FIXTURE)
        old = int(session.fields()["player.coordinates"].value)
        patch = {"player.coordinates": old + 1}
        summary = session.patch_risk_summary(patch).to_dict()
        self.assertIn("ADVANCED", summary["risks"])
        self.assertTrue(summary["requires_advanced_confirmation"])
        self.assertTrue(session.requires_advanced_confirmation(patch))

    def test_reset_changes_model_and_preview_are_read_only(self) -> None:
        before = SAVE.read_bytes()
        session = SaveEditorSession(FIXTURE)
        reset = session.reset_changes_model()
        self.assertIn("player.current_hp", reset)
        self.assertEqual(SAVE.read_bytes(), before)
        preview = session.preview_patch({"player.current_hp": int(session.fields()["player.current_hp"].value) + 1})
        self.assertEqual(len(preview), 1)
        self.assertEqual(SAVE.read_bytes(), before)
        self.assertEqual(bytes(session.save_dat.data), before)

    def test_validation_summary(self) -> None:
        session = SaveEditorSession(FIXTURE)
        summary = session.validation_summary()
        self.assertIn(summary["status"], {"OK", "WARN", "FAIL"})
        self.assertEqual(summary["issues"], [])
        self.assertIn("artifact_warnings", summary)
        self.assertIn("raw_block_warnings", summary)
        self.assertIn("map_scan_warnings", summary)


if __name__ == "__main__":
    unittest.main()
