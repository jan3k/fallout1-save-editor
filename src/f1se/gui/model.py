"""GUI-safe facade over the round-trip SAVE.DAT parser/editor.

The GUI deliberately talks to this model instead of reimplementing binary logic.
This keeps the Tk layer thin and makes most behaviour testable without X11.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from f1se.format.slot import SaveSlot
from f1se.format.save_dat import SaveDat
from f1se.io.atomic_write import atomic_write_bytes
from f1se.io.backup import backup_slot
from f1se.schema.fields import Diff, Field


@dataclass(slots=True)
class WriteResult:
    diffs: list[Diff]
    backup_path: Path | None
    written: bool


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
