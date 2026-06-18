from __future__ import annotations

import unittest

from f1se.project.release_audit import EXPECTED_CONTRACT_COVERAGE, run_release_audit


class ReleaseAuditContractCoverageTests(unittest.TestCase):
    def test_expected_contract_coverage_matrix(self) -> None:
        self.assertIn("commands", EXPECTED_CONTRACT_COVERAGE)
        self.assertIn("release_audit", EXPECTED_CONTRACT_COVERAGE)
        self.assertTrue(EXPECTED_CONTRACT_COVERAGE["commands"]["types"])
        self.assertTrue(EXPECTED_CONTRACT_COVERAGE["commands"]["nested"])

    def test_audit_reports_contract_coverage(self) -> None:
        payload = run_release_audit()
        checks = {check["id"]: check for check in payload["checks"]}
        self.assertIn("json.contract_coverage", checks)
        check = checks["json.contract_coverage"]
        self.assertEqual(check["status"], "OK")
        details = check["details"]
        self.assertEqual(details["missing_contracts"], [])
        self.assertEqual(details["missing_type_contracts"], [])
        self.assertEqual(details["missing_nested_contracts"], [])
        self.assertGreaterEqual(details["expected_contract_count"], 10)
        self.assertTrue(details["matrix"]["commands"]["has_top_level_types"])
        self.assertTrue(details["matrix"]["commands"]["has_nested_samples"])
        self.assertTrue(details["matrix"]["fixture_coverage"]["requires_nested_samples"])


if __name__ == "__main__":
    unittest.main()
