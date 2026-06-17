"""SAVE.DAT function block metadata."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib

FUNCTION_NAMES = [
    "unused_0",
    "dude_cid",
    "scripts_game_save_1",
    "maps",
    "scripts_game_save_2",
    "player_object_inventory",
    "player_critter_stats",
    "kill_counts",
    "tag_skills",
    "roll",
    "perks",
    "combat",
    "combat_ai",
    "pc_stats",
    "items_subsystem",
    "queue_events",
    "traits",
    "automap_state",
    "options",
    "editor",
    "worldmap",
    "pipboy",
    "movies",
    "skill_use",
    "party",
    "interface",
    "unused_26",
]


@dataclass(slots=True)
class FunctionBlock:
    index: int
    name: str
    start: int
    end: int
    parser_status: str = "raw"
    warnings: list[str] = field(default_factory=list)

    @property
    def size(self) -> int:
        return self.end - self.start

    def sha256(self, data: bytes | bytearray) -> str:
        return hashlib.sha256(bytes(data[self.start:self.end])).hexdigest()

    def to_dict(self, data: bytes | bytearray | None = None) -> dict:
        out = {
            "index": self.index,
            "name": self.name,
            "start": self.start,
            "start_hex": f"0x{self.start:X}",
            "end": self.end,
            "end_hex": f"0x{self.end:X}",
            "size": self.size,
            "size_hex": f"0x{self.size:X}",
            "parser_status": self.parser_status,
            "warnings": list(self.warnings),
        }
        if data is not None:
            out["sha256"] = self.sha256(data)
        return out
