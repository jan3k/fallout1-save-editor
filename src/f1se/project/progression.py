"""Read-only Fallout 1 progression summary."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from f1se.format.slot import SaveSlot

FALLOUT1_LEVEL_MIN = 1
FALLOUT1_LEVEL_MAX = 21


def xp_threshold_for_level(level: int) -> int:
    """Return Fallout 1 cumulative XP threshold for a player level."""
    if level < FALLOUT1_LEVEL_MIN:
        raise ValueError("level must be >= 1")
    return ((level - 1) * level // 2) * 1000


def _field_int(slot: SaveSlot, name: str, default: int = 0) -> int:
    field = slot.save_dat.fields.get(name)
    if field is None:
        return default
    return int(field.value)


def _selected_trait_names(slot: SaveSlot) -> list[str]:
    return [row["name"] for row in slot.save_dat.selected_traits() if row.get("id") != -1]


def perk_interval_for_traits(traits: list[str]) -> int:
    # Fallout 1 Skilled changes perk cadence from every 3 levels to every 4.
    return 4 if "skilled" in set(traits) else 3


def next_perk_level(current_level: int, interval: int) -> int | None:
    if current_level >= FALLOUT1_LEVEL_MAX:
        return None
    for level in range(current_level + 1, FALLOUT1_LEVEL_MAX + 1):
        if level % interval == 0:
            return level
    return None


def progression_summary(slot_path: str | Path) -> dict[str, Any]:
    slot = SaveSlot.open(slot_path)
    sd = slot.save_dat
    h = sd.header
    level = _field_int(slot, "pc.level", 1)
    xp = _field_int(slot, "pc.experience", 0)
    skill_points = _field_int(slot, "pc.skill_points", 0)
    traits = _selected_trait_names(slot)
    interval = perk_interval_for_traits(traits)
    next_level = level + 1 if level < FALLOUT1_LEVEL_MAX else None
    current_threshold = xp_threshold_for_level(max(level, FALLOUT1_LEVEL_MIN))
    next_threshold = xp_threshold_for_level(next_level) if next_level is not None else None
    xp_to_next = max(0, next_threshold - xp) if next_threshold is not None else None
    perk_level = next_perk_level(level, interval)
    perk_xp_threshold = xp_threshold_for_level(perk_level) if perk_level is not None else None
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
        "level": {
            "current": level,
            "max": FALLOUT1_LEVEL_MAX,
            "next": next_level,
            "current_threshold": current_threshold,
            "next_threshold": next_threshold,
            "xp_to_next": xp_to_next,
            "at_or_above_max": level >= FALLOUT1_LEVEL_MAX,
        },
        "experience": xp,
        "skill_points": skill_points,
        "karma": _field_int(slot, "pc.karma", 0),
        "reputation": _field_int(slot, "pc.reputation", 0),
        "traits": traits,
        "perk_cadence": {
            "interval_levels": interval,
            "reason": "skilled trait" if interval == 4 else "default",
            "next_perk_level": perk_level,
            "next_perk_xp_threshold": perk_xp_threshold,
            "xp_to_next_perk_level": max(0, perk_xp_threshold - xp) if perk_xp_threshold is not None else None,
        },
        "warnings": list(dict.fromkeys(sd.warnings)),
    }
