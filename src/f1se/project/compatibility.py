"""Public compatibility matrix for Fallout 1 and Fallout 2 support."""
from __future__ import annotations

from typing import Any

from f1se.project.game_profile import GameKind, get_profile

COMMANDS = (
    "detect",
    "dump",
    "character-summary",
    "progression",
    "derived-stats",
    "fields",
    "get",
    "inventory",
    "artifacts",
    "map-summary",
    "set",
    "patch",
    "preset",
    "raw-read",
    "raw-write",
    "gui",
)


def _capability(status: str, reason: str, required_fixtures: tuple[str, ...] = ()) -> dict[str, Any]:
    return {
        "status": status,
        "reason": reason,
        "required_fixtures": list(required_fixtures),
    }


def compatibility_payload() -> dict[str, Any]:
    f1 = {
        "detect": _capability("supported", "Fallout 1 SAVE.DAT parsing remains the default profile."),
        "dump": _capability("supported", "Existing Fallout 1 dump payload is preserved."),
        "character-summary": _capability("read_only", "Fallout 1 character summary aggregates identity, progression, SPECIAL, skills, traits, perks, kills, inventory and warnings without mutation."),
        "progression": _capability("read_only", "Fallout 1 progression summary reports level, XP thresholds, skill points and perk cadence without mutation."),
        "derived-stats": _capability("read_only", "Fallout 1 derived-stats compares saved secondary stats against conservative SPECIAL-derived formula targets without mutation."),
        "fields": _capability("supported", "Existing Fallout 1 field registry is preserved."),
        "get": _capability("supported", "Existing Fallout 1 field lookup is preserved."),
        "inventory": _capability("supported", "Existing Fallout 1 inventory listing is preserved."),
        "artifacts": _capability("supported", "Existing slot artifact parsing remains Fallout 1 oriented."),
        "map-summary": _capability("supported", "Existing MAP.SAV summary support is preserved."),
        "set": _capability("supported", "Existing fixed-width Fallout 1 writes remain backup/dry-run guarded."),
        "patch": _capability("supported", "Existing Fallout 1 patch workflow is preserved."),
        "preset": _capability("supported", "Existing Fallout 1 presets are preserved."),
        "raw-read": _capability("supported", "Existing read-only raw access remains available."),
        "raw-write": _capability("unsafe", "Experimental raw-write remains explicitly gated by --experimental and --write."),
        "gui": _capability("supported", "Existing Tkinter GUI behavior remains available for Fallout 1 editing."),
    }
    f2 = {
        "detect": _capability("supported", "Fallout 2 structural detection is available for SLOT directories and direct SAVE.DAT paths."),
        "dump": _capability("read_only", "Fallout 2 dump exposes header, metadata, sections, fields and warnings without mutation."),
        "character-summary": _capability("not_supported", "Character summary is currently a Fallout 1-focused aggregate view."),
        "progression": _capability("not_supported", "Progression summary is currently a Fallout 1-focused aggregate view."),
        "derived-stats": _capability("not_supported", "Derived-stat consistency checking is currently implemented for Fallout 1 only."),
        "fields": _capability("read_only", "Fallout 2 field schema is read-only and includes offset, size, endian, risk and confidence metadata."),
        "get": _capability("read_only", "Fallout 2 fixed fields can be read by name; writes remain disabled."),
        "inventory": _capability("read_only", "Fallout 2 inventory lists existing objects only; add/remove/create operations are blocked."),
        "artifacts": _capability("partial", "Fallout 2 GUI lists SAVE.DAT sections, but non-SAVE.DAT artifact semantics still need curated fixtures."),
        "map-summary": _capability("not_supported", "Fallout 2 map artifact summary requires curated fixtures before public support."),
        "set": _capability("not_supported", "Fallout 2 write support is disabled until high-confidence fields are fixture-proven.", ("fallout2.baseline",)),
        "patch": _capability("not_supported", "Fallout 2 patch support is disabled until write fixtures exist.", ("fallout2.baseline",)),
        "preset": _capability("not_supported", "Fallout 2 presets would imply writes and are intentionally absent."),
        "raw-read": _capability("partial", "Raw read is available for diagnostics; semantic Fallout 2 raw surfaces remain limited."),
        "raw-write": _capability("unsafe", "Fallout 2 raw-write is explicitly blocked in CLI/GUI compatibility policy."),
        "gui": _capability("read_only", "GUI can open Fallout 2 saves with overview, fields, inventory, warnings and compatibility tabs; write controls are disabled."),
    }
    return {
        "read_only": True,
        "games": {
            GameKind.FALLOUT1.value: {"profile": get_profile(GameKind.FALLOUT1).to_dict(), **f1},
            GameKind.FALLOUT2.value: {"profile": get_profile(GameKind.FALLOUT2).to_dict(), **f2},
        },
        "status_values": ["supported", "partial", "read_only", "not_supported", "unsafe"],
        "notes": [
            "Fallout 2 write operations are intentionally absent in this foundation phase.",
            "Fallout 1 compatibility is preserved by keeping legacy commands delegated by default.",
        ],
    }
