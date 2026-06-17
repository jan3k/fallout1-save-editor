"""Fallout 1 save slot wrapper."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import hashlib
from typing import Any

from f1se.format.automap_sav import parse_automap_sav
from f1se.format.map_sav import parse_map_sav
from f1se.format.save_dat import SaveDat

ARTIFACT_SAVE_DAT = "SAVE_DAT"
ARTIFACT_AUTOMAP_SAV = "AUTOMAP_SAV"
ARTIFACT_MAP_SAV = "MAP_SAV"
ARTIFACT_UNKNOWN = "UNKNOWN"


def classify_artifact(path: str | Path) -> str:
    p = Path(path)
    upper = p.name.upper()
    if upper == "SAVE.DAT":
        return ARTIFACT_SAVE_DAT
    if upper == "AUTOMAP.SAV":
        return ARTIFACT_AUTOMAP_SAV
    if p.suffix.upper() == ".SAV":
        return ARTIFACT_MAP_SAV
    return ARTIFACT_UNKNOWN


@dataclass(slots=True)
class SlotArtifact:
    name: str
    size: int
    sha256: str
    kind: str
    parser_status: str = "raw-fingerprint"
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "size": self.size,
            "size_hex": f"0x{self.size:X}",
            "sha256": self.sha256,
            "kind": self.kind,
            "parser_status": self.parser_status,
            "warnings": list(self.warnings),
            "details": dict(self.details),
        }


# Backward-compatible alias for older imports/tests.
SlotFileInfo = SlotArtifact


def _artifact_from_path(path: Path) -> SlotArtifact:
    kind = classify_artifact(path)
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    warnings: list[str] = []
    details: dict[str, Any] = {}
    parser_status = "raw-fingerprint"

    if kind == ARTIFACT_AUTOMAP_SAV:
        info = parse_automap_sav(path)
        warnings = list(info.warnings)
        parser_status = info.parser_status
        details = info.to_dict()
    elif kind == ARTIFACT_MAP_SAV:
        info = parse_map_sav(path)
        warnings = list(info.warnings)
        parser_status = info.parser_status
        details = info.to_dict()
    elif kind == ARTIFACT_UNKNOWN:
        parser_status = "raw-unknown"
        if len(payload) == 0:
            warnings.append("empty unknown slot artifact")

    return SlotArtifact(
        name=path.name,
        size=len(payload),
        sha256=digest,
        kind=kind,
        parser_status=parser_status,
        warnings=warnings,
        details=details,
    )


@dataclass(slots=True)
class SaveSlot:
    path: Path
    save_dat: SaveDat
    artifacts: list[SlotArtifact]

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
        artifacts: list[SlotArtifact] = []
        for child in sorted(slot.iterdir(), key=lambda p: p.name.lower()):
            if child.is_file() and child.name.upper() != "SAVE.DAT":
                artifacts.append(_artifact_from_path(child))
        return cls(slot, save_dat, artifacts)

    def to_dict(self) -> dict:
        return {
            "slot_path": str(self.path),
            "SAVE.DAT": self.save_dat.to_dict(),
            "artifacts": [a.to_dict() for a in self.artifacts],
        }
