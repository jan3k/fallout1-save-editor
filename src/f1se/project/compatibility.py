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
    "combat-summary",
    "special-set",
    "skill-set",
    "fields",
    "get",
    "inventory",
    "fallout2-writable-fields",
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
        "character-summary": _capability("read_only", "Fallout 1 aggregate view."),
        "progression": _capability("read_only", "Fallout 1 progression view."),
        "derived-stats": _capability("read_only", "Fallout 1 derived stat report."),
        "combat-summary": _capability("read_only", "Fallout 1 combat view."),
        "special-set": _capability("supported", "Dedicated Fallout 1 SPECIAL edit helper."),
        "skill-set": _capability("supported", "Dedicated Fallout 1 skill edit helper."),
        "fields": _capability("supported", "Existing Fallout 1 field registry is preserved."),
        "get": _capability("supported", "Existing Fallout 1 field lookup is preserved."),
        "inventory": _capability("supported", "Existing Fallout 1 inventory listing is preserved."),
        "fallout2-writable-fields": _capability("not_supported", "Fallout 2 only."),
        "artifacts": _capability("supported", "Existing slot artifact parsing remains Fallout 1 oriented."),
        "map-summary": _capability("supported", "Existing MAP.SAV summary support is preserved."),
        "set": _capability("supported", "Existing Fallout 1 set command is preserved."),
        "patch": _capability("supported", "Existing Fallout 1 patch workflow is preserved."),
        "preset": _capability("supported", "Existing Fallout 1 presets are preserved."),
        "raw-read": _capability("supported", "Existing diagnostic read access remains available."),
        "raw-write": _capability("unsafe", "Existing experimental command remains gated."),
        "gui": _capability("supported", "Existing Tkinter GUI behavior remains available for Fallout 1 editing."),
    }
    f2 = {
        "detect": _capability("supported", "Fallout 2 structural detection is available."),
        "dump": _capability("read_only", "Fallout 2 dump is available."),
        "character-summary": _capability("not_supported", "Fallout 1 only."),
        "progression": _capability("not_supported", "Fallout 1 only."),
        "derived-stats": _capability("not_supported", "Fallout 1 only."),
        "combat-summary": _capability("not_supported", "Fallout 1 only."),
        "special-set": _capability("partial", "Dedicated Fallout 2 SPECIAL edit helper for base SPECIAL fields."),
        "skill-set": _capability("partial", "Dedicated Fallout 2 skill edit helper for skills.* fields."),
        "fields": _capability("read_only", "Fallout 2 field schema is readable."),
        "get": _capability("read_only", "Fallout 2 field lookup is readable."),
        "inventory": _capability("read_only", "Fallout 2 inventory listing is readable."),
        "fallout2-writable-fields": _capability("read_only", "Lists accepted Fallout 2 fields."),
        "artifacts": _capability("partial", "Fallout 2 SAVE.DAT sections are available."),
        "map-summary": _capability("not_supported", "Needs curated fixtures."),
        "set": _capability("partial", "Single-field Fallout 2 set is available for the accepted field subset."),
        "patch": _capability("not_supported", "Batch patch is not available."),
        "preset": _capability("not_supported", "Presets are not available."),
        "raw-read": _capability("partial", "Diagnostic read access remains limited."),
        "raw-write": _capability("unsafe", "Not part of the Fallout 2 semantic surface."),
        "gui": _capability("read_only", "GUI Fallout 2 view remains inspection-only."),
    }
    return {
        "read_only": False,
        "games": {
            GameKind.FALLOUT1.value: {"profile": get_profile(GameKind.FALLOUT1).to_dict(), **f1},
            GameKind.FALLOUT2.value: {"profile": get_profile(GameKind.FALLOUT2).to_dict(), **f2},
        },
        "status_values": ["supported", "partial", "read_only", "not_supported", "unsafe"],
        "notes": [
            "Fallout 2 set is limited to an accepted semantic field subset.",
            "Fallout 1 compatibility is preserved by keeping legacy commands delegated by default.",
        ],
    }
