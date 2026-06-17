"""SAVE.DAT header parser."""
from __future__ import annotations

from dataclasses import dataclass

from f1se.io.endian import c_string, u16be, u32be

SAVE_SIGNATURE = b"FALLOUT SAVE FILE"
HEADER_SIZE = 0x7563


@dataclass(slots=True)
class SaveHeader:
    signature: str
    version: str
    player_name: str
    save_name: str
    real_day: int
    real_month: int
    real_year: int
    game_month: int
    game_day: int
    game_year: int
    game_time: int
    elevation: int
    map_id: int
    current_map_file: str
    screenshot_offset: int = 0x83
    screenshot_size: int = 0x7460

    def to_dict(self) -> dict:
        return {
            "signature": self.signature,
            "version": self.version,
            "player_name": self.player_name,
            "save_name": self.save_name,
            "real_date": f"{self.real_year:04d}-{self.real_month:02d}-{self.real_day:02d}",
            "game_date": {"month": self.game_month, "day": self.game_day, "year": self.game_year},
            "game_time": self.game_time,
            "elevation": self.elevation,
            "map_id": self.map_id,
            "current_map_file": self.current_map_file,
            "screenshot_offset": self.screenshot_offset,
            "screenshot_size": self.screenshot_size,
        }


def parse_header(data: bytes | bytearray) -> SaveHeader:
    if len(data) < HEADER_SIZE:
        raise ValueError(f"SAVE.DAT too small for Fallout header: {len(data)} bytes")
    raw_sig = bytes(data[0:24])
    if not raw_sig.startswith(SAVE_SIGNATURE):
        raise ValueError(f"invalid SAVE.DAT signature: {raw_sig!r}")
    version_major = u16be(data, 0x18)
    version_minor = u16be(data, 0x1A)
    release = chr(data[0x1C])
    version = f"{version_major}.{version_minor:02d}{release}"
    return SaveHeader(
        signature=c_string(data, 0x00, 0x18).strip(),
        version=version,
        player_name=c_string(data, 0x1D, 0x20),
        save_name=c_string(data, 0x3D, 0x1E),
        real_day=u16be(data, 0x5B),
        real_month=u16be(data, 0x5D),
        real_year=u16be(data, 0x5F),
        game_month=u16be(data, 0x65),
        game_day=u16be(data, 0x67),
        game_year=u16be(data, 0x69),
        game_time=u32be(data, 0x6B),
        elevation=u16be(data, 0x6F),
        map_id=u16be(data, 0x71),
        current_map_file=c_string(data, 0x73, 0x10),
    )
