from __future__ import annotations

from pathlib import Path
from typing import Any

from f1se.format.slot import SaveSlot
from f1se.io.atomic_write import atomic_write_bytes
from f1se.io.backup import backup_slot
from f1se.project.fallout2_write import set_field as fallout2_set_field
from f1se.project.game_detection import detect_game
from f1se.project.game_profile import GameKind
from f1se.schema.enums import SKILL_NAMES

SKILL_ALIASES = {
    "retoryka": "speech",
    "retoryki": "speech",
    "speech": "speech",
    "mowa": "speech",
    "smallguns": "small_guns",
    "small_guns": "small_guns",
    "bigguns": "big_guns",
    "big_guns": "big_guns",
    "energyweapons": "energy_weapons",
    "energy_weapons": "energy_weapons",
    "unarmed": "unarmed",
    "melee": "melee_weapons",
    "meleeweapons": "melee_weapons",
    "melee_weapons": "melee_weapons",
    "throwing": "throwing",
    "firstaid": "first_aid",
    "first_aid": "first_aid",
    "doctor": "doctor",
    "sneak": "sneak",
    "lockpick": "lockpick",
    "steal": "steal",
    "traps": "traps",
    "science": "science",
    "repair": "repair",
    "barter": "barter",
    "gambling": "gambling",
    "outdoorsman": "outdoorsman",
}


def normalize_skill_name(name: str) -> str:
    key = name.strip().lower().replace("-", "_").replace(" ", "_")
    compact = key.replace("_", "")
    if key in SKILL_NAMES:
        return key
    if key in SKILL_ALIASES:
        return SKILL_ALIASES[key]
    if compact in SKILL_ALIASES:
        return SKILL_ALIASES[compact]
    allowed = ", ".join(SKILL_NAMES + ["retoryka"])
    raise ValueError(f"unknown skill: {name}; expected one of: {allowed}")


def _validate_skill_value(value: int, *, allow_out_of_range: bool = False) -> None:
    if allow_out_of_range:
        if not -100 <= value <= 999:
            raise ValueError("skill debug value must be in range -100..999")
        return
    if not 0 <= value <= 300:
        raise ValueError("skill value must be in range 0..300")


def _diff_to_dict(diff) -> dict[str, Any]:
    return {
        "file": diff.file_name,
        "offset": diff.offset,
        "offset_hex": f"0x{diff.offset:X}",
        "old_bytes": diff.old.hex(),
        "new_bytes": diff.new.hex(),
        "field": diff.field_name,
    }


def _set_fallout1(slot_path: str | Path, skill: str, value: int, *, write: bool, allow_out_of_range: bool) -> dict[str, Any]:
    _validate_skill_value(value, allow_out_of_range=allow_out_of_range)
    slot = SaveSlot.open(slot_path)
    field_name = f"skills.{skill}"
    old_value = int(slot.save_dat.fields[field_name].value)
    diffs = slot.save_dat.set_field(field_name, value, allow_out_of_range=allow_out_of_range, mode="raw")
    payload = {
        "game_kind": "fallout1",
        "slot_path": str(slot.path),
        "save_dat": str(slot.path / "SAVE.DAT"),
        "skill": skill,
        "field": field_name,
        "old_value": old_value,
        "new_value": value,
        "diffs": [_diff_to_dict(diff) for diff in diffs],
        "changed": bool(diffs),
        "written": False,
        "write_required": True,
        "backup_path": None,
        "read_only": False,
        "warnings": list(dict.fromkeys(slot.save_dat.warnings)),
        "note": "skills.* values are saved points over base, not final calculated skill percentage",
    }
    if not write:
        return payload
    backup_path = backup_slot(slot.path)
    atomic_write_bytes(slot.path / "SAVE.DAT", bytes(slot.save_dat.data))
    payload["written"] = True
    payload["write_required"] = False
    payload["backup_path"] = str(backup_path)
    payload["sha256_after"] = SaveSlot.open(slot.path).save_dat.sha256
    return payload


def _set_fallout2(slot_path: str | Path, skill: str, value: int, *, write: bool, allow_out_of_range: bool) -> dict[str, Any]:
    _validate_skill_value(value, allow_out_of_range=allow_out_of_range)
    field_name = f"skills.{skill}"
    payload = fallout2_set_field(slot_path, field_name, value, write=write, allow_advanced=False)
    payload["skill"] = skill
    payload["note"] = "skills.* values are saved points over base, not final calculated skill percentage"
    return payload


def set_skill(slot_path: str | Path, skill_name: str, value: int, *, game: str = "auto", write: bool = False, allow_out_of_range: bool = False) -> dict[str, Any]:
    skill = normalize_skill_name(skill_name)
    requested = game.lower()
    if requested == "fallout1":
        return _set_fallout1(slot_path, skill, value, write=write, allow_out_of_range=allow_out_of_range)
    if requested == "fallout2":
        return _set_fallout2(slot_path, skill, value, write=write, allow_out_of_range=allow_out_of_range)
    detected = detect_game(slot_path).game_kind
    if detected is GameKind.FALLOUT2:
        return _set_fallout2(slot_path, skill, value, write=write, allow_out_of_range=allow_out_of_range)
    return _set_fallout1(slot_path, skill, value, write=write, allow_out_of_range=allow_out_of_range)
