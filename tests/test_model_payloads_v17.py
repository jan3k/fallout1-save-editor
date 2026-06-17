from __future__ import annotations

import unittest
from pathlib import Path

from f1se.gui.model import SaveEditorSession

ROOT = Path(__file__).resolve().parents[1]
SLOT = ROOT / "tests" / "fixtures" / "SLOT01"


class ModelPayloadsV17Tests(unittest.TestCase):
    def test_map_summary_payload(self) -> None:
        session = SaveEditorSession(SLOT)
        payload = session.map_summary_payload()
        self.assertTrue(payload["maps"])
        self.assertEqual(payload["maps"][0]["file_name"], "V13ENT.SAV")
        self.assertTrue(payload["maps"][0]["read_only"])

    def test_map_summary_filter(self) -> None:
        session = SaveEditorSession(SLOT)
        payload = session.map_summary_payload("V13ENT.SAV")
        self.assertEqual([row["file_name"] for row in payload["maps"]], ["V13ENT.SAV"])

    def test_cli_commands_payload(self) -> None:
        session = SaveEditorSession(SLOT)
        payload = session.cli_commands_payload()
        names = [row["name"] for row in payload["commands"]]
        self.assertIn("commands", names)
        self.assertIn("map-summary", names)
        self.assertGreater(payload["count"], 20)


if __name__ == "__main__":
    unittest.main()
