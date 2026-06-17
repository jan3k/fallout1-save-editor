from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLOT = ROOT / "tests" / "fixtures" / "SLOT01"
SAV = SLOT / "V13ENT.SAV"


class SavCliTests(unittest.TestCase):
    def test_map_summary_json(self) -> None:
        env = {"PYTHONPATH": str(ROOT / "src")}
        before = SAV.read_bytes()
        cp = subprocess.run([sys.executable, "-m", "f1se", "map-summary", str(SLOT), "--file", "V13ENT.SAV", "--json"], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertEqual(payload["maps"][0]["file_name"], "V13ENT.SAV")
        self.assertTrue(payload["maps"][0]["read_only"])
        self.assertEqual(SAV.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
