"""Fallout 1 save slot wrapper."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib

from f1se.format.save_dat import SaveDat


@dataclass(slots=True)
class SlotFileInfo:
    name: str
    size: int
    sha256: str

    def to_dict(self) -> dict:
        return {"name": self.name, "size": self.size, "size_hex": f"0x{self.size:X}", "sha256": self.sha256}


@dataclass(slots=True)
class SaveSlot:
    path: Path
    save_dat: SaveDat
    artifacts: list[SlotFileInfo]

    @classmethod
    def open(cls, path: str | Path) -> "SaveSlot":
        slot = Path(path)
        if slot.is_file() and slot.name.upper() == "SAVE.DAT":
            slot = slot.parent
        if not slot.is_dir():
            raise ValueError(f"slot is not a directory: {slot}")
        save_path = slot / "SAVE.DAT"
        if not save_path.is_file():
            raise FileNotFoundError(f"SAVE.DAT missing in slot: {slot}")
        save_dat = SaveDat.from_path(save_path)
        artifacts: list[SlotFileInfo] = []
        for child in sorted(slot.iterdir(), key=lambda p: p.name.lower()):
            if child.is_file() and child.name.upper() != "SAVE.DAT":
                payload = child.read_bytes()
                artifacts.append(SlotFileInfo(child.name, len(payload), hashlib.sha256(payload).hexdigest()))
        return cls(slot, save_dat, artifacts)

    def to_dict(self) -> dict:
        return {
            "slot_path": str(self.path),
            "SAVE.DAT": self.save_dat.to_dict(),
            "artifacts": [a.to_dict() for a in self.artifacts],
        }
