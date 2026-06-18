from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from f1se.project.cli_index import JSON_COMMANDS, PUBLIC_COMMANDS
from f1se.project.compatibility import compatibility_payload
from f1se.project.features import FEATURES
from f1se.project.fixture_coverage import CATEGORY_TARGETS
from f1se.project.json_contracts import CONTRACTS, expected_payload_types
from f1se.project.json_nested_contracts import expected_nested_payload_types

EXPECTED_CONTRACT_COVERAGE: dict[str, dict[str, bool | str]] = {
    "commands": {"command": "commands", "types": True, "nested": True},
    "json_contracts": {"command": "json-contracts", "types": True, "nested": False},
    "release_audit": {"command": "release-audit", "types": True, "nested": True},
    "smoke": {"command": "smoke", "types": True, "nested": False},
    "detect": {"command": "detect", "types": True, "nested": False},
    "compatibility": {"command": "compatibility", "types": True, "nested": False},
    "fallout2_dump": {"command": "dump", "types": True, "nested": False},
    "fallout2_fields": {"command": "fields", "types": True, "nested": False},
    "fallout2_inventory": {"command": "inventory", "types": True, "nested": False},
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


def _fallout2_contract_details(contracts: dict[str, Any]) -> dict[str, Any]:
    required = ["detect", "compatibility", "fallout2_dump", "fallout2_fields", "fallout2_inventory"]
    return {
        "required_contracts": required,
        "missing_contracts": [contract_id for contract_id in required if contract_id not in contracts],
        "typed_contracts": [contract_id for contract_id in required if expected_payload_types(contract_id)],
    }


def _fallout2_fixture_details() -> dict[str, Any]:
    declared = [category for category in CATEGORY_TARGETS if category.startswith("fallout2.")]
    required = [
        "fallout2.baseline",
        "fallout2.inventory",
        "fallout2.perks",
        "fallout2.status_effects",
        "fallout2.late_game",
        "fallout2.negative",
    ]
    return {
        "declared_categories": declared,
        "required_categories": required,
        "missing_declared_categories": [category for category in required if category not in declared],
        "real_save_policy": "No real Fallout 2 saves are required or committed by this audit; curated fixtures must be imported explicitly.",
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
    f2_contracts = _fallout2_contract_details(contracts)
    checks.append(AuditCheck("json.contract_coverage.fallout2", _status(has_fail=bool(f2_contracts["missing_contracts"])), "Fallout 2 public JSON payloads are covered by explicit contracts.", f2_contracts))
    matrix = compatibility_payload()
    f2_matrix = matrix["games"]["fallout2"]
    write_statuses = {name: f2_matrix[name]["status"] for name in ("set", "patch", "preset", "raw-write")}
    unsafe_write_enabled = any(status == "supported" for status in write_statuses.values())
    checks.append(AuditCheck("compatibility.fallout2", _status(has_fail=unsafe_write_enabled), "Fallout 2 compatibility matrix keeps write support disabled or unsafe/read-only.", {"write_statuses": write_statuses, "detect_status": f2_matrix["detect"]["status"], "inventory_status": f2_matrix["inventory"]["status"]}))
    f2_fixtures = _fallout2_fixture_details()
    checks.append(AuditCheck("fixtures.fallout2", _status(has_warn=bool(f2_fixtures["missing_declared_categories"])), "Fallout 2 fixture categories are declared; real save fixtures remain opt-in.", f2_fixtures))
    result = "FAIL" if any(check.status == "FAIL" for check in checks) else "WARN" if any(check.status == "WARN" for check in checks) else "OK"
    return {"status": result, "checks": [check.to_dict() for check in checks], "summary": {"ok": sum(1 for check in checks if check.status == "OK"), "warn": sum(1 for check in checks if check.status == "WARN"), "fail": sum(1 for check in checks if check.status == "FAIL")}, "read_only": True}


def audit_exit_code(payload: dict[str, Any], *, strict: bool = False) -> int:
    if payload.get("status") == "FAIL":
        return 1
    if strict and payload.get("status") == "WARN":
        return 1
    return 0
