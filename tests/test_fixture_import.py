from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "SLOT01"


class FixtureImportTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {"PYTHONPATH": str(ROOT / "src")}
        return subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)

    def test_fixture_import_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "SOURCE"
            shutil.copytree(FIXTURE, src)
            before = (src / "SAVE.DAT").read_bytes()
            root = Path(td) / "fixtures"
            cp = self.run_cli("fixture-import", str(src), "--fixture-root", str(root), "--name", "SLOT02_AFTER_COMBAT", "--dry-run", "--json")
            self.assertEqual(cp.returncode, 0, cp.stderr)
            payload = json.loads(cp.stdout)
            self.assertFalse(payload["written"])
            self.assertTrue(payload["ok"])
            self.assertIn("SAVE.DAT", payload["files"])
            self.assertEqual((src / "SAVE.DAT").read_bytes(), before)
            self.assertFalse((root / "SLOT02_AFTER_COMBAT").exists())

    def test_fixture_import_write_and_check(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "SOURCE"
            shutil.copytree(FIXTURE, src)
            (src / ".f1se-backups").mkdir()
            (src / ".f1se-backups" / "junk.txt").write_text("skip", encoding="utf-8")
            (src / "ignored.tmp").write_text("skip", encoding="utf-8")
            before = (src / "SAVE.DAT").read_bytes()
            root = Path(td) / "fixtures"
            cp = self.run_cli("fixture-import", str(src), "--fixture-root", str(root), "--name", "SLOT_COPY", "--write", "--json")
            self.assertEqual(cp.returncode, 0, cp.stderr)
            payload = json.loads(cp.stdout)
            self.assertTrue(payload["written"])
            self.assertTrue((root / "SLOT_COPY" / "SAVE.DAT").is_file())
            self.assertFalse((root / "SLOT_COPY" / ".f1se-backups").exists())
            self.assertFalse((root / "SLOT_COPY" / "ignored.tmp").exists())
            self.assertEqual((src / "SAVE.DAT").read_bytes(), before)
            manifest = json.loads((root / "fixtures.json").read_text(encoding="utf-8"))
            self.assertIn("SLOT_COPY", manifest)
            self.assertEqual(manifest["SLOT_COPY"]["function5_start"], "0x88CC")
            cp = self.run_cli("fixture-check", str(root), "--json")
            self.assertEqual(cp.returncode, 0, cp.stderr)
            check = json.loads(cp.stdout)
            self.assertTrue(check["ok"])


if __name__ == "__main__":
    unittest.main()
