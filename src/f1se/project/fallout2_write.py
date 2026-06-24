from __future__ import annotations

from pathlib import Path
from typing import Any

from f1se.format.fallout2.save_dat import Fallout2SaveDat
from f1se.io.atomic_write import atomic_write_bytes
from f1se.io.backup import backup_slot
from f1se.project.game_detection import resolve_save_dat_path
from f1se.schema.enums import SKILL_NAMES

I32_MIN = -(2**31)
I32_MAX = 2**31 - 1

SAFE_EXACT_FIELDS = {
    "player.crippled_body_parts",
    "player.current_hp",
    "player.radiation",
    "player.poison",
    "pc.skill_points",
    "pc.level",
    "pc.experience",
}

ADVANCED_EXACT_FIELDS = {
    "player.base_hitpoints",
    "player.bonus_hitpoints",
    "player.base_action_points",
    "player.base_armor_class",
    "player.base_melee_damage",
    "player.starting_age",
    "player.gender",
    "pc.reputation_or_unknown",
    "pc.karma_or_unknown",
}

SAFE_PREFIXES = ("player.base_", "skills.", "kill_counts.", "tag_skills.", "traits.")
ADVANCED_PREFIXES = ("player.bonus_", "perks.")
DENIED_PREFIXES = ("inventory.", "header.")


def _category(name: str) -> str:
    if name in SAFE_EXACT_FIELDS or name.startswith(SAFE_PREFIXES):
        return "safe"
    if name in ADVANCED_EXACT_FIELDS or name.startswith(ADVANCED_PREFIXES):
        return "advanced"
    if name.startswith(DENIED_PREFIXES):
        return "denied"
    return "unsupported"


def _allowed(field, allow_advanced: bool) -> tuple[bool, str]:
    if field.type_name != "i32":
        return False, "only i32 fields are supported"
    if field.confidence not in {"high", "medium"}:
        return False, f"confidence {field.confidence} is not accepted"
    cat = _category(field.name)
    if cat == "safe":
        return True, "safe"
    if cat == "advanced" and allow_advanced:
        return True, "advanced"
    if cat == "advanced":
        return False, "requires --allow-advanced"
    return False, f"category {cat} is not supported"


def _validate(name: str, value: int) -> None:
    if not I32_MIN <= value <= I32_MAX:
        raise ValueError(f"{name}: outside signed i32 range")
    if name.startswith(("player.base_", "player.bonus_")) and not -10 <= value <= 20:
        raise ValueError(f"{name}: expected -10..20")
    if name.startswith("skills.") and not 0 <= value <= 300:
        raise ValueError(f"{name}: expected 0..300")
    if name.startswith("tag_skills.") and not (value == -1 or 0 <= value < len(SKILL_NAMES)):
        raise ValueError(f"{name}: expected -1 or a skill id")
    if name.startswith("traits.") and not (value == -1 or 0 <= value < 16):
        raise ValueError(f"{name}: expected -1 or 0..15")
    if name.startswith("perks.") and not 0 <= value <= 99:
        raise ValueError(f"{name}: expected 0..99")
    if name == "pc.level" and not 1 <= value <= 99:
        raise ValueError("pc.level: expected 1..99")
    if name == "pc.experience" and not 0 <= value <= 999_999_999:
        raise ValueError("pc.experience: expected 0..999999999")
    if name == "pc.skill_points" and not 0 <= value <= 999:
        raise ValueError("pc.skill_points: expected 0..999")


def writable_fields_payload(slot_path: str | Path, *, allow_advanced: bool = False) -> dict[str, Any]:
    save_path = resolve_save_dat_path(slot_path)
    save = Fallout2SaveDat.from_path(save_path)
    fields: dict[str, Any] = {}
    for name, field in sorted(save.fields.items()):
        ok, reason = _allowed(field, allow_advanced)
        doc = field.to_dict()
        doc["writable"] = ok
        doc["write_reason"] = reason
        doc["write_category"] = _category(name)
        fields[name] = doc
    return {
        "game_kind": "fallout2",
        "path": str(save_path),
        "slot_path": str(save_path.parent),
        "read_only": False,
        "allow_advanced": allow_advanced,
        "fields": fields,
        "warnings": list(dict.fromkeys(save.warnings)),
    }


def set_field(slot_path: str | Path, field_name: str, value: int, *, write: bool = False, allow_advanced: bool = False) -> dict[str, Any]:
    save_path = resolve_save_dat_path(slot_path)
    save = Fallout2SaveDat.from_path(save_path)
    if field_name not in save.fields:
        raise KeyError(f"unknown Fallout 2 field: {field_name}")
    field = save.fields[field_name]
    ok, reason = _allowed(field, allow_advanced)
    if not ok:
        raise ValueError(f"{field_name}: {reason}")
    if not isinstance(field.value, int):
        raise ValueError(f"{field_name}: not an integer field")
    _validate(field.name, value)
    old_bytes = bytes(save.data[field.abs_offset:field.abs_offset + field.size])
    new_bytes = int(value).to_bytes(field.size, "big", signed=True)
    payload = {
        "game_kind": "fallout2",
        "path": str(save_path),
        "slot_path": str(save_path.parent),
        "read_only": False,
        "field": field.to_dict() | {"writable": True, "write_reason": reason, "write_category": _category(field.name)},
        "diff": {
            "field": field.name,
            "offset": field.abs_offset,
            "offset_hex": f"0x{field.abs_offset:X}",
            "old_value": field.value,
            "new_value": value,
            "old_bytes": old_bytes.hex(),
            "new_bytes": new_bytes.hex(),
        },
        "changed": old_bytes != new_bytes,
        "written": False,
        "write_required": True,
        "backup_path": None,
        "warnings": list(dict.fromkeys(save.warnings)),
    }
    if not write:
        return payload
    save.data[field.abs_offset:field.abs_offset + field.size] = new_bytes
    backup_path = backup_slot(save_path.parent)
    atomic_write_bytes(save_path, bytes(save.data))
    payload["written"] = True
    payload["write_required"] = False
    payload["backup_path"] = str(backup_path)
    payload["sha256_after"] = Fallout2SaveDat.from_path(save_path).sha256
    return payload
