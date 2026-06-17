"""Read-only diagnostics for potential global/script state regions."""
from __future__ import annotations

from dataclasses import dataclass

from f1se.format.functions import FunctionBlock
from f1se.io.endian import i32be

GLOBAL_STATE_CANDIDATE_BLOCKS = {2, 4, 20}


@dataclass(slots=True)
class GlobalStateCandidate:
    block_index: int
    block_name: str
    start: int
    end: int
    i32_count: int
    nonzero_i32_count: int
    min_i32: int | None
    max_i32: int | None
    confidence: str
    notes: str

    def to_dict(self) -> dict:
        return {
            "block_index": self.block_index,
            "block_name": self.block_name,
            "start": self.start,
            "start_hex": f"0x{self.start:X}",
            "end": self.end,
            "end_hex": f"0x{self.end:X}",
            "i32_count": self.i32_count,
            "nonzero_i32_count": self.nonzero_i32_count,
            "min_i32": self.min_i32,
            "max_i32": self.max_i32,
            "confidence": self.confidence,
            "notes": self.notes,
        }


def inspect_global_state_candidate(data: bytes | bytearray, block: FunctionBlock) -> GlobalStateCandidate:
    values: list[int] = []
    count = block.size // 4
    for idx in range(count):
        values.append(i32be(data, block.start + idx * 4))
    nonzero = [value for value in values if value != 0]
    if not values:
        confidence = "unknown"
        notes = "no i32-aligned payload to inspect"
    elif block.index in (2, 4) and nonzero:
        confidence = "medium"
        notes = "source-order scripts/game-save block; read-only candidate for global/script state"
    elif block.index == 20 and nonzero:
        confidence = "low"
        notes = "late world-state block; may include worldmap/Pip-Boy/movie/party/interface data"
    else:
        confidence = "low"
        notes = "mostly empty or low-signal raw block"
    return GlobalStateCandidate(
        block_index=block.index,
        block_name=block.name,
        start=block.start,
        end=block.end,
        i32_count=count,
        nonzero_i32_count=len(nonzero),
        min_i32=min(values) if values else None,
        max_i32=max(values) if values else None,
        confidence=confidence,
        notes=notes,
    )


def discover_global_state_candidates(data: bytes | bytearray, blocks: list[FunctionBlock]) -> list[GlobalStateCandidate]:
    return [
        inspect_global_state_candidate(data, block)
        for block in blocks
        if block.index in GLOBAL_STATE_CANDIDATE_BLOCKS
    ]
