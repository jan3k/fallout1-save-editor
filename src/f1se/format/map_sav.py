"""Read-only map .SAV fingerprint parser."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import hashlib


@dataclass(slots=True)
class MapSavInfo:
    path: Path
    name: str
    size: int
    sha256: str
    probable_map_file: str
    parser_status: str = "raw-fingerprint"
    warnings: list[str] = field(default_factory=list)

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
            "probable_map_file": self.probable_map_file,
            "is_empty": self.is_empty,
            "parser_status": self.parser_status,
            "warnings": list(self.warnings),
        }


def parse_map_sav(path: str | Path) -> MapSavInfo:
    p = Path(path)
    payload = p.read_bytes()
    warnings: list[str] = []
    if p.name.upper() == "AUTOMAP.SAV":
        warnings.append("AUTOMAP.SAV should be handled by automap parser")
    if p.suffix.upper() != ".SAV":
        warnings.append("file extension is not .SAV")
    if len(payload) == 0:
        warnings.append("empty map .SAV")
    return MapSavInfo(
        path=p,
        name=p.name,
        size=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        probable_map_file=p.name,
        warnings=warnings,
    )
