from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from f1se.project.cli_index import JSON_COMMANDS, PUBLIC_COMMANDS
from f1se.project.features import FEATURES
from f1se.project.json_contracts import CONTRACTS, expected_payload_types
from f1se.project.json_nested_contracts import expected_nested_payload_types

EXPECTED_CONTRACT_COVERAGE: dict[str, dict[str, bool | str]] = {
    "commands": {"command": "commands", "types": True, "nested": True},
    "json_contracts": {"command": "json-contracts", "types": True, "nested": False},
    "release_audit": {"command": "release-audit", "types": True, "nested": True},
    "smoke": {"command": "smoke", "types": True, "nested": False},
    "save_diff": {"command": "diff", "types": True, "nested": True},
    "fixture_doctor": {"command": "fixture-doctor", "types": True, "nested": True},
    "fixture_coverage": {"command": "fixture-coverage", "types": True, "nested": True},
    "fixture_status": {"command": "fixture-status", "types": True, "nested": False},
    "global_labels": {"command": "global-labels", "types": True, "nested": False},
    "map_summary": {"command": "map-summary", "types": True, "nested": False},
    "globals_scan": {"command": "globals-scan", "types": True, "nested": False},
    "inventory_editable": {"command": "inventory-editable", "types": True, "nested": False},
}


@dataclass(frozen=True, slots=True)
class AuditCheck:
    id: str
    status: str
    summary: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "status": self.status, "summary": self.summary, "details": dict(self.details)}


def _status(has_fail: bool = False, has_warn: bool = False) -> str:
    if has_fail:
        return "FAIL"
    if has_warn:
        return "WARN"
    return "OK"


def _contract_coverage_details(contracts: dict[str, Any]) -> dict[str, Any]:
    missing_contracts = sorted(contract_id for contract_id in EXPECTED_CONTRACT_COVERAGE if contract_id not in contracts)
    missing_type_contracts = sorted(
        contract_id
        for contract_id, rule in EXPECTED_CONTRACT_COVERAGE.items()
        if rule["types"] and contract_id in contracts and not expected_payload_types(contract_id)
    )
    missing_nested_contracts = sorted(
        contract_id
        for contract_id, rule in EXPECTED_CONTRACT_COVERAGE.items()
        if rule["nested"] and contract_id in contracts and not expected_nested_payload_types(contract_id)
    )
    matrix = {
        contract_id: {
            "command": rule["command"],
            "has_contract": contract_id in contracts,
            "has_top_level_types": bool(expected_payload_types(contract_id)),
            "has_nested_samples": bool(expected_nested_payload_types(contract_id)),
            "requires_nested_samples": bool(rule["nested"]),
        }
        for contract_id, rule in EXPECTED_CONTRACT_COVERAGE.items()
    }
    return {
        "expected_contract_count": len(EXPECTED_CONTRACT_COVERAGE),
        "missing_contracts": missing_contracts,
        "missing_type_contracts": missing_type_contracts,
        "missing_nested_contracts": missing_nested_contracts,
        "matrix": matrix,
    }


def run_release_audit() -> dict[str, Any]:
    checks: list[AuditCheck] = []
    commands = set(PUBLIC_COMMANDS)
    contracts = {contract.id: contract for contract in CONTRACTS}
    contract_commands = {contract.command.split()[0] for contract in CONTRACTS}
    missing_contracts = sorted(name for name in JSON_COMMANDS if name not in contract_commands and name not in {"fixture-import", "fixture-snapshot", "fixture-check", "effective", "map-scan", "raw-blocks", "artifacts", "inventory"})
    checks.append(AuditCheck("cli.command_index", _status(has_fail=not commands, has_warn=bool(missing_contracts)), "Public CLI command index is present and key JSON contracts are tracked.", {"command_count": len(commands), "json_command_count": len(JSON_COMMANDS), "missing_contracts": missing_contracts}))
    feature_ids = {feature.id for feature in FEATURES}
    required_features = {"inventory.quantity_workflow", "global.labels", "map.sav.scan", "raw.access", "fixtures.import_workflow"}
    missing_features = sorted(required_features - feature_ids)
    checks.append(AuditCheck("features.required_capabilities", _status(has_fail=bool(missing_features)), "Required safety and diagnostic feature rows are present.", {"missing_features": missing_features, "feature_count": len(feature_ids)}))
    raw_features = [feature.id for feature in FEATURES if feature.risk_level == "RAW"]
    experimental_features = [feature.id for feature in FEATURES if feature.risk_level == "EXPERIMENTAL"]
    checks.append(AuditCheck("safety.risk_surface", _status(has_warn=bool(experimental_features)), "Risk surface remains explicit and auditable.", {"raw_features": raw_features, "experimental_features": experimental_features}))
    read_only_contracts = [contract.id for contract in CONTRACTS if contract.read_only]
    typed_contracts = [contract.id for contract in CONTRACTS if expected_payload_types(contract.id)]
    nested_contracts = [contract.id for contract in CONTRACTS if expected_nested_payload_types(contract.id)]
    checks.append(AuditCheck("json.contracts", _status(has_fail=not read_only_contracts or not typed_contracts), "JSON payload contracts exist for public automation surfaces.", {"contract_count": len(contracts), "read_only_contracts": read_only_contracts, "typed_contracts": typed_contracts, "nested_contracts": nested_contracts}))
    coverage = _contract_coverage_details(contracts)
    coverage_fail = bool(coverage["missing_contracts"] or coverage["missing_type_contracts"] or coverage["missing_nested_contracts"])
    checks.append(AuditCheck("json.contract_coverage", _status(has_fail=coverage_fail), "Expected JSON contracts have top-level type coverage and required nested samples.", coverage))
    result = "FAIL" if any(check.status == "FAIL" for check in checks) else "WARN" if any(check.status == "WARN" for check in checks) else "OK"
    return {"status": result, "checks": [check.to_dict() for check in checks], "summary": {"ok": sum(1 for check in checks if check.status == "OK"), "warn": sum(1 for check in checks if check.status == "WARN"), "fail": sum(1 for check in checks if check.status == "FAIL")}, "read_only": True}


def audit_exit_code(payload: dict[str, Any], *, strict: bool = False) -> int:
    if payload.get("status") == "FAIL":
        return 1
    if strict and payload.get("status") == "WARN":
        return 1
    return 0
