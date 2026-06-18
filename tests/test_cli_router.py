from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from f1se.cli_router import COMMAND_HANDLERS, dispatch

ROOT = Path(__file__).resolve().parents[1]
SLOT = ROOT / "tests" / "fixtures" / "SLOT01"
FIXTURES = ROOT / "tests" / "fixtures"


class CliRouterTests(unittest.TestCase):
    def run_cli_json(self, *args: str, expected: set[int] = {0}) -> dict:
        env = {"PYTHONPATH": str(ROOT / "src")}
        cp = subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertIn(cp.returncode, expected, cp.stderr)
        return json.loads(cp.stdout)

    def test_command_handler_table(self) -> None:
        for name in ["fixture-doctor", "diff", "smoke"]:
            self.assertIn(name, COMMAND_HANDLERS)
            self.assertTrue(callable(COMMAND_HANDLERS[name]))

    def test_dispatch_fallback_for_legacy_command(self) -> None:
        seen: list[list[str]] = []

        def fallback(args: list[str]) -> int:
            seen.append(args)
            return 17

        self.assertEqual(dispatch(["legacy-command", "x"], fallback), 17)
        self.assertEqual(seen, [["legacy-command", "x"]])

    def test_router_commands_from_entrypoint(self) -> None:
        smoke = self.run_cli_json("smoke", "--json")
        self.assertTrue(smoke["ok"])
        diff = self.run_cli_json("diff", str(SLOT), str(SLOT), "--json")
        self.assertEqual(diff["summary"]["field_diff_count"], 0)
        doctor = self.run_cli_json("fixture-doctor", str(FIXTURES), "--json", expected={0, 1})
        self.assertIn("checked_slots", doctor)


if __name__ == "__main__":
    unittest.main()
