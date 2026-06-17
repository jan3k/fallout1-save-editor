"""SAVE.DAT function block metadata."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib

from f1se.format.function_registry import FUNCTION_NAMES, get_function_spec


@dataclass(slots=True)
class FunctionBlock:
    index: int
    name: str
    start: int
    end: int
    parser_status: str = "raw"
    warnings: list[str] = field(default_factory=list)
    save_handler: str = ""
    load_handler: str = ""
    writable_policy: str = ""
    source_parser_status: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        try:
            spec = get_function_spec(self.index)
        except KeyError:
            return
        if not self.name:
            self.name = spec.name
        if not self.save_handler:
            self.save_handler = spec.save_handler
        if not self.load_handler:
            self.load_handler = spec.load_handler
        if not self.writable_policy:
            self.writable_policy = spec.writable_policy
        if not self.source_parser_status:
            self.source_parser_status = spec.parser_status
        if not self.notes:
            self.notes = spec.notes

    @property
    def size(self) -> int:
        return self.end - self.start

    def sha256(self, data: bytes | bytearray) -> str:
        return hashlib.sha256(bytes(data[self.start:self.end])).hexdigest()

    def to_dict(self, data: bytes | bytearray | None = None) -> dict:
        out = {
            "index": self.index,
            "name": self.name,
            "save_handler": self.save_handler,
            "load_handler": self.load_handler,
            "start": self.start,
            "start_hex": f"0x{self.start:X}",
            "end": self.end,
            "end_hex": f"0x{self.end:X}",
            "size": self.size,
            "size_hex": f"0x{self.size:X}",
            "parser_status": self.parser_status,
            "source_parser_status": self.source_parser_status,
            "writable_policy": self.writable_policy,
            "warnings": list(self.warnings),
        }
        if self.notes:
            out["notes"] = self.notes
        if data is not None:
            out["sha256"] = self.sha256(data)
        return out
