"""Read-only Fallout 1 character summary payload."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from f1se.format.slot import SaveSlot
from f1se.schema.enums import CRIPPLED_PART_FLAGS, SKILL_NAMES, SPECIAL_NAMES


def _field_value(slot: SaveSlot, name: str, default: Any = None) -> Any:
    field = slot.save_dat.fields.get(name)
    if field is None:
        return default
    return field.value


def _status_effects(slot: SaveSlot) -> dict[str, Any]:
    sd = slot.save_dat
    crippled = int(_field_value(slot, "player.crippled_body_parts", 0))
    return {
        "current_hp": int(_field_value(slot, "player.current_hp", 0)),
        "max_hp": int(_field_value(slot, "player.base_hitpoints", 0)),
        "radiation": int(_field_value(slot, "player.radiation", 0)),
        "poison": int(_field_value(slot, "player.poison", 0)),
        "crippled_body_parts": crippled,
        "crippled_body_parts_hex": f"0x{crippled:X}",
        "crippled_flags": {
            name: bool(crippled & mask)
            for name, mask in CRIPPLED_PART_FLAGS.items()
        },
        "warnings": [w for w in sd.warnings if "crippled" in w.lower() or "hp" in w.lower() or "poison" in w.lower() or "radiation" in w.lower()],
    }


def _special(slot: SaveSlot) -> dict[str, Any]:
    effective = slot.save_dat.effective_special()
    rows: dict[str, Any] = {}
    for stat in SPECIAL_NAMES:
        rows[stat] = {
            "base": int(_field_value(slot, f"player.base_{stat}", 0)),
            "bonus": int(_field_value(slot, f"player.bonus_{stat}", 0)),
            "static_trait": int(effective.get(stat, {}).get("static_trait", 0)),
            "effective_static": int(effective.get(stat, {}).get("effective_static", 0)),
            "base_offset_hex": slot.save_dat.fields[f"player.base_{stat}"].to_dict()["abs_offset_hex"],
        }
    return rows


def _skills(slot: SaveSlot) -> dict[str, Any]:
    tag_ids = []
    for idx in range(4):
        value = int(_field_value(slot, f"tag_skills.{idx}", -1))
        tag_ids.append(value)
    tagged = {
        SKILL_NAMES[idx]: True
        for idx in tag_ids
        if 0 <= idx < len(SKILL_NAMES)
    }
    rows: dict[str, Any] = {}
    for skill in SKILL_NAMES:
        field = slot.save_dat.fields[f"skills.{skill}"]
        rows[skill] = {
            "saved_points_over_base": int(field.value),
            "tagged": bool(tagged.get(skill, False)),
            "offset_hex": field.to_dict()["abs_offset_hex"],
            "risk": field.risk,
        }
    return {"tag_skill_ids": tag_ids, "skills": rows}


def _active_perks(slot: SaveSlot) -> list[dict[str, Any]]:
    perks: list[dict[str, Any]] = []
    for name, field in sorted(slot.save_dat.fields.items(), key=lambda item: item[1].abs_offset):
        if not name.startswith("perks."):
            continue
        rank = int(field.value)
        if rank <= 0:
            continue
        perks.append({
            "name": name.split(".", 1)[1],
            "rank": rank,
            "offset_hex": field.to_dict()["abs_offset_hex"],
            "risk": field.risk,
        })
    return perks


def _nonzero_kills(slot: SaveSlot) -> list[dict[str, Any]]:
    kills: list[dict[str, Any]] = []
    for name, field in sorted(slot.save_dat.fields.items(), key=lambda item: item[1].abs_offset):
        if not name.startswith("kill_counts."):
            continue
        count = int(field.value)
        if count <= 0:
            continue
        kills.append({
            "name": name.split(".", 1)[1],
            "count": count,
            "offset_hex": field.to_dict()["abs_offset_hex"],
        })
    return kills


def _inventory_summary(slot: SaveSlot) -> dict[str, Any]:
    items = slot.save_dat.player_object.inventory
    known = [item for item in items if item.known_pid]
    unknown = [item for item in items if not item.known_pid]
    total_quantity = sum(int(item.quantity) for item in items)
    top_items = sorted(items, key=lambda item: (-int(item.quantity), item.index))[:10]
    return {
        "inventory_count": slot.save_dat.player_object.inventory_count,
        "parsed_item_count": len(items),
        "known_pid_count": len(known),
        "unknown_pid_count": len(unknown),
        "total_quantity": total_quantity,
        "top_items": [
            {
                "index": item.index,
                "name": item.object_name,
                "pid": item.pid,
                "quantity": item.quantity,
                "type": item.type_name,
                "offset_hex": f"0x{item.start:X}",
                "confidence": item.confidence,
            }
            for item in top_items
        ],
    }


def character_summary(slot_path: str | Path) -> dict[str, Any]:
    slot = SaveSlot.open(slot_path)
    sd = slot.save_dat
    h = sd.header
    return {
        "game_kind": "fallout1",
        "slot_path": str(slot.path),
        "read_only": True,
        "identity": {
            "player_name": h.player_name,
            "save_name": h.save_name,
            "version": h.version,
            "signature": h.signature,
            "saved_date": f"{h.real_year:04d}-{h.real_month:02d}-{h.real_day:02d}",
            "current_map_file": h.current_map_file,
            "map_id": h.map_id,
            "elevation": h.elevation,
            "sha256": sd.sha256,
        },
        "progression": {
            "level": int(_field_value(slot, "pc.level", 0)),
            "experience": int(_field_value(slot, "pc.experience", 0)),
            "skill_points": int(_field_value(slot, "pc.skill_points", 0)),
            "reputation": int(_field_value(slot, "pc.reputation", 0)),
            "karma": int(_field_value(slot, "pc.karma", 0)),
        },
        "status_effects": _status_effects(slot),
        "special": _special(slot),
        "skills": _skills(slot),
        "traits": slot.save_dat.selected_traits(),
        "trait_effect_notes": slot.save_dat.trait_effect_notes(),
        "active_perks": _active_perks(slot),
        "nonzero_kill_counts": _nonzero_kills(slot),
        "inventory_summary": _inventory_summary(slot),
        "warnings": list(dict.fromkeys(sd.warnings)),
    }
