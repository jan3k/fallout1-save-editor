from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from f1se.project.backup_restore import create_slot_backup, list_backups, restore_preview

ROOT = Path(__file__).resolve().parents[1]
SLOT = ROOT / "tests" / "fixtures" / "SLOT01"


class BackupManifestTests(unittest.TestCase):
    def run_cli_json(self, *args: str) -> dict:
        env = {"PYTHONPATH": str(ROOT / "src")}
        cp = subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        return json.loads(cp.stdout)

    def test_create_backup_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            slot = Path(td) / "SLOT"
            shutil.copytree(SLOT, slot)
            result = create_slot_backup(slot)
            self.assertEqual(result["manifest"]["backup"], result["backup"])
            self.assertGreater(result["manifest"]["file_count"], 0)
            catalog = list_backups(slot)
            self.assertEqual(catalog["count"], 1)
            self.assertTrue(catalog["backups"][0]["manifest_present"])

    def test_restore_preview_diff_summary(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            slot = Path(td) / "SLOT"
            shutil.copytree(SLOT, slot)
            result = create_slot_backup(slot)
            save_path = slot / "SAVE.DAT"
            payload = bytearray(save_path.read_bytes())
            payload[-1] ^= 1
            save_path.write_bytes(bytes(payload))
            preview = restore_preview(slot, result["backup"])
            self.assertTrue(preview["manifest_present"])
            self.assertGreaterEqual(preview["diff_summary"]["changed_or_missing_files"], 1)

    def test_backup_cli_json_uses_manifest_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            slot = Path(td) / "SLOT"
            shutil.copytree(SLOT, slot)
            payload = self.run_cli_json("backup", str(slot), "--json")
            self.assertIn("manifest", payload)
            self.assertGreater(payload["manifest"]["file_count"], 0)


if __name__ == "__main__":
    unittest.main()
