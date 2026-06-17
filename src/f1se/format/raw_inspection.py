"""Read-only structural inspection for preserved raw SAVE.DAT blocks."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib

from f1se.format.functions import FunctionBlock
from f1se.io.endian import i32be


@dataclass(slots=True)
class RawBlockInspection:
    index: int
    name: str
    start: int
    end: int
    size: int
    sha256: str
    parser_status: str
    entropy_hint: str
    zero_ratio: float
    i32_count: int
    plausible_i32_count: int
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "name": self.name,
            "start": self.start,
            "start_hex": f"0x{self.start:X}",
            "end": self.end,
            "end_hex": f"0x{self.end:X}",
            "size": self.size,
            "size_hex": f"0x{self.size:X}",
            "sha256": self.sha256,
            "parser_status": self.parser_status,
            "entropy_hint": self.entropy_hint,
            "zero_ratio": self.zero_ratio,
            "i32_count": self.i32_count,
            "plausible_i32_count": self.plausible_i32_count,
            "warnings": list(self.warnings),
        }


def _entropy_hint(payload: bytes, zero_ratio: float, i32_count: int, plausible_i32_count: int) -> str:
    if not payload:
        return "empty"
    if zero_ratio >= 0.90:
        return "mostly-zero"
    if i32_count and plausible_i32_count / i32_count >= 0.80:
        return "dense-i32-table"
    if zero_ratio <= 0.05:
        return "dense-binary"
    return "mixed-raw"


def inspect_raw_block(data: bytes | bytearray, block: FunctionBlock) -> RawBlockInspection:
    payload = bytes(data[block.start:block.end])
    warnings = list(block.warnings)
    if block.size == 0:
        warnings.append("zero-length block")
    if block.size % 4 != 0:
        warnings.append("block size is not aligned to i32 width")
    zero_ratio = (payload.count(0) / len(payload)) if payload else 1.0
    i32_count = len(payload) // 4
    plausible_i32_count = 0
    for idx in range(i32_count):
        try:
            value = i32be(payload, idx * 4)
        except ValueError:
            continue
        if -1_000_000 <= value <= 1_000_000:
            plausible_i32_count += 1
    return RawBlockInspection(
        index=block.index,
        name=block.name,
        start=block.start,
        end=block.end,
        size=block.size,
        sha256=hashlib.sha256(payload).hexdigest(),
        parser_status=block.parser_status,
        entropy_hint=_entropy_hint(payload, zero_ratio, i32_count, plausible_i32_count),
        zero_ratio=round(zero_ratio, 6),
        i32_count=i32_count,
        plausible_i32_count=plausible_i32_count,
        warnings=warnings,
    )


def inspect_raw_blocks(data: bytes | bytearray, blocks: list[FunctionBlock]) -> list[RawBlockInspection]:
    return [
        inspect_raw_block(data, block)
        for block in blocks
        if block.parser_status in {"raw", "semantic-partial", "known-empty"}
    ]
