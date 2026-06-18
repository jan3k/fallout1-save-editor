"""Synthetic Fallout 2 SAVE.DAT fixtures for unit tests.

The bytes generated here are deliberately minimal and artificial. They are not
private game saves and should never be treated as proof that all real Fallout 2
layouts are writable.
"""
from __future__ import annotations

from f1se.format.fallout2.save_dat import (
    FUNCTION13_PC_STATS_SIZE,
    FUNCTION15_TRAITS_SIZE,
    FUNCTION7_KILL_COUNT_SIZE,
    FUNCTION8_TAG_SKILL_SIZE,
    FUNCTION9_PERK_SIZE,
)
from f1se.format.function_5_player_object import FP_SIGNATURE
from f1se.format.function_6_critter_stats import FUNCTION6_SIZE, SKILLS_REL_OFFSET
from f1se.format.header import HEADER_SIZE, SAVE_SIGNATURE


def _put_i32(data: bytearray, offset: int, value: int) -> None:
    data[offset:offset + 4] = int(value).to_bytes(4, "big", signed=True)


def _put_u16(data: bytearray, offset: int, value: int) -> None:
    data[offset:offset + 2] = int(value).to_bytes(2, "big", signed=False)


def _put_cstr(data: bytearray, offset: int, size: int, value: str) -> None:
    raw = value.encode("ascii")[:size - 1]
    data[offset:offset + size] = b"\x00" * size
    data[offset:offset + len(raw)] = raw


def build_minimal_fallout2_save() -> bytes:
    f5_start = HEADER_SIZE + 0x20
    f6_start = f5_start + 0x84
    f7_start = f6_start + FUNCTION6_SIZE
    f8_start = f7_start + FUNCTION7_KILL_COUNT_SIZE
    f9_start = f8_start + FUNCTION8_TAG_SKILL_SIZE
    f13_start = f9_start + FUNCTION9_PERK_SIZE
    f15_start = f13_start + FUNCTION13_PC_STATS_SIZE
    end = f15_start + FUNCTION15_TRAITS_SIZE + 0x40

    data = bytearray(b"\x00" * end)
    data[0:len(SAVE_SIGNATURE)] = SAVE_SIGNATURE
    _put_u16(data, 0x18, 1)
    _put_u16(data, 0x1A, 2)
    data[0x1C] = ord("d")
    _put_cstr(data, 0x1D, 0x20, "Chosen One")
    _put_cstr(data, 0x3D, 0x1E, "Synthetic FO2")
    _put_u16(data, 0x5B, 18)
    _put_u16(data, 0x5D, 6)
    _put_u16(data, 0x5F, 2026)
    _put_u16(data, 0x65, 7)
    _put_u16(data, 0x67, 25)
    _put_u16(data, 0x69, 2241)
    _put_i32(data, 0x6B, 12345)
    _put_u16(data, 0x6F, 0)
    _put_u16(data, 0x71, 1)
    _put_cstr(data, 0x73, 0x10, "ARROYO.MAP")

    data[f5_start:f5_start + 4] = FP_SIGNATURE
    _put_i32(data, f5_start + 0x1C, 0)
    _put_i32(data, f5_start + 0x20, 0x01000001)
    _put_i32(data, f5_start + 0x28, 0)
    _put_i32(data, f5_start + 0x48, 0)
    _put_i32(data, f5_start + 0x64, 0)
    _put_i32(data, f5_start + 0x74, 32)
    _put_i32(data, f5_start + 0x78, 0)
    _put_i32(data, f5_start + 0x7C, 0)
    _put_i32(data, f6_start - 4, 0)

    special = [5, 6, 7, 4, 8, 6, 5]
    for idx, value in enumerate(special):
        _put_i32(data, f6_start + 0x08 + idx * 4, value)
    for rel, value in {
        0x24: 32,
        0x28: 8,
        0x2C: 6,
        0x34: 2,
        0x38: 175,
        0x3C: 12,
        0x40: 1,
        0x44: 5,
        0x8C: 20,
        0x90: 0,
    }.items():
        _put_i32(data, f6_start + rel, value)
    for idx in range(18):
        _put_i32(data, f6_start + SKILLS_REL_OFFSET + idx * 4, 10 + idx)

    for idx in range(FUNCTION7_KILL_COUNT_SIZE // 4):
        _put_i32(data, f7_start + idx * 4, idx)
    for idx, skill_id in enumerate([0, 3, 13, 14]):
        _put_i32(data, f8_start + idx * 4, skill_id)
    for idx in range(FUNCTION9_PERK_SIZE // 4):
        _put_i32(data, f9_start + idx * 4, 0)
    _put_i32(data, f13_start + 0x00, 12)
    _put_i32(data, f13_start + 0x04, 3)
    _put_i32(data, f13_start + 0x08, 1500)
    _put_i32(data, f13_start + 0x0C, 0)
    _put_i32(data, f13_start + 0x10, 0)
    _put_i32(data, f15_start + 0x00, -1)
    _put_i32(data, f15_start + 0x04, -1)
    return bytes(data)
