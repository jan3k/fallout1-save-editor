"""Function 6: critter/player stat block."""
from __future__ import annotations

from dataclasses import dataclass

from f1se.io.endian import i32be
from f1se.schema.enums import SKILL_NAMES, SPECIAL_NAMES

FUNCTION6_SIZE = 0x178

STAT_REL_OFFSETS = {
    "tabs_flags": 0x04,
    "base_strength": 0x08,
    "base_perception": 0x0C,
    "base_endurance": 0x10,
    "base_charisma": 0x14,
    "base_intelligence": 0x18,
    "base_agility": 0x1C,
    "base_luck": 0x20,
    "base_hitpoints": 0x24,
    "base_action_points": 0x28,
    "base_armor_class": 0x2C,
    "base_unarmed_damage_unused": 0x30,
    "base_melee_damage": 0x34,
    "base_carry_weight": 0x38,
    "base_sequence": 0x3C,
    "base_healing_rate": 0x40,
    "base_critical_chance": 0x44,
    "base_better_criticals": 0x48,
    "base_damage_threshold": 0x4C,
    "base_damage_threshold_laser": 0x50,
    "base_damage_threshold_fire": 0x54,
    "base_damage_threshold_plasma": 0x58,
    "base_damage_threshold_electrical": 0x5C,
    "base_damage_threshold_emp": 0x60,
    "base_damage_threshold_explosion": 0x64,
    "base_damage_resistance": 0x68,
    "base_damage_resistance_laser": 0x6C,
    "base_damage_resistance_fire": 0x70,
    "base_damage_resistance_plasma": 0x74,
    "base_damage_resistance_electrical": 0x78,
    "base_damage_resistance_emp": 0x7C,
    "base_damage_resistance_explosion": 0x80,
    "radiation_resistance": 0x84,
    "poison_resistance": 0x88,
    "starting_age": 0x8C,
    "gender": 0x90,
    "bonus_strength": 0x94,
    "bonus_perception": 0x98,
    "bonus_endurance": 0x9C,
    "bonus_charisma": 0xA0,
    "bonus_intelligence": 0xA4,
    "bonus_agility": 0xA8,
    "bonus_luck": 0xAC,
    "bonus_hitpoints": 0xB0,
    "bonus_action_points": 0xB4,
    "bonus_armor_class": 0xB8,
    "bonus_unarmed_damage_unused": 0xBC,
    "bonus_melee_damage": 0xC0,
    "bonus_carry_weight": 0xC4,
    "bonus_sequence": 0xC8,
    "bonus_healing_rate": 0xCC,
    "bonus_critical_chance": 0xD0,
    "bonus_better_criticals": 0xD4,
    "bonus_damage_threshold": 0xD8,
    "bonus_damage_threshold_laser": 0xDC,
    "bonus_damage_threshold_fire": 0xE0,
    "bonus_damage_threshold_plasma": 0xE4,
    "bonus_damage_threshold_electrical": 0xE8,
    "bonus_damage_threshold_emp": 0xEC,
    "bonus_damage_threshold_explosion": 0xF0,
    "bonus_damage_resistance": 0xF4,
    "bonus_damage_resistance_laser": 0xF8,
    "bonus_damage_resistance_fire": 0xFC,
    "bonus_damage_resistance_plasma": 0x100,
    "bonus_damage_resistance_electrical": 0x104,
    "bonus_damage_resistance_emp": 0x108,
    "bonus_damage_resistance_explosion": 0x10C,
    "bonus_radiation_resistance": 0x110,
    "bonus_poison_resistance": 0x114,
    "bonus_age": 0x118,
    "bonus_gender": 0x11C,
    "proto_id": 0x168,
    "message_id": 0x16C,
    "description_line": 0x174,
}

SKILLS_REL_OFFSET = 0x120


@dataclass(slots=True)
class CritterStats:
    start: int
    end: int
    values: dict[str, int]
    skills: dict[str, int]

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "start_hex": f"0x{self.start:X}",
            "end": self.end,
            "end_hex": f"0x{self.end:X}",
            "size": self.end - self.start,
            "values": dict(self.values),
            "skills": dict(self.skills),
        }


def parse_function6(data: bytes | bytearray, start: int) -> CritterStats:
    end = start + FUNCTION6_SIZE
    if end > len(data):
        raise ValueError("Function 6 extends beyond EOF")
    values = {name: i32be(data, start + rel) for name, rel in STAT_REL_OFFSETS.items()}
    skills = {name: i32be(data, start + SKILLS_REL_OFFSET + idx * 4) for idx, name in enumerate(SKILL_NAMES)}
    return CritterStats(start=start, end=end, values=values, skills=skills)


def derived_stat_targets(strength: int, perception: int, endurance: int, agility: int, luck: int) -> dict[str, int]:
    """Conservative Fallout 1 derived-stat recalculation for semantic SPECIAL edits.

    This intentionally covers only stable, formulaic secondary stats. Damage
    thresholds/resistances and perk/trait effects are not recomputed here.
    """
    return {
        "player.base_hitpoints": strength + (endurance * 2) + 15,
        "player.base_action_points": agility // 2 + 5,
        "player.base_armor_class": agility,
        "player.base_melee_damage": max(1, strength - 5),
        "player.base_carry_weight": 25 + strength * 25,
        "player.base_sequence": perception * 2,
        "player.base_healing_rate": max(1, endurance // 3),
        "player.base_critical_chance": luck,
        "player.radiation_resistance": endurance * 2,
        "player.poison_resistance": endurance * 5,
    }
