from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from f1se.gui.model import SaveEditorSession
from f1se.project.backup_restore import create_slot_backup

ROOT = Path(__file__).resolve().parents[1]
SLOT = ROOT / "tests" / "fixtures" / "SLOT01"
FIXTURES = ROOT / "tests" / "fixtures"


class ModelDiagnosticPayloadsV13Tests(unittest.TestCase):
    def test_read_only_diagnostic_payloads(self) -> None:
        session = SaveEditorSession(SLOT)
        smoke = session.smoke_payload()
        self.assertTrue(smoke["ok"])
        doctor = session.fixture_doctor_payload(FIXTURES)
        self.assertIn("checked_slots", doctor)
        diff = session.slot_diff_payload(SLOT)
        self.assertTrue(diff["read_only"])
        self.assertEqual(diff["summary"]["field_diff_count"], 0)

    def test_recovery_payloads_on_temp_slot(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            slot = Path(td) / "SLOT"
            shutil.copytree(SLOT, slot)
            session = SaveEditorSession(slot)
            before = (slot / "SAVE.DAT").read_bytes()
            empty_catalog = session.backup_catalog_payload()
            self.assertEqual(empty_catalog["count"], 0)
            created = create_slot_backup(slot)
            catalog = session.backup_catalog_payload()
            self.assertEqual(catalog["count"], 1)
            self.assertTrue(catalog["backups"][0]["manifest_present"])
            preview = session.restore_preview_payload(created["backup"])
            self.assertTrue(preview["can_restore"])
            self.assertTrue(preview["safety_backup_before_restore"])
            self.assertEqual((slot / "SAVE.DAT").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
