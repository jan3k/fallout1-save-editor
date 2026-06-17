from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from f1se.project.json_contracts import CONTRACTS, contract_ids, contracts_payload, validate_payload_keys

ROOT = Path(__file__).resolve().parents[1]
SLOT = ROOT / "tests" / "fixtures" / "SLOT01"
FIXTURES = ROOT / "tests" / "fixtures"


class JsonContractsTests(unittest.TestCase):
    def run_cli_json(self, *args: str) -> dict:
        env = {"PYTHONPATH": str(ROOT / "src")}
        cp = subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        return json.loads(cp.stdout)

    def test_contract_catalog(self) -> None:
        payload = contracts_payload()
        self.assertEqual(payload["count"], len(CONTRACTS))
        self.assertIn("features", contract_ids())
        self.assertIn("commands", contract_ids())
        self.assertIn("fixture_status", contract_ids())
        for row in payload["contracts"]:
            self.assertTrue(row["required_keys"])
            self.assertTrue(row["read_only"])

    def test_contracts_cli_json(self) -> None:
        payload = self.run_cli_json("json-contracts", "--json")
        self.assertIn("contracts", payload)
        self.assertIn("count", payload)
        self.assertGreaterEqual(payload["count"], 7)

    def test_public_json_payload_shapes(self) -> None:
        cases = {
            "features": ("features", "--json"),
            "commands": ("commands", "--json"),
            "inventory_editable": ("inventory-editable", str(SLOT), "--json"),
            "map_summary": ("map-summary", str(SLOT), "--json"),
            "global_labels": ("global-labels", "--json"),
            "globals_scan": ("globals-scan", str(SLOT), "--json"),
            "fixture_status": ("fixture-status", str(FIXTURES), "--json"),
        }
        for contract_id, args in cases.items():
            with self.subTest(contract_id=contract_id):
                payload = self.run_cli_json(*args)
                self.assertEqual(validate_payload_keys(payload, contract_id), [])

    def test_read_only_commands_do_not_modify_fixture(self) -> None:
        before = (SLOT / "SAVE.DAT").read_bytes()
        for args in [
            ("json-contracts", "--json"),
            ("commands", "--json"),
            ("map-summary", str(SLOT), "--json"),
            ("global-labels", "--json"),
            ("globals-scan", str(SLOT), "--json"),
        ]:
            self.run_cli_json(*args)
        self.assertEqual((SLOT / "SAVE.DAT").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
