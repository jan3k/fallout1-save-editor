from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from f1se.project.cli_index import PUBLIC_COMMANDS, commands_payload

ROOT = Path(__file__).resolve().parents[1]
SLOT = ROOT / "tests" / "fixtures" / "SLOT01"


class CliIndexTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {"PYTHONPATH": str(ROOT / "src")}
        return subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)

    def test_registry_payload(self) -> None:
        payload = commands_payload()
        names = [row["name"] for row in payload["commands"]]
        self.assertEqual(payload["count"], len(PUBLIC_COMMANDS))
        for name in ["inspect", "dump", "inventory", "features", "map-summary", "commands"]:
            if name != "commands":
                self.assertIn(name, names)

    def test_commands_cli_json(self) -> None:
        cp = self.run_cli("commands", "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        names = [row["name"] for row in payload["commands"]]
        self.assertIn("map-summary", names)
        self.assertIn("global-labels", names)
        self.assertIn("inventory-editable", names)

    def test_selected_read_only_commands_still_work(self) -> None:
        cases = [
            ("dump", str(SLOT), "--json"),
            ("inventory", str(SLOT), "--json"),
            ("artifacts", str(SLOT), "--json"),
            ("globals-scan", str(SLOT), "--json"),
            ("global-labels", "--json"),
            ("map-summary", str(SLOT), "--json"),
            ("features", "--json"),
            ("fixture-status", str(ROOT / "tests" / "fixtures"), "--json"),
        ]
        for case in cases:
            with self.subTest(case=case):
                cp = self.run_cli(*case)
                self.assertEqual(cp.returncode, 0, cp.stderr)
                json.loads(cp.stdout)


if __name__ == "__main__":
    unittest.main()
