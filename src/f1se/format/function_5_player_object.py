"""Function 5: player object + dynamic inventory."""
from __future__ import annotations

from dataclasses import dataclass, field

from f1se.io.endian import i32be, u32be
from f1se.format.inventory import ParsedInventoryItem, infer_inventory

FP_SIGNATURE = b"\x00\x00FP"


@dataclass(slots=True)
class PlayerObject:
    start: int
    end: int
    function6_start: int
    coordinates: int
    facing: int
    fid: int
    map_level: int
    inventory_count: int
    crippled_body_parts: int
    current_hp: int
    radiation: int
    poison: int
    item_list_start: int
    inventory: list[ParsedInventoryItem]
    camera_position_offset: int
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "start_hex": f"0x{self.start:X}",
            "end": self.end,
            "end_hex": f"0x{self.end:X}",
            "function6_start": self.function6_start,
            "function6_start_hex": f"0x{self.function6_start:X}",
            "coordinates": self.coordinates,
            "facing": self.facing,
            "fid": self.fid,
            "fid_hex": f"0x{self.fid:08X}",
            "map_level": self.map_level,
            "inventory_count": self.inventory_count,
            "crippled_body_parts": self.crippled_body_parts,
            "current_hp": self.current_hp,
            "radiation": self.radiation,
            "poison": self.poison,
            "item_list_start": self.item_list_start,
            "item_list_start_hex": f"0x{self.item_list_start:X}",
            "camera_position_offset": self.camera_position_offset,
            "camera_position_offset_hex": f"0x{self.camera_position_offset:X}",
            "inventory": [item.to_dict() for item in self.inventory],
            "warnings": list(self.warnings),
        }


def parse_function5_at(data: bytes | bytearray, start: int) -> PlayerObject:
    if bytes(data[start:start + 4]) != FP_SIGNATURE:
        raise ValueError(f"Function 5 signature not found at 0x{start:X}")
    inv_count = i32be(data, start + 0x48)
    item_start = start + 0x80
    items, f6_start = infer_inventory(data, item_start, inv_count)
    end = f6_start
    camera_offset = f6_start - 4
    warnings: list[str] = []
    facing = i32be(data, start + 0x1C)
    if facing not in range(6):
        warnings.append(f"facing outside expected 0..5: {facing}")
    return PlayerObject(
        start=start,
        end=end,
        function6_start=f6_start,
        coordinates=i32be(data, start + 0x04),
        facing=facing,
        fid=u32be(data, start + 0x20),
        map_level=i32be(data, start + 0x28),
        inventory_count=inv_count,
        crippled_body_parts=i32be(data, start + 0x64),
        current_hp=i32be(data, start + 0x74),
        radiation=i32be(data, start + 0x78),
        poison=i32be(data, start + 0x7C),
        item_list_start=item_start,
        inventory=items,
        camera_position_offset=camera_offset,
        warnings=warnings,
    )


def find_function5(data: bytes | bytearray, start_at: int = 0x7563) -> PlayerObject:
    pos = max(0, start_at)
    while True:
        found = bytes(data).find(FP_SIGNATURE, pos)
        if found < 0:
            raise ValueError("could not find unique Function 5 FP signature")
        try:
            return parse_function5_at(data, found)
        except Exception:
            pos = found + 1
