from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from f1se.format.save_dat import SaveDat

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "SLOT01"


class InventoryQuantityCliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {"PYTHONPATH": str(ROOT / "src")}
        return subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)

    def test_inventory_editable_json(self) -> None:
        cp = self.run_cli("inventory-editable", str(FIXTURE), "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertEqual(payload["inventory_count"], 5)
        items = {item["index"]: item for item in payload["items"]}
        self.assertEqual(items[3]["pid"], 40)
        self.assertEqual(items[3]["quantity"], 6)

    def test_quantity_dry_run(self) -> None:
        before = (FIXTURE / "SAVE.DAT").read_bytes()
        cp = self.run_cli("inventory-set-quantity", str(FIXTURE), "--index", "3", "--quantity", "20", "--json", "--dry-run")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertFalse(payload["written"])
        self.assertEqual(payload["plan"]["patch"], {"inventory.3.quantity": 20})
        self.assertEqual((FIXTURE / "SAVE.DAT").read_bytes(), before)

    def test_bad_values_return_nonzero(self) -> None:
        cp = self.run_cli("inventory-set-quantity", str(FIXTURE), "--index", "3", "--quantity", "0", "--json")
        self.assertNotEqual(cp.returncode, 0)
        cp = self.run_cli("inventory-set-quantity", str(FIXTURE), "--index", "99", "--quantity", "1", "--json")
        self.assertNotEqual(cp.returncode, 0)

    def test_quantity_write_on_temp_slot(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            slot = Path(td) / "SLOT"
            shutil.copytree(FIXTURE, slot)
            before_map = (slot / "V13ENT.SAV").read_bytes()
            cp = self.run_cli("inventory-set-quantity", str(slot), "--index", "3", "--quantity", "20", "--json", "--write")
            self.assertEqual(cp.returncode, 0, cp.stderr)
            payload = json.loads(cp.stdout)
            self.assertTrue(payload["written"])
            self.assertTrue((slot / ".f1se-backups").is_dir())
            sd = SaveDat.from_path(slot / "SAVE.DAT")
            self.assertEqual(sd.fields["inventory.3.quantity"].value, 20)
            self.assertEqual(sd.verify(), [])
            self.assertEqual(bytes(SaveDat.from_bytes(bytes(sd.data), slot / "SAVE.DAT").data), bytes(sd.data))
            self.assertEqual((slot / "V13ENT.SAV").read_bytes(), before_map)


if __name__ == "__main__":
    unittest.main()
