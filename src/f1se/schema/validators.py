"""Field validators."""
from __future__ import annotations

from .enums import PC_LEVEL_MAX, PRIMARY_STAT_MAX, PRIMARY_STAT_MIN, SKILL_COUNT, TRAIT_COUNT


def validate_i32(value: int) -> None:
    if not (-2_147_483_648 <= value <= 2_147_483_647):
        raise ValueError("value does not fit signed 32-bit integer")


def validate_special(value: int, allow_out_of_range: bool = False) -> None:
    validate_i32(value)
    if not allow_out_of_range and not (PRIMARY_STAT_MIN <= value <= PRIMARY_STAT_MAX):
        raise ValueError(f"SPECIAL base value must be {PRIMARY_STAT_MIN}..{PRIMARY_STAT_MAX}; use --allow-out-of-range to override")


def validate_bonus_stat(value: int) -> None:
    validate_i32(value)
    if not (-50 <= value <= 50):
        raise ValueError("bonus stat outside conservative -50..50 range")


def validate_hp(value: int) -> None:
    validate_i32(value)
    if not (0 <= value <= 9999):
        raise ValueError("HP must be 0..9999")


def validate_meter(value: int) -> None:
    validate_i32(value)
    if not (0 <= value <= 2000):
        raise ValueError("radiation/poison must be 0..2000")


def validate_skill_over_base(value: int) -> None:
    validate_i32(value)
    if not (0 <= value <= 300):
        raise ValueError("saved skill points-over-base must be 0..300")


def validate_tag_skill(value: int) -> None:
    validate_i32(value)
    if value != -1 and not (0 <= value < SKILL_COUNT):
        raise ValueError("tag skill must be -1 or 0..17")


def validate_trait(value: int) -> None:
    validate_i32(value)
    if value != -1 and not (0 <= value < TRAIT_COUNT):
        raise ValueError("trait must be -1 or 0..15")


def validate_level(value: int) -> None:
    validate_i32(value)
    if not (1 <= value <= PC_LEVEL_MAX):
        raise ValueError(f"PC level must be 1..{PC_LEVEL_MAX}")


def validate_xp(value: int) -> None:
    validate_i32(value)
    if not (0 <= value <= 99_999_999):
        raise ValueError("experience must be 0..99,999,999")


def validate_karma(value: int) -> None:
    validate_i32(value)
    if not (-1_000_000 <= value <= 1_000_000):
        raise ValueError("karma outside conservative -1,000,000..1,000,000 range")


def validate_reputation(value: int) -> None:
    validate_i32(value)
    if not (-1000 <= value <= 1000):
        raise ValueError("reputation outside conservative -1000..1000 range")


def validate_quantity(value: int) -> None:
    validate_i32(value)
    if not (0 <= value <= 999_999):
        raise ValueError("quantity must be 0..999999")


def validate_perk_rank(value: int) -> None:
    validate_i32(value)
    if not (0 <= value <= 99):
        raise ValueError("perk rank must be 0..99")


def validate_option_bool(value: int) -> None:
    validate_i32(value)
    if value not in (0, 1):
        raise ValueError("option boolean must be 0 or 1")



def validate_skill_points(value: int) -> None:
    validate_i32(value)
    if not (0 <= value <= 999):
        raise ValueError("unspent skill points must be 0..999")


def validate_kill_count(value: int) -> None:
    validate_i32(value)
    if not (0 <= value <= 999_999):
        raise ValueError("kill count must be 0..999999")


def validate_crippled_body_parts(value: int) -> None:
    validate_i32(value)
    if not (0 <= value <= 0x1F):
        raise ValueError("crippled body-part bitfield must fit known Fallout 1 bits 0x00..0x1F")


def validate_any_i32(value: int) -> None:
    validate_i32(value)
