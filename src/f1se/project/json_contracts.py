from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class JsonPayloadContract:
    id: str
    command: str
    required_keys: tuple[str, ...]
    optional_keys: tuple[str, ...] = ()
    read_only: bool = True
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "command": self.command,
            "required_keys": list(self.required_keys),
            "optional_keys": list(self.optional_keys),
            "read_only": self.read_only,
            "notes": self.notes,
        }


CONTRACTS: tuple[JsonPayloadContract, ...] = (
    JsonPayloadContract("features", "features --json", ("features",), ("counts_by_status", "counts_by_risk", "recommended_next_milestones"), True, "Feature matrix payload."),
    JsonPayloadContract("commands", "commands --json", ("commands", "count"), (), True, "Public CLI index payload."),
    JsonPayloadContract("json_contracts", "json-contracts --json", ("contracts", "count"), (), True, "JSON contract catalog."),
    JsonPayloadContract("release_audit", "release-audit --json", ("status", "checks", "summary", "read_only"), (), True, "Release audit payload."),
    JsonPayloadContract("smoke", "smoke --json", ("ok", "checks", "commands_count", "contracts_count", "audit_status", "read_only"), (), True, "Smoke payload."),
    JsonPayloadContract("inventory_editable", "inventory-editable SLOT --json", ("slot_path", "inventory_count", "items", "blocked_operations", "quantity_range"), (), True, "Existing inventory workflow view."),
    JsonPayloadContract("map_summary", "map-summary SLOT --json", ("slot_path", "maps"), (), True, "Read-only map artifact summary."),
    JsonPayloadContract("save_diff", "diff LEFT RIGHT --json", ("left_slot", "right_slot", "field_diffs", "artifact_diffs", "block_diffs", "summary", "read_only"), (), True, "Read-only slot comparison."),
    JsonPayloadContract("fixture_doctor", "fixture-doctor FIXTURES --json", ("fixture_root", "ok", "issues", "warnings", "checked_slots", "status"), (), True, "Fixture corpus doctor."),
    JsonPayloadContract("global_labels", "global-labels --json", ("labels", "count", "block_index", "read_only", "confidence_values"), (), True, "Read-only global label catalog."),
    JsonPayloadContract("globals_scan", "globals-scan SLOT --json", ("slot_path", "candidates"), (), True, "Read-only global/script candidate scan."),
    JsonPayloadContract("fixture_status", "fixture-status FIXTURES --json", ("fixture_root", "ok", "issues", "manifest_count"), ("present", "recommended", "missing_recommended", "coverage_categories", "coverage_score"), True, "Fixture corpus status."),
)


def contract_ids() -> list[str]:
    return [contract.id for contract in CONTRACTS]


def get_contract(contract_id: str) -> JsonPayloadContract:
    for contract in CONTRACTS:
        if contract.id == contract_id:
            return contract
    raise KeyError(contract_id)


def contracts_payload() -> dict[str, Any]:
    return {"contracts": [contract.to_dict() for contract in CONTRACTS], "count": len(CONTRACTS)}


def validate_payload_keys(payload: dict[str, Any], contract_id: str) -> list[str]:
    contract = get_contract(contract_id)
    return [key for key in contract.required_keys if key not in payload]
