"""Dynamic field registry models."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

Risk = Literal["SAFE", "ADVANCED", "EXPERIMENTAL", "RAW"]


@dataclass(slots=True)
class Field:
    name: str
    file_name: str
    block: str
    abs_offset: int
    rel_offset: int
    size: int
    endian: str
    type_name: str
    value: int | str
    risk: Risk
    validator: Callable[..., None] | None = None
    writable: bool = True
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "file": self.file_name,
            "block": self.block,
            "abs_offset": self.abs_offset,
            "abs_offset_hex": f"0x{self.abs_offset:X}",
            "rel_offset": self.rel_offset,
            "rel_offset_hex": f"0x{self.rel_offset:X}",
            "size": self.size,
            "endian": self.endian,
            "type": self.type_name,
            "value": self.value,
            "risk": self.risk,
            "writable": self.writable,
            "description": self.description,
        }


@dataclass(slots=True)
class Diff:
    file_name: str
    offset: int
    old: bytes
    new: bytes
    field_name: str

    def to_dict(self) -> dict:
        return {
            "file": self.file_name,
            "offset": self.offset,
            "offset_hex": f"0x{self.offset:X}",
            "old_hex": self.old.hex(),
            "new_hex": self.new.hex(),
            "field": self.field_name,
        }
