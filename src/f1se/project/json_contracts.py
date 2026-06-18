from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from f1se.project.json_nested_contracts import expected_nested_payload_types, validate_nested_payload_types


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
            "field_types": expected_payload_types(self.id),
            "nested_field_types": expected_nested_payload_types(self.id),
        }


C = JsonPayloadContract
CONTRACTS: tuple[JsonPayloadContract, ...] = (
    C("features", "features --json", ("features",), ("counts_by_status", "counts_by_risk", "recommended_next_milestones"), True, "Feature matrix payload."),
    C("commands", "commands --json", ("commands", "count"), (), True, "Public CLI index payload."),
    C("json_contracts", "json-contracts --json", ("contracts", "count"), (), True, "JSON contract catalog."),
    C("release_audit", "release-audit --json", ("status", "checks", "summary", "read_only"), (), True, "Release audit payload."),
    C("smoke", "smoke --json", ("ok", "checks", "commands_count", "contracts_count", "audit_status", "read_only"), (), True, "Smoke payload."),
    C("detect", "detect SLOT --json", ("game_kind", "confidence", "signature", "version", "reason", "read_only"), ("profile",), True, "Game detection payload for Fallout 1, Fallout 2 or unknown saves."),
    C("compatibility", "compatibility --json", ("games", "status_values", "read_only"), ("notes",), True, "Game compatibility matrix."),
    C("character_summary", "character-summary SLOT --json", ("game_kind", "slot_path", "identity", "progression", "status_effects", "special", "skills", "traits", "active_perks", "inventory_summary", "warnings", "read_only"), ("trait_effect_notes", "nonzero_kill_counts"), True, "Fallout 1 read-only character summary."),
    C("progression", "progression SLOT --json", ("game_kind", "slot_path", "identity", "level", "experience", "skill_points", "karma", "reputation", "traits", "perk_cadence", "warnings", "read_only"), (), True, "Fallout 1 read-only progression summary."),
    C("derived_stats", "derived-stats SLOT --json", ("game_kind", "slot_path", "identity", "source_special", "formula_scope", "derived_stats", "mismatches", "summary", "warnings", "read_only"), (), True, "Fallout 1 read-only derived-stat consistency report."),
    C("fallout2_dump", "dump SLOT --game fallout2 --json", ("game_kind", "path", "size", "sha256", "header", "metadata", "sections", "fields", "inventory", "warnings", "read_only", "parser_status"), ("inventory_count", "size_hex"), True, "Fallout 2 read-only dump payload."),
    C("fallout2_fields", "fields SLOT --game fallout2 --json", ("game_kind", "path", "fields", "warnings", "read_only", "parser_status"), (), True, "Fallout 2 read-only field schema payload."),
    C("fallout2_inventory", "inventory SLOT --game fallout2 --json", ("game_kind", "slot_path", "inventory_count", "inventory", "blocked_operations", "warnings", "read_only"), (), True, "Fallout 2 read-only inventory payload."),
    C("inventory_editable", "inventory-editable SLOT --json", ("slot_path", "inventory_count", "items", "blocked_operations", "quantity_range"), (), True, "Existing inventory workflow view."),
    C("map_summary", "map-summary SLOT --json", ("slot_path", "maps"), (), True, "Read-only map artifact summary."),
    C("save_diff", "diff LEFT RIGHT --json", ("left_slot", "right_slot", "field_diffs", "artifact_diffs", "block_diffs", "summary", "read_only"), (), True, "Read-only slot comparison."),
    C("fixture_doctor", "fixture-doctor FIXTURES --json", ("fixture_root", "ok", "issues", "warnings", "findings", "checked_slots", "status"), (), True, "Fixture corpus doctor."),
    C("fixture_coverage", "fixture-coverage FIXTURES --json", ("fixture_root", "status", "recommended", "expansion_plan", "coverage_categories", "missing_categories", "summary", "read_only"), (), True, "Fixture coverage plan."),
    C("global_labels", "global-labels --json", ("labels", "count", "block_index", "read_only", "confidence_values"), (), True, "Read-only global label catalog."),
    C("globals_scan", "globals-scan SLOT --json", ("slot_path", "candidates"), (), True, "Read-only global/script candidate scan."),
    C("fixture_status", "fixture-status FIXTURES --json", ("fixture_root", "ok", "issues", "manifest_count"), ("present", "recommended", "missing_recommended", "coverage_categories", "coverage_score"), True, "Fixture corpus status."),
)

CONTRACT_FIELD_TYPES: dict[str, dict[str, str]] = {
    "features": {"features": "list", "counts_by_status": "dict", "counts_by_risk": "dict", "recommended_next_milestones": "list"},
    "commands": {"commands": "list", "count": "int"},
    "json_contracts": {"contracts": "list", "count": "int"},
    "release_audit": {"status": "str", "checks": "list", "summary": "dict", "read_only": "bool"},
    "smoke": {"ok": "bool", "checks": "list", "commands_count": "int", "contracts_count": "int", "audit_status": "str", "read_only": "bool"},
    "detect": {"game_kind": "str", "confidence": "int", "signature": "str", "version": "str_or_none", "reason": "str", "read_only": "bool", "profile": "dict"},
    "compatibility": {"games": "dict", "status_values": "list", "read_only": "bool", "notes": "list"},
    "character_summary": {"game_kind": "str", "slot_path": "str", "identity": "dict", "progression": "dict", "status_effects": "dict", "special": "dict", "skills": "dict", "traits": "list", "trait_effect_notes": "list", "active_perks": "list", "nonzero_kill_counts": "list", "inventory_summary": "dict", "warnings": "list", "read_only": "bool"},
    "progression": {"game_kind": "str", "slot_path": "str", "identity": "dict", "level": "dict", "experience": "int", "skill_points": "int", "karma": "int", "reputation": "int", "traits": "list", "perk_cadence": "dict", "warnings": "list", "read_only": "bool"},
    "derived_stats": {"game_kind": "str", "slot_path": "str", "identity": "dict", "source_special": "dict", "formula_scope": "str", "derived_stats": "dict", "mismatches": "list", "summary": "dict", "warnings": "list", "read_only": "bool"},
    "fallout2_dump": {"game_kind": "str", "path": "str", "size": "int", "size_hex": "str", "sha256": "str", "header": "dict", "metadata": "dict", "sections": "dict", "fields": "dict", "inventory": "list", "inventory_count": "int", "warnings": "list", "read_only": "bool", "parser_status": "str"},
    "fallout2_fields": {"game_kind": "str", "path": "str", "fields": "dict", "warnings": "list", "read_only": "bool", "parser_status": "str"},
    "fallout2_inventory": {"game_kind": "str", "slot_path": "str", "inventory_count": "int", "inventory": "list", "blocked_operations": "list", "warnings": "list", "read_only": "bool"},
    "inventory_editable": {"slot_path": "str", "inventory_count": "int", "items": "list", "blocked_operations": "list", "quantity_range": "dict"},
    "map_summary": {"slot_path": "str", "maps": "list"},
    "save_diff": {"left_slot": "str", "right_slot": "str", "field_diffs": "list", "artifact_diffs": "list", "block_diffs": "list", "summary": "dict", "read_only": "bool"},
    "fixture_doctor": {"fixture_root": "str", "ok": "bool", "issues": "list", "warnings": "list", "findings": "list", "checked_slots": "list", "status": "dict"},
    "fixture_coverage": {"fixture_root": "str", "status": "dict", "recommended": "list", "expansion_plan": "list", "coverage_categories": "list", "missing_categories": "list", "summary": "dict", "read_only": "bool"},
    "global_labels": {"labels": "list", "count": "int", "block_index": "dict_or_none", "read_only": "bool", "confidence_values": "list"},
    "globals_scan": {"slot_path": "str", "candidates": "list"},
    "fixture_status": {"fixture_root": "str", "ok": "bool", "issues": "list", "manifest_count": "int", "present": "list", "recommended": "list", "missing_recommended": "list", "coverage_categories": "list", "coverage_score": "number"},
}


def contract_ids() -> list[str]:
    return [contract.id for contract in CONTRACTS]


def get_contract(contract_id: str) -> JsonPayloadContract:
    for contract in CONTRACTS:
        if contract.id == contract_id:
            return contract
    raise KeyError(contract_id)


def expected_payload_types(contract_id: str) -> dict[str, str]:
    return dict(CONTRACT_FIELD_TYPES.get(contract_id, {}))


def contracts_payload() -> dict[str, Any]:
    return {"contracts": [contract.to_dict() for contract in CONTRACTS], "count": len(CONTRACTS)}


def validate_payload_keys(payload: dict[str, Any], contract_id: str) -> list[str]:
    contract = get_contract(contract_id)
    return [key for key in contract.required_keys if key not in payload]


def _matches_type(value: Any, type_name: str) -> bool:
    if type_name == "str":
        return isinstance(value, str)
    if type_name == "str_or_none":
        return value is None or isinstance(value, str)
    if type_name == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "bool":
        return isinstance(value, bool)
    if type_name == "list":
        return isinstance(value, list)
    if type_name == "dict":
        return isinstance(value, dict)
    if type_name == "dict_or_none":
        return value is None or isinstance(value, dict)
    if type_name == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    raise ValueError(f"unknown JSON contract type: {type_name}")


def validate_payload_types(payload: dict[str, Any], contract_id: str) -> list[str]:
    issues: list[str] = []
    for key, type_name in expected_payload_types(contract_id).items():
        if key in payload and not _matches_type(payload[key], type_name):
            issues.append(f"{key}: expected {type_name}, got {type(payload[key]).__name__}")
    return issues
