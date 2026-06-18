"""Game profile metadata for Fallout save support."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class GameKind(StrEnum):
    FALLOUT1 = "fallout1"
    FALLOUT2 = "fallout2"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class GameProfile:
    game_kind: GameKind
    supported_save_signatures: tuple[str, ...]
    supported_versions: tuple[str, ...]
    field_schema: str
    handler_layout_assumptions: tuple[str, ...]
    inventory_proto_strategy: str
    supported_write_capabilities: tuple[str, ...]
    risk_surface: tuple[str, ...]
    read_only: bool = True
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "game_kind": self.game_kind.value,
            "supported_save_signatures": list(self.supported_save_signatures),
            "supported_versions": list(self.supported_versions),
            "field_schema": self.field_schema,
            "handler_layout_assumptions": list(self.handler_layout_assumptions),
            "inventory_proto_strategy": self.inventory_proto_strategy,
            "supported_write_capabilities": list(self.supported_write_capabilities),
            "risk_surface": list(self.risk_surface),
            "read_only": self.read_only,
            "notes": list(self.notes),
        }


FALLOUT1_PROFILE = GameProfile(
    game_kind=GameKind.FALLOUT1,
    supported_save_signatures=("FALLOUT SAVE FILE",),
    supported_versions=("1.00", "1.01", "1.02", "1.02d"),
    field_schema="existing f1se Fallout 1 SAVE.DAT schema",
    handler_layout_assumptions=(
        "27 source-order handler blocks exposed by the existing Fallout 1 parser",
        "Function 5 FP marker anchors the player object",
        "Function 6 critter stats block is fixed-width 0x178",
    ),
    inventory_proto_strategy="Fallout 1 curated PID metadata plus conservative size inference",
    supported_write_capabilities=("set", "patch", "preset", "raw-write"),
    risk_surface=("raw access remains experimental", "semantic writes limited to existing fixed-width fields"),
    read_only=False,
)

FALLOUT2_PROFILE = GameProfile(
    game_kind=GameKind.FALLOUT2,
    supported_save_signatures=("FALLOUT SAVE FILE",),
    supported_versions=("1.02d", "1.02", "unknown"),
    field_schema="Fallout 2 read-only field schema with per-field confidence metadata",
    handler_layout_assumptions=(
        "Function 5 FP marker anchors player object and inventory",
        "Function 6 critter stats block is fixed-width 0x178",
        "Function 7 kill counters are treated as 0x4C / 19 counters",
        "Function 8 tag skills are treated as 0x10 / 4 skill ids",
        "Function 9 perks are treated as 0x2C8 / 178 perk ranks",
        "Function 13 PC stats and Function 15 traits are located heuristically until curated fixtures confirm offsets",
    ),
    inventory_proto_strategy="read-only object-list walk; PID names are not invented and object graph rewrites are disabled",
    supported_write_capabilities=(),
    risk_surface=(
        "inventory object sizes can vary by proto/type and build",
        "party/world-state sections are variable and preserved read-only",
        "perk writes can miss engine-side one-time side effects",
        "no Fallout 2 write support until fixture-backed confirmation",
    ),
    read_only=True,
)

UNKNOWN_PROFILE = GameProfile(
    game_kind=GameKind.UNKNOWN,
    supported_save_signatures=(),
    supported_versions=(),
    field_schema="none",
    handler_layout_assumptions=(),
    inventory_proto_strategy="none",
    supported_write_capabilities=(),
    risk_surface=("unrecognized or corrupt save; no parsing assumptions are safe",),
    read_only=True,
)

PROFILES: dict[GameKind, GameProfile] = {
    GameKind.FALLOUT1: FALLOUT1_PROFILE,
    GameKind.FALLOUT2: FALLOUT2_PROFILE,
    GameKind.UNKNOWN: UNKNOWN_PROFILE,
}


def get_profile(kind: GameKind | str) -> GameProfile:
    game_kind = kind if isinstance(kind, GameKind) else GameKind(str(kind))
    return PROFILES[game_kind]
