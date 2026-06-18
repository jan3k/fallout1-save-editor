from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from f1se.project.json_contracts import contracts_payload
from f1se.project.json_contracts import validate_nested_payload_types
from f1se.project.json_nested_contracts import expected_nested_payload_types

ROOT = Path(__file__).resolve().parents[1]
SLOT = ROOT / "tests" / "fixtures" / "SLOT01"
FIXTURES = ROOT / "tests" / "fixtures"


class NestedJsonContractTests(unittest.TestCase):
    def run_cli_json(self, *args: str, expected: set[int] = {0}) -> dict:
        env = {"PYTHONPATH": str(ROOT / "src")}
        cp = subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertIn(cp.returncode, expected, cp.stderr)
        return json.loads(cp.stdout)

    def test_contract_catalog_includes_nested_types(self) -> None:
        payload = contracts_payload()
        rows = {row["id"]: row for row in payload["contracts"]}
        self.assertIn("nested_field_types", rows["commands"])
        self.assertIn("commands[]", rows["commands"]["nested_field_types"])
        self.assertIn("summary", rows["save_diff"]["nested_field_types"])

    def test_nested_validator_reports_bad_types(self) -> None:
        issues = validate_nested_payload_types({"commands": [{"name": 1, "json": "no"}]}, "commands")
        self.assertGreaterEqual(len(issues), 2)
        self.assertTrue(any("commands[0].name" in issue for issue in issues))
        self.assertTrue(any("commands[0].json" in issue for issue in issues))

    def test_expected_nested_type_copy(self) -> None:
        types = expected_nested_payload_types("commands")
        types["commands[]"]["name"] = "int"
        self.assertEqual(expected_nested_payload_types("commands")["commands[]"]["name"], "str")

    def test_real_cli_payloads_match_nested_contracts(self) -> None:
        cases = [
            ("commands", ("commands", "--json"), {0}),
            ("release_audit", ("release-audit", "--json"), {0}),
            ("fixture_doctor", ("fixture-doctor", str(FIXTURES), "--json"), {0, 1}),
            ("fixture_coverage", ("fixture-coverage", str(FIXTURES), "--json"), {0}),
            ("save_diff", ("diff", str(SLOT), str(SLOT), "--json"), {0}),
        ]
        for contract_id, args, expected in cases:
            with self.subTest(contract_id=contract_id):
                payload = self.run_cli_json(*args, expected=expected)
                self.assertEqual(validate_nested_payload_types(payload, contract_id), [])


if __name__ == "__main__":
    unittest.main()
