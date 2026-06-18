"""GUI-safe Fallout 2 read-only session model."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from f1se.format.fallout2.save_dat import Fallout2SaveDat
from f1se.project.game_detection import resolve_save_dat_path
from f1se.project.game_profile import GameKind
from f1se.schema.enums import SPECIAL_NAMES, TRAIT_NAMES


class Fallout2GuiSession:
    """Read-only session with the subset of SaveEditorSession used by the GUI."""

    game_kind = GameKind.FALLOUT2
    read_only = True

    def __init__(self, slot_path: str | Path):
        self.save_path = resolve_save_dat_path(slot_path)
        self.slot_path = self.save_path.parent
        self.save_dat = Fallout2SaveDat.from_path(self.save_path)

    def reload(self) -> None:
        self.save_dat = Fallout2SaveDat.from_path(self.save_path)

    def summary(self) -> dict[str, Any]:
        h = self.save_dat.header
        return {
            "game_kind": "fallout2",
            "read_only": True,
            "slot_path": str(self.slot_path),
            "size": len(self.save_dat.data),
            "size_hex": f"0x{len(self.save_dat.data):X}",
            "sha256": self.save_dat.sha256,
            "signature": h.signature,
            "version": h.version,
            "player_name": h.player_name,
            "save_name": h.save_name,
            "saved_date": f"{h.real_year:04d}-{h.real_month:02d}-{h.real_day:02d}",
            "current_map_file": h.current_map_file,
            "map_id": h.map_id,
            "elevation": h.elevation,
            "function5_start": self.save_dat.player_object.start,
            "function6_start": self.save_dat.critter_stats_start,
            "parser_status": self.save_dat.parser_status,
            "warnings": list(dict.fromkeys(self.save_dat.warnings)),
        }

    def validation_issues(self) -> list[str]:
        return []

    def selected_traits(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for idx in range(2):
            name = f"traits.{idx}"
            if name not in self.save_dat.fields:
                continue
            trait_id = int(self.save_dat.fields[name].value)
            trait_name = TRAIT_NAMES[trait_id] if 0 <= trait_id < len(TRAIT_NAMES) else "none"
            result.append({"slot": idx, "id": trait_id, "name": trait_name if trait_id != -1 else "none", "effect": "Fallout 2 trait effect metadata is not modeled yet."})
        return result

    def trait_effect_notes(self) -> list[str]:
        return [f"{trait['slot']}: {trait['name']}: {trait['effect']}" for trait in self.selected_traits() if trait["id"] != -1]

    def effective_special(self) -> dict[str, dict[str, int]]:
        result: dict[str, dict[str, int]] = {}
        for stat in SPECIAL_NAMES:
            base = int(self.save_dat.fields[f"player.base_{stat}"].value)
            bonus_name = f"player.bonus_{stat}"
            bonus = int(self.save_dat.fields[bonus_name].value) if bonus_name in self.save_dat.fields else 0
            result[stat] = {"base": base, "bonus": bonus, "static_trait": 0, "effective_static": base + bonus}
        return result

    def preset_patch(self, preset: str) -> dict[str, int]:
        raise ValueError("Fallout 2 GUI is read-only; presets are disabled")

    def artifacts_payload(self) -> dict[str, Any]:
        return {"slot_path": str(self.slot_path), "artifacts": [], "read_only": True}

    def raw_blocks_payload(self) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        for idx, section in enumerate(self.save_dat.sections.values()):
            doc = section.to_dict()
            doc.update({"index": idx, "parser_status": section.confidence, "entropy_hint": "fallout2-read-only"})
            rows.append(doc)
        return {"slot_path": str(self.slot_path), "raw_blocks": rows, "read_only": True}

    def globals_scan_payload(self) -> dict[str, Any]:
        return {"slot_path": str(self.slot_path), "candidates": [], "read_only": True, "warnings": ["Fallout 2 global/script scan is not implemented yet."]}

    def map_scan_payload(self) -> dict[str, Any]:
        return {"slot_path": str(self.slot_path), "maps": [], "read_only": True}

    def map_summary_payload(self, file_name: str | None = None) -> dict[str, Any]:
        return {"slot_path": str(self.slot_path), "maps": [], "read_only": True}

    def inventory_workflow_payload(self) -> dict[str, Any]:
        return self.save_dat.inventory_payload()

    def reset_changes_model(self) -> dict[str, int]:
        return {}

    def patch_risk_summary(self, patch: dict[str, int]):
        from f1se.gui.model import PatchRiskSummary

        return PatchRiskSummary(changed_field_count=0, risks=[], contains_advanced=False, safe_only=False, requires_advanced_confirmation=False, fields=[])

    def dirty_state(self, patch: dict[str, int]):
        from f1se.gui.model import DirtyState

        return DirtyState(dirty=False, changed_field_count=0, risks=[], safe_only=False, contains_advanced=False)

    def requires_advanced_confirmation(self, patch: dict[str, int]) -> bool:
        return False

    def preview_patch(self, patch: dict[str, int], *, allow_out_of_range: bool = False, mode: str = "raw"):
        if patch:
            raise ValueError("Fallout 2 GUI is read-only; field writes are disabled")
        return []

    def apply_patch(self, patch: dict[str, int], *, write: bool, allow_out_of_range: bool = False, mode: str = "raw"):
        raise ValueError("Fallout 2 GUI is read-only; field writes are disabled")

    def raw_read(self, offset: int, size: int) -> bytes:
        if offset < 0 or size < 0 or offset + size > len(self.save_dat.data):
            raise ValueError("raw read outside SAVE.DAT")
        return bytes(self.save_dat.data[offset:offset + size])

    def raw_preview(self, offset: int, payload: bytes):
        raise ValueError("Fallout 2 GUI is read-only; raw writes are disabled")

    def raw_write(self, offset: int, payload: bytes, *, write: bool):
        raise ValueError("Fallout 2 GUI is read-only; raw writes are disabled")
