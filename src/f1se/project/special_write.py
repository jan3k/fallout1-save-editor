from __future__ import annotations

from pathlib import Path
from typing import Any

from f1se.format.slot import SaveSlot
from f1se.io.atomic_write import atomic_write_bytes
from f1se.io.backup import backup_slot
from f1se.project.fallout2_write import set_field as fallout2_set_field
from f1se.project.game_detection import detect_game
from f1se.project.game_profile import GameKind
from f1se.schema.enums import SPECIAL_NAMES

SPECIAL_ALIASES = {
    "s": "strength",
    "str": "strength",
    "strength": "strength",
    "p": "perception",
    "per": "perception",
    "perception": "perception",
    "e": "endurance",
    "end": "endurance",
    "endurance": "endurance",
    "c": "charisma",
    "cha": "charisma",
    "charisma": "charisma",
    "i": "intelligence",
    "int": "intelligence",
    "intelligence": "intelligence",
    "a": "agility",
    "agi": "agility",
    "agility": "agility",
    "l": "luck",
    "luc": "luck",
    "luck": "luck",
}


def normalize_special_name(name: str) -> str:
    key = name.strip().lower().replace(".", "")
    if key not in SPECIAL_ALIASES:
        allowed = ", ".join(SPECIAL_NAMES)
        raise ValueError(f"unknown SPECIAL stat: {name}; expected one of: {allowed}")
    return SPECIAL_ALIASES[key]


def _validate_special_value(value: int, *, allow_out_of_range: bool = False) -> None:
    if allow_out_of_range:
        if not -10 <= value <= 20:
            raise ValueError("SPECIAL debug value must be in range -10..20")
        return
    if not 1 <= value <= 10:
        raise ValueError("SPECIAL value must be in range 1..10")


def _diff_to_dict(diff) -> dict[str, Any]:
    return {
        "file": diff.file_name,
        "offset": diff.offset,
        "offset_hex": f"0x{diff.offset:X}",
        "old_bytes": diff.old.hex(),
        "new_bytes": diff.new.hex(),
        "field": diff.field_name,
    }


def _set_fallout1(slot_path: str | Path, stat: str, value: int, *, write: bool, mode: str, allow_out_of_range: bool) -> dict[str, Any]:
    _validate_special_value(value, allow_out_of_range=allow_out_of_range)
    slot = SaveSlot.open(slot_path)
    field_name = f"player.base_{stat}"
    old_value = int(slot.save_dat.fields[field_name].value)
    diffs = slot.save_dat.set_field(field_name, value, allow_out_of_range=allow_out_of_range, mode=mode)
    payload = {
        "game_kind": "fallout1",
        "slot_path": str(slot.path),
        "save_dat": str(slot.path / "SAVE.DAT"),
        "stat": stat,
        "field": field_name,
        "old_value": old_value,
        "new_value": value,
        "mode": mode,
        "diffs": [_diff_to_dict(diff) for diff in diffs],
        "changed": bool(diffs),
        "written": False,
        "write_required": True,
        "backup_path": None,
        "read_only": False,
        "warnings": list(dict.fromkeys(slot.save_dat.warnings)),
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


def _set_fallout2(slot_path: str | Path, stat: str, value: int, *, write: bool, allow_out_of_range: bool) -> dict[str, Any]:
    _validate_special_value(value, allow_out_of_range=allow_out_of_range)
    field_name = f"player.base_{stat}"
    payload = fallout2_set_field(slot_path, field_name, value, write=write, allow_advanced=False)
    payload["stat"] = stat
    payload["mode"] = "single-field"
    return payload


def set_special(slot_path: str | Path, stat_name: str, value: int, *, game: str = "auto", write: bool = False, mode: str = "semantic", allow_out_of_range: bool = False) -> dict[str, Any]:
    stat = normalize_special_name(stat_name)
    requested = game.lower()
    if requested == "fallout1":
        return _set_fallout1(slot_path, stat, value, write=write, mode=mode, allow_out_of_range=allow_out_of_range)
    if requested == "fallout2":
        return _set_fallout2(slot_path, stat, value, write=write, allow_out_of_range=allow_out_of_range)
    detected = detect_game(slot_path).game_kind
    if detected is GameKind.FALLOUT2:
        return _set_fallout2(slot_path, stat, value, write=write, allow_out_of_range=allow_out_of_range)
    return _set_fallout1(slot_path, stat, value, write=write, mode=mode, allow_out_of_range=allow_out_of_range)
