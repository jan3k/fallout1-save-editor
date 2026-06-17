from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from f1se.gui.model import SaveEditorSession, format_diff

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "SLOT01"


class GuiModelTests(unittest.TestCase):
    def test_session_summary_and_groups(self) -> None:
        session = SaveEditorSession(FIXTURE)
        summary = session.summary()
        self.assertEqual(summary["signature"], "FALLOUT SAVE FILE")
        self.assertEqual(summary["version"], "1.02R")
        groups = session.field_groups()
        self.assertEqual(len(groups["special_base"]), 7)
        self.assertEqual(len(groups["skills"]), 18)
        self.assertEqual(len(groups["traits"]), 2)
        self.assertGreaterEqual(len(groups["perks"]), 64)

    def test_preview_patch_does_not_mutate_session(self) -> None:
        session = SaveEditorSession(FIXTURE)
        before = bytes(session.save_dat.data)
        diffs = session.preview_patch({"player.base_strength": 9})
        self.assertEqual(len(diffs), 1)
        self.assertIn("player.base_strength", format_diff(diffs[0]))
        self.assertEqual(bytes(session.save_dat.data), before)

    def test_dry_run_apply_does_not_modify_disk(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            slot = Path(td) / "SLOT01"
            shutil.copytree(FIXTURE, slot)
            before = (slot / "SAVE.DAT").read_bytes()
            session = SaveEditorSession(slot)
            result = session.apply_patch({"player.base_strength": 9}, write=False)
            self.assertFalse(result.written)
            self.assertIsNone(result.backup_path)
            self.assertEqual((slot / "SAVE.DAT").read_bytes(), before)
            self.assertFalse((slot / ".f1se-backups").exists())

    def test_write_changes_disk_and_creates_backup(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            slot = Path(td) / "SLOT01"
            shutil.copytree(FIXTURE, slot)
            before = (slot / "SAVE.DAT").read_bytes()
            session = SaveEditorSession(slot)
            result = session.apply_patch({"player.base_strength": 9}, write=True)
            self.assertTrue(result.written)
            self.assertIsNotNone(result.backup_path)
            assert result.backup_path is not None
            self.assertEqual((result.backup_path / "SAVE.DAT").read_bytes(), before)
            after = (slot / "SAVE.DAT").read_bytes()
            self.assertNotEqual(after, before)
            self.assertEqual(after[0x8B40:0x8B44], b"\x00\x00\x00\x09")


    def test_source_aligned_groups_include_kills_options_and_derived(self) -> None:
        session = SaveEditorSession(FIXTURE)
        groups = session.field_groups()
        self.assertEqual(len(groups["kill_counts"]), 15)
        self.assertGreaterEqual(len(groups["options"]), 13)
        self.assertGreaterEqual(len(groups["derived_stats"]), 10)

    def test_model_exposes_trait_effects_and_presets(self) -> None:
        session = SaveEditorSession(FIXTURE)
        self.assertEqual(len(session.effective_special()), 7)
        self.assertIn("player.radiation", session.preset_patch("heal"))
        self.assertIsInstance(session.trait_effect_notes(), list)

    def test_cli_gui_help_does_not_require_display(self) -> None:
        env = {"PYTHONPATH": str(ROOT / "src")}
        cp = subprocess.run([sys.executable, "-m", "f1se", "gui", "--help"], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("optional save slot", cp.stdout)


if __name__ == "__main__":
    unittest.main()
