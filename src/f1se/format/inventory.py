"""Dynamic Fallout 1 inventory parser for Function 5 item list."""
from __future__ import annotations

from dataclasses import dataclass, field

from f1se.io.endian import i32be, u32be
from f1se.schema.enums import ITEM_PID_NAMES


@dataclass(slots=True)
class ParsedInventoryItem:
    index: int
    start: int
    end: int
    quantity: int
    pid: int
    type_name: str
    object_name: str
    ammo_or_charges: int | None
    ammo_type: int | None
    raw_fields: dict[str, int]
    warnings: list[str] = field(default_factory=list)

    @property
    def size(self) -> int:
        return self.end - self.start

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "start": self.start,
            "start_hex": f"0x{self.start:X}",
            "end": self.end,
            "end_hex": f"0x{self.end:X}",
            "size": self.size,
            "size_hex": f"0x{self.size:X}",
            "quantity": self.quantity,
            "pid": self.pid,
            "type": self.type_name,
            "name": self.object_name,
            "ammo_or_charges": self.ammo_or_charges,
            "ammo_type": self.ammo_type,
            "raw_fields": self.raw_fields,
            "warnings": list(self.warnings),
        }


def _looks_like_f6(data: bytes | bytearray, off: int) -> bool:
    if off < 0 or off + 0x178 > len(data):
        return False
    try:
        special = [i32be(data, off + 0x08 + i * 4) for i in range(7)]
        age = i32be(data, off + 0x8C)
        gender = i32be(data, off + 0x90)
        skills = [i32be(data, off + 0x120 + i * 4) for i in range(18)]
    except ValueError:
        return False
    # Keep this tolerant: edited saves may have out-of-range SPECIAL.
    if not all(-1000 <= v <= 1000 for v in special):
        return False
    if not (0 <= age <= 200):
        return False
    if gender not in (0, 1):
        return False
    if not all(-1000 <= v <= 1000 for v in skills):
        return False
    return True


def _size_options_for_pid(pid: int) -> list[int]:
    if pid in ITEM_PID_NAMES:
        return [ITEM_PID_NAMES[pid][2]]
    # Fallout object payload is type-dependent. These are the common terminal sizes
    # encountered in Fallout 1/Fallout 2 object serialization for inventory items.
    return [0x64, 0x60, 0x5C]


def infer_inventory(data: bytes | bytearray, start: int, count: int) -> tuple[list[ParsedInventoryItem], int]:
    """Parse Function 5 inventory and return (items, function6_start).

    Function 5 item entries are variable-sized. For known PIDs we use a curated
    Fallout 1 map. For unknown PIDs we try common object tail sizes and accept
    the path whose post-inventory camera dword is followed by a valid Function 6.
    """
    if count < 0 or count > 10_000:
        raise ValueError(f"unreasonable inventory count: {count}")

    memo: dict[tuple[int, int], tuple[list[tuple[int, int]], int] | None] = {}

    def solve(pos: int, idx: int) -> tuple[list[tuple[int, int]], int] | None:
        key = (pos, idx)
        if key in memo:
            return memo[key]
        if idx == count:
            f6_start = pos + 4  # camera position dword sits between inventory and Function 6
            if _looks_like_f6(data, f6_start):
                memo[key] = ([], f6_start)
                return memo[key]
            memo[key] = None
            return None
        if pos + 0x5C > len(data):
            memo[key] = None
            return None
        try:
            pid = i32be(data, pos + 0x30)
        except ValueError:
            memo[key] = None
            return None
        for size in _size_options_for_pid(pid):
            if pos + size > len(data):
                continue
            try:
                qty = i32be(data, pos)
                loc = i32be(data, pos + 0x08)
            except ValueError:
                continue
            if qty < 0 or qty > 1_000_000:
                continue
            if loc not in (-1, 0, 1, 2):
                continue
            rest = solve(pos + size, idx + 1)
            if rest is not None:
                sizes, f6_start = rest
                memo[key] = ([(pos, size)] + sizes, f6_start)
                return memo[key]
        memo[key] = None
        return None

    solved = solve(start, 0)
    if solved is None:
        raise ValueError("could not infer dynamic inventory item sizes or Function 6 start")
    chunks, f6_start = solved
    out: list[ParsedInventoryItem] = []
    for idx, (pos, size) in enumerate(chunks):
        pid = i32be(data, pos + 0x30)
        name, item_type, _known_size = ITEM_PID_NAMES.get(pid, (f"pid_{pid}", "unknown", size))
        raw = {
            "location": i32be(data, pos + 0x08),
            "frm_id": i32be(data, pos + 0x24),
            "object_flags": u32be(data, pos + 0x28),
            "map_level": i32be(data, pos + 0x2C),
            "script_id": i32be(data, pos + 0x44),
            "container_count": i32be(data, pos + 0x4C),
        }
        ammo_or_charges = i32be(data, pos + 0x5C) if size >= 0x60 else None
        ammo_type = i32be(data, pos + 0x60) if size >= 0x64 else None
        warnings: list[str] = []
        if pid not in ITEM_PID_NAMES:
            warnings.append("unknown PID; size inferred heuristically")
        out.append(ParsedInventoryItem(
            index=idx,
            start=pos,
            end=pos + size,
            quantity=i32be(data, pos),
            pid=pid,
            type_name=item_type,
            object_name=name,
            ammo_or_charges=ammo_or_charges,
            ammo_type=ammo_type,
            raw_fields=raw,
            warnings=warnings,
        ))
    return out, f6_start
