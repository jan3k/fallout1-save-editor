"""Read-only AUTOMAP.SAV fingerprint parser."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import hashlib


@dataclass(slots=True)
class AutomapSavInfo:
    path: Path
    size: int
    sha256: str
    parser_status: str = "raw-fingerprint"
    warnings: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def is_empty(self) -> bool:
        return self.size == 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": str(self.path),
            "size": self.size,
            "size_hex": f"0x{self.size:X}",
            "sha256": self.sha256,
            "is_empty": self.is_empty,
            "parser_status": self.parser_status,
            "warnings": list(self.warnings),
        }


def parse_automap_sav(path: str | Path) -> AutomapSavInfo:
    p = Path(path)
    payload = p.read_bytes()
    warnings: list[str] = []
    if p.name.upper() != "AUTOMAP.SAV":
        warnings.append("file name is not AUTOMAP.SAV")
    if len(payload) == 0:
        warnings.append("empty AUTOMAP.SAV")
    return AutomapSavInfo(
        path=p,
        size=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        warnings=warnings,
    )
