"""Read-only Fallout 1 derived-stat consistency report."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from f1se.format.function_6_critter_stats import derived_stat_targets
from f1se.format.slot import SaveSlot
from f1se.schema.enums import SPECIAL_NAMES


def _field_int(slot: SaveSlot, name: str) -> int:
    return int(slot.save_dat.fields[name].value)


def _offset_hex(slot: SaveSlot, name: str) -> str:
    return slot.save_dat.fields[name].to_dict()["abs_offset_hex"]


def derived_stats_report(slot_path: str | Path) -> dict[str, Any]:
    slot = SaveSlot.open(slot_path)
    sd = slot.save_dat
    h = sd.header
    special = {stat: _field_int(slot, f"player.base_{stat}") for stat in SPECIAL_NAMES}
    targets = derived_stat_targets(
        special["strength"],
        special["perception"],
        special["endurance"],
        special["agility"],
        special["luck"],
    )

    rows: dict[str, Any] = {}
    mismatches: list[dict[str, Any]] = []
    for field_name, expected in targets.items():
        if field_name not in sd.fields:
            rows[field_name] = {
                "present": False,
                "expected": expected,
                "actual": None,
                "delta": None,
                "matches": False,
                "offset_hex": None,
                "risk": "missing",
            }
            mismatches.append({"field": field_name, "expected": expected, "actual": None, "delta": None, "reason": "field missing"})
            continue
        actual = _field_int(slot, field_name)
        delta = actual - expected
        matches = actual == expected
        field = sd.fields[field_name]
        row = {
            "present": True,
            "expected": expected,
            "actual": actual,
            "delta": delta,
            "matches": matches,
            "offset_hex": _offset_hex(slot, field_name),
            "risk": field.risk,
        }
        rows[field_name] = row
        if not matches:
            mismatches.append({"field": field_name, "expected": expected, "actual": actual, "delta": delta, "reason": "saved value differs from formula target"})

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
        "source_special": special,
        "formula_scope": "stable Fallout 1 formulaic secondary stats only; perks, armor, temporary effects and many trait side effects are intentionally excluded",
        "derived_stats": rows,
        "mismatches": mismatches,
        "summary": {
            "checked_count": len(rows),
            "mismatch_count": len(mismatches),
            "ok": not mismatches,
        },
        "warnings": list(dict.fromkeys(sd.warnings)),
    }
