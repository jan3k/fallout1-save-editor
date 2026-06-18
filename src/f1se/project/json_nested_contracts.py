from __future__ import annotations

from typing import Any

NESTED_FIELD_TYPES: dict[str, dict[str, dict[str, str]]] = {
    "commands": {
        "commands[]": {"name": "str", "json": "bool"},
    },
    "release_audit": {
        "checks[]": {"id": "str", "status": "str", "summary": "str", "details": "dict"},
    },
    "save_diff": {
        "summary": {"field_diff_count": "int", "artifact_diff_count": "int", "block_diff_count": "int"},
    },
    "fixture_doctor": {
        "findings[]": {"severity": "str", "code": "str", "message": "str"},
    },
    "fixture_coverage": {
        "expansion_plan[]": {"name": "str", "goal": "str", "requirements": "str", "coverage": "str", "source": "str", "present": "bool", "priority": "str"},
        "summary": {"present_count": "int", "recommended_count": "int", "missing_recommended_count": "int", "coverage_score": "number", "missing_category_count": "int"},
    },
}


def expected_nested_payload_types(contract_id: str) -> dict[str, dict[str, str]]:
    return {path: dict(types) for path, types in NESTED_FIELD_TYPES.get(contract_id, {}).items()}


def _matches_type(value: Any, type_name: str) -> bool:
    if type_name == "str":
        return isinstance(value, str)
    if type_name == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "bool":
        return isinstance(value, bool)
    if type_name == "list":
        return isinstance(value, list)
    if type_name == "dict":
        return isinstance(value, dict)
    if type_name == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    raise ValueError(f"unknown nested JSON contract type: {type_name}")


def _validate_object(value: Any, type_map: dict[str, str], path: str) -> list[str]:
    issues: list[str] = []
    if not isinstance(value, dict):
        return [f"{path}: expected dict, got {type(value).__name__}"]
    for key, type_name in type_map.items():
        if key not in value:
            issues.append(f"{path}.{key}: missing")
            continue
        if not _matches_type(value[key], type_name):
            issues.append(f"{path}.{key}: expected {type_name}, got {type(value[key]).__name__}")
    return issues


def validate_nested_payload_types(payload: dict[str, Any], contract_id: str) -> list[str]:
    issues: list[str] = []
    for path, type_map in expected_nested_payload_types(contract_id).items():
        if path.endswith("[]"):
            key = path[:-2]
            rows = payload.get(key, [])
            if not isinstance(rows, list):
                issues.append(f"{path}: expected list, got {type(rows).__name__}")
                continue
            for index, row in enumerate(rows):
                issues.extend(_validate_object(row, type_map, f"{path[:-2]}[{index}]"))
        else:
            if path not in payload:
                continue
            issues.extend(_validate_object(payload[path], type_map, path))
    return issues
