"""Read-only Fallout 1 combat summary payload."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from f1se.format.slot import SaveSlot
from f1se.schema.enums import CRIPPLED_PART_FLAGS, SPECIAL_NAMES

COMBAT_DERIVED_FIELDS = (
    "player.current_hp",
    "player.base_hitpoints",
    "player.base_action_points",
    "player.base_armor_class",
    "player.base_melee_damage",
    "player.base_carry_weight",
    "player.base_sequence",
    "player.base_healing_rate",
    "player.base_critical_chance",
    "player.radiation_resistance",
    "player.poison_resistance",
    "player.radiation",
    "player.poison",
    "player.crippled_body_parts",
)


def _field_int(slot: SaveSlot, name: str, default: int = 0) -> int:
    field = slot.save_dat.fields.get(name)
    if field is None:
        return default
    return int(field.value)


def _field_row(slot: SaveSlot, name: str) -> dict[str, Any]:
    field = slot.save_dat.fields.get(name)
    if field is None:
        return {
            "present": False,
            "value": None,
            "offset_hex": None,
            "risk": "missing",
            "writable": False,
        }
    return {
        "present": True,
        "value": int(field.value),
        "offset_hex": field.to_dict()["abs_offset_hex"],
        "risk": field.risk,
        "writable": bool(field.writable),
    }


def _crippled_payload(mask: int) -> dict[str, Any]:
    return {
        "value": mask,
        "hex": f"0x{mask:X}",
        "flags": {name: bool(mask & bit) for name, bit in CRIPPLED_PART_FLAGS.items()},
        "active": [name for name, bit in CRIPPLED_PART_FLAGS.items() if mask & bit],
    }


def combat_summary(slot_path: str | Path) -> dict[str, Any]:
    slot = SaveSlot.open(slot_path)
    sd = slot.save_dat
    h = sd.header
    current_hp = _field_int(slot, "player.current_hp")
    max_hp = _field_int(slot, "player.base_hitpoints")
    crippled = _field_int(slot, "player.crippled_body_parts")
    combat_fields = {name: _field_row(slot, name) for name in COMBAT_DERIVED_FIELDS}
    return {
        "game_kind": "fallout1",
        "slot_path": str(slot.path),
        "read_only": True,
        "identity": {
            "player_name": h.player_name,
            "save_name": h.save_name,
            "version": h.version,
            "current_map_file": h.current_map_file,
            "saved_date": f"{h.real_year:04d}-{h.real_month:02d}-{h.real_day:02d}",
            "sha256": sd.sha256,
        },
        "special": {stat: _field_int(slot, f"player.base_{stat}") for stat in SPECIAL_NAMES},
        "hp": {
            "current": current_hp,
            "max": max_hp,
            "missing": max(0, max_hp - current_hp),
            "over_max": current_hp > max_hp,
            "percent": round((current_hp / max_hp) * 100, 2) if max_hp > 0 else None,
        },
        "action_points": _field_int(slot, "player.base_action_points"),
        "armor_class": _field_int(slot, "player.base_armor_class"),
        "melee_damage": _field_int(slot, "player.base_melee_damage"),
        "carry_weight": _field_int(slot, "player.base_carry_weight"),
        "sequence": _field_int(slot, "player.base_sequence"),
        "healing_rate": _field_int(slot, "player.base_healing_rate"),
        "critical_chance": _field_int(slot, "player.base_critical_chance"),
        "resistances": {
            "radiation": _field_int(slot, "player.radiation_resistance"),
            "poison": _field_int(slot, "player.poison_resistance"),
        },
        "status_effects": {
            "radiation": _field_int(slot, "player.radiation"),
            "poison": _field_int(slot, "player.poison"),
            "crippled_body_parts": _crippled_payload(crippled),
        },
        "fields": combat_fields,
        "summary": {
            "checked_field_count": len(combat_fields),
            "active_crippled_part_count": len(_crippled_payload(crippled)["active"]),
            "has_radiation": _field_int(slot, "player.radiation") > 0,
            "has_poison": _field_int(slot, "player.poison") > 0,
            "is_over_max_hp": current_hp > max_hp,
        },
        "warnings": list(dict.fromkeys(sd.warnings)),
    }
