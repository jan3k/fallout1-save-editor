"""GUI-safe facade over the round-trip SAVE.DAT parser/editor.

The GUI deliberately talks to this model instead of reimplementing binary logic.
This keeps the Tk layer thin and makes most behaviour testable without X11.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from f1se.format.global_state import discover_global_state_candidates
from f1se.format.map_objects import scan_map_objects
from f1se.format.raw_inspection import inspect_raw_blocks
from f1se.format.slot import ARTIFACT_MAP_SAV, SaveSlot
from f1se.format.save_dat import SaveDat
from f1se.io.atomic_write import atomic_write_bytes
from f1se.io.backup import backup_slot
from f1se.project.features import feature_matrix_payload as project_feature_matrix_payload
from f1se.project.inventory_workflow import build_inventory_quantity_patch, inventory_workflow_payload
from f1se.schema.fields import Diff, Field


@dataclass(slots=True)
class WriteResult:
    diffs: list[Diff]
    backup_path: Path | None
    written: bool


@dataclass(slots=True)
class PatchFieldSummary:
    name: str
    risk: str
    offset: int
    old_value: int
    new_value: int
    old_bytes: str
    new_bytes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "risk": self.risk,
            "offset": self.offset,
            "offset_hex": f"0x{self.offset:X}",
            "old_value": self.old_value,
            "new_value": self.new_value,
            "old_bytes": self.old_bytes,
            "new_bytes": self.new_bytes,
        }


@dataclass(slots=True)
class PatchRiskSummary:
    changed_field_count: int
    risks: list[str]
    contains_advanced: bool
    safe_only: bool
    requires_advanced_confirmation: bool
    fields: list[PatchFieldSummary]

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed_field_count": self.changed_field_count,
            "risks": list(self.risks),
            "contains_advanced": self.contains_advanced,
            "safe_only": self.safe_only,
            "requires_advanced_confirmation": self.requires_advanced_confirmation,
            "backup_before_write": True,
            "atomic_write": True,
            "fields": [field.to_dict() for field in self.fields],
        }


@dataclass(slots=True)
class DirtyState:
    dirty: bool
    changed_field_count: int
    risks: list[str]
    safe_only: bool
    contains_advanced: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "dirty": self.dirty,
            "changed_field_count": self.changed_field_count,
            "risks": list(self.risks),
            "safe_only": self.safe_only,
            "contains_advanced": self.contains_advanced,
        }


def format_diff(diff: Diff) -> str:
    return f"{diff.file_name}:0x{diff.offset:X} {diff.old.hex()} -> {diff.new.hex()}  {diff.field_name}"


class SaveEditorSession:
    """Loaded save-slot session used by both GUI and tests."""

    def __init__(self, slot_path: str | Path):
        self.slot_path = Path(slot_path)
        self.slot = SaveSlot.open(self.slot_path)
        self.slot_path = self.slot.path
        self.save_dat = self.slot.save_dat

    def reload(self) -> None:
        self.slot = SaveSlot.open(self.slot_path)
        self.save_dat = self.slot.save_dat

    def summary(self) -> dict[str, Any]:
        h = self.save_dat.header
        return {
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
            "function6_start": self.save_dat.critter_stats.start,
            "warnings": list(dict.fromkeys(self.save_dat.warnings)),
        }

    def fields(self) -> dict[str, Field]:
        return self.save_dat.fields

    def field_groups(self) -> dict[str, list[str]]:
        names = self.save_dat.fields.keys()
        return {
            "special_base": [n for n in names if n.startswith("player.base_") and n.split("player.base_", 1)[1] in {"strength", "perception", "endurance", "charisma", "intelligence", "agility", "luck"}],
            "special_bonus": [n for n in names if n.startswith("player.bonus_") and n.split("player.bonus_", 1)[1] in {"strength", "perception", "endurance", "charisma", "intelligence", "agility", "luck"}],
            "skills": [n for n in names if n.startswith("skills.")],
            "tag_skills": [n for n in names if n.startswith("tag_skills.")],
            "traits": ["traits.trait_0", "traits.trait_1"],
            "perks": [n for n in names if n.startswith("perks.")],
            "kill_counts": [n for n in names if n.startswith("kill_counts.")],
            "inventory": [n for n in names if n.startswith("inventory.")],
            "options": [n for n in names if n.startswith("options.")],
            "pc": [n for n in names if n.startswith("pc.")],
            "derived_stats": [n for n in names if n.startswith("player.") and self.save_dat.fields[n].risk == "ADVANCED"],
            "player_safe": [n for n in names if n in {"player.current_hp", "player.radiation", "player.poison", "player.crippled_body_parts"}],
        }

    def validation_issues(self) -> list[str]:
        return self.save_dat.verify()

    def selected_traits(self) -> list[dict[str, Any]]:
        return self.save_dat.selected_traits()

    def trait_effect_notes(self) -> list[str]:
        return self.save_dat.trait_effect_notes()

    def effective_special(self) -> dict[str, dict[str, int]]:
        return self.save_dat.effective_special()

    def preset_patch(self, preset: str) -> dict[str, int]:
        return self.save_dat.preset_patch(preset)

    def artifacts_payload(self) -> dict[str, Any]:
        return {"slot_path": str(self.slot_path), "artifacts": [artifact.to_dict() for artifact in self.slot.artifacts]}

    def raw_blocks_payload(self) -> dict[str, Any]:
        return {"slot_path": str(self.slot_path), "raw_blocks": [row.to_dict() for row in inspect_raw_blocks(self.save_dat.data, self.save_dat.blocks)]}

    def globals_scan_payload(self) -> dict[str, Any]:
        return {"slot_path": str(self.slot_path), "candidates": [row.to_dict() for row in discover_global_state_candidates(self.save_dat.data, self.save_dat.blocks)]}

    def map_scan_payload(self) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        for artifact in self.slot.artifacts:
            if artifact.kind == ARTIFACT_MAP_SAV:
                rows.append(scan_map_objects(self.slot_path / artifact.name).to_dict())
        return {"slot_path": str(self.slot_path), "maps": rows}

    def feature_matrix_payload(self) -> dict[str, Any]:
        return project_feature_matrix_payload()

    def inventory_workflow_payload(self) -> dict[str, Any]:
        return inventory_workflow_payload(self.slot)

    def inventory_quantity_plan(self, item_index: int, quantity: int) -> dict[str, Any]:
        return build_inventory_quantity_patch(self.slot, item_index, quantity).to_dict()

    def validation_summary(self) -> dict[str, Any]:
        issues = self.validation_issues()
        warnings = list(dict.fromkeys(self.save_dat.warnings))
        artifact_warnings = [f"{artifact.name}: {warning}" for artifact in self.slot.artifacts for warning in artifact.warnings]
        raw_warnings = [f"{row.name}: {warning}" for row in inspect_raw_blocks(self.save_dat.data, self.save_dat.blocks) for warning in row.warnings]
        map_warnings = [f"{row['file_name']}: {warning}" for row in self.map_scan_payload()["maps"] for warning in row.get("warnings", [])]
        status = "FAIL" if issues else "WARN" if warnings or artifact_warnings or raw_warnings or map_warnings else "OK"
        return {
            "status": status,
            "issues": issues,
            "warnings": warnings,
            "artifact_warnings": artifact_warnings,
            "raw_block_warnings": raw_warnings,
            "map_scan_warnings": map_warnings,
        }

    def patch_risk_summary(self, patch: dict[str, int]) -> PatchRiskSummary:
        fields: list[PatchFieldSummary] = []
        risks: set[str] = set()
        for name, value in patch.items():
            field = self.save_dat.fields[name]
            old_bytes = bytes(self.save_dat.data[field.abs_offset:field.abs_offset + field.size])
            new_bytes = int(value).to_bytes(field.size, "big", signed=True)
            fields.append(PatchFieldSummary(
                name=name,
                risk=field.risk,
                offset=field.abs_offset,
                old_value=int(field.value),
                new_value=int(value),
                old_bytes=old_bytes.hex(),
                new_bytes=new_bytes.hex(),
            ))
            risks.add(field.risk)
        ordered_risks = sorted(risks)
        contains_advanced = any(risk == "ADVANCED" for risk in risks)
        safe_only = bool(fields) and risks == {"SAFE"}
        return PatchRiskSummary(
            changed_field_count=len(fields),
            risks=ordered_risks,
            contains_advanced=contains_advanced,
            safe_only=safe_only,
            requires_advanced_confirmation=contains_advanced,
            fields=fields,
        )

    def dirty_state(self, patch: dict[str, int]) -> DirtyState:
        summary = self.patch_risk_summary(patch)
        return DirtyState(
            dirty=summary.changed_field_count > 0,
            changed_field_count=summary.changed_field_count,
            risks=summary.risks,
            safe_only=summary.safe_only,
            contains_advanced=summary.contains_advanced,
        )

    def reset_changes_model(self) -> dict[str, int]:
        return {name: int(field.value) for name, field in self.save_dat.fields.items() if field.writable and field.type_name == "i32"}

    def requires_advanced_confirmation(self, patch: dict[str, int]) -> bool:
        return self.patch_risk_summary(patch).requires_advanced_confirmation

    def preview_patch(self, patch: dict[str, int], *, allow_out_of_range: bool = False, mode: str = "raw") -> list[Diff]:
        staged = self.save_dat.clone()
        return staged.apply_patch(patch, allow_out_of_range=allow_out_of_range, mode=mode)

    def apply_patch(self, patch: dict[str, int], *, write: bool, allow_out_of_range: bool = False, mode: str = "raw") -> WriteResult:
        diffs = self.save_dat.apply_patch(patch, allow_out_of_range=allow_out_of_range, mode=mode)
        backup_path: Path | None = None
        if write:
            backup_path = backup_slot(self.slot_path)
            atomic_write_bytes(self.slot_path / "SAVE.DAT", bytes(self.save_dat.data))
            self.reload()
            return WriteResult(diffs=diffs, backup_path=backup_path, written=True)
        # Dry-run means leave the session exactly as it was before previewing.
        self.reload()
        return WriteResult(diffs=diffs, backup_path=None, written=False)

    def raw_read(self, offset: int, size: int) -> bytes:
        return self.save_dat.raw_read(offset, size)

    def raw_preview(self, offset: int, payload: bytes) -> list[Diff]:
        staged = self.save_dat.clone()
        return staged.raw_write(offset, payload, "raw-write")

    def raw_write(self, offset: int, payload: bytes, *, write: bool) -> WriteResult:
        diffs = self.save_dat.raw_write(offset, payload, "raw-write")
        backup_path: Path | None = None
        if write:
            backup_path = backup_slot(self.slot_path)
            atomic_write_bytes(self.slot_path / "SAVE.DAT", bytes(self.save_dat.data))
            self.reload()
            return WriteResult(diffs=diffs, backup_path=backup_path, written=True)
        self.reload()
        return WriteResult(diffs=diffs, backup_path=None, written=False)
