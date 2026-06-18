"""Public compatibility matrix for Fallout 1 and Fallout 2 support."""
from __future__ import annotations

from typing import Any

from f1se.project.game_profile import GameKind, get_profile

COMMANDS = (
    "detect",
    "dump",
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
        "gui": _capability("supported", "Existing Tkinter GUI behavior is not changed by the Fallout 2 foundation."),
    }
    f2 = {
        "detect": _capability("supported", "Fallout 2 structural detection is available for SLOT directories and direct SAVE.DAT paths."),
        "dump": _capability("read_only", "Fallout 2 dump exposes header, metadata, sections, fields and warnings without mutation."),
        "fields": _capability("read_only", "Fallout 2 field schema is read-only and includes offset, size, endian, risk and confidence metadata."),
        "get": _capability("read_only", "Fallout 2 fixed fields can be read by name; writes remain disabled."),
        "inventory": _capability("read_only", "Fallout 2 inventory lists existing objects only; add/remove/create operations are blocked."),
        "artifacts": _capability("not_supported", "Fallout 2 slot artifact semantics are not yet separated from Fallout 1 artifact parsing."),
        "map-summary": _capability("not_supported", "Fallout 2 map artifact summary requires curated fixtures before public support."),
        "set": _capability("not_supported", "Fallout 2 write support is disabled until high-confidence fields are fixture-proven.", ("fallout2.baseline",)),
        "patch": _capability("not_supported", "Fallout 2 patch support is disabled until write fixtures exist.", ("fallout2.baseline",)),
        "preset": _capability("not_supported", "Fallout 2 presets would imply writes and are intentionally absent."),
        "raw-read": _capability("partial", "Use existing raw-read only with explicit user-supplied offsets; no Fallout 2 semantic raw command exists yet."),
        "raw-write": _capability("unsafe", "Fallout 2 raw-write is not a supported compatibility surface."),
        "gui": _capability("partial", "GUI write controls remain Fallout 1 only; Fallout 2 read-only GUI integration is a later phase."),
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
