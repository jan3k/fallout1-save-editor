from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from f1se.project.json_contracts import contracts_payload, expected_payload_types, validate_payload_keys, validate_payload_types

ROOT = Path(__file__).resolve().parents[1]
SLOT = ROOT / "tests" / "fixtures" / "SLOT01"
FIXTURES = ROOT / "tests" / "fixtures"


class JsonContractTypesTests(unittest.TestCase):
    def run_cli_json(self, *args: str, expected: set[int] = {0}) -> dict:
        env = {"PYTHONPATH": str(ROOT / "src")}
        cp = subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertIn(cp.returncode, expected, cp.stderr)
        return json.loads(cp.stdout)

    def assert_contract(self, contract_id: str, payload: dict) -> None:
        self.assertEqual(validate_payload_keys(payload, contract_id), [])
        self.assertEqual(validate_payload_types(payload, contract_id), [])

    def test_contract_catalog_includes_field_types(self) -> None:
        payload = contracts_payload()
        self.assertGreater(payload["count"], 0)
        for row in payload["contracts"]:
            self.assertIn("field_types", row)
            self.assertIsInstance(row["field_types"], dict)
        self.assertEqual(expected_payload_types("commands")["count"], "int")

    def test_type_validator_reports_bad_types(self) -> None:
        issues = validate_payload_types({"commands": [], "count": "bad"}, "commands")
        self.assertEqual(len(issues), 1)
        self.assertIn("count", issues[0])

    def test_real_cli_payloads_match_typed_contracts(self) -> None:
        cases = [
            ("commands", ("commands", "--json"), {0}),
            ("json_contracts", ("json-contracts", "--json"), {0}),
            ("release_audit", ("release-audit", "--json"), {0}),
            ("smoke", ("smoke", "--json"), {0}),
            ("fixture_coverage", ("fixture-coverage", str(FIXTURES), "--json"), {0}),
            ("fixture_doctor", ("fixture-doctor", str(FIXTURES), "--json"), {0, 1}),
            ("save_diff", ("diff", str(SLOT), str(SLOT), "--json"), {0}),
            ("map_summary", ("map-summary", str(SLOT), "--json"), {0}),
            ("global_labels", ("global-labels", "--json"), {0}),
            ("fixture_status", ("fixture-status", str(FIXTURES), "--json"), {0}),
        ]
        for contract_id, args, expected in cases:
            with self.subTest(contract_id=contract_id):
                self.assert_contract(contract_id, self.run_cli_json(*args, expected=expected))


if __name__ == "__main__":
    unittest.main()
