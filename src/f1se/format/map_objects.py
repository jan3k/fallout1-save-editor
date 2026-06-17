"""Heuristic read-only scan for object-like data in map .SAV files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import hashlib

from f1se.io.endian import i32be
from f1se.schema.items import get_item_meta


@dataclass(slots=True)
class MapObjectCandidate:
    file_name: str
    offset: int
    size_hint: int
    pid: int | None
    fid: int | None
    object_type_hint: str
    confidence: str
    reason: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "file_name": self.file_name,
            "offset": self.offset,
            "offset_hex": f"0x{self.offset:X}",
            "size_hint": self.size_hint,
            "size_hint_hex": f"0x{self.size_hint:X}",
            "pid": self.pid,
            "fid": self.fid,
            "object_type_hint": self.object_type_hint,
            "confidence": self.confidence,
            "reason": self.reason,
            "warnings": list(self.warnings),
        }


@dataclass(slots=True)
class MapObjectScan:
    file_name: str
    size: int
    sha256: str
    parser_status: str
    candidates: list[MapObjectCandidate]
    warnings: list[str] = field(default_factory=list)

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)

    def to_dict(self) -> dict:
        return {
            "file_name": self.file_name,
            "size": self.size,
            "size_hex": f"0x{self.size:X}",
            "sha256": self.sha256,
            "parser_status": self.parser_status,
            "candidate_count": self.candidate_count,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "warnings": list(self.warnings),
        }


def _looks_like_fid(value: int) -> bool:
    if value <= 0:
        return False
    family = (value >> 24) & 0xFF
    return 0 <= family <= 0x0F and (value & 0x00FFFFFF) != 0


def scan_map_objects(path: str | Path, *, max_candidates: int = 256) -> MapObjectScan:
    p = Path(path)
    payload = p.read_bytes()
    warnings: list[str] = []
    candidates: list[MapObjectCandidate] = []
    seen: set[tuple[int, int | None]] = set()
    if p.suffix.upper() != ".SAV" or p.name.upper() == "AUTOMAP.SAV":
        warnings.append("not a map .SAV file")
    for off in range(0, max(0, len(payload) - 4 + 1), 4):
        value = i32be(payload, off)
        meta = get_item_meta(value)
        if meta is None:
            continue
        fid = None
        for fid_rel in (-12, -8, -4, 4, 8, 12):
            pos = off + fid_rel
            if 0 <= pos <= len(payload) - 4:
                maybe_fid = i32be(payload, pos)
                if _looks_like_fid(maybe_fid):
                    fid = maybe_fid
                    break
        key = (off, value)
        if key in seen:
            continue
        seen.add(key)
        confidence = "medium" if fid is not None else "low"
        reason = "known item PID found at i32-aligned offset"
        if fid is not None:
            reason += "; nearby FID-like value observed"
        candidates.append(MapObjectCandidate(
            file_name=p.name,
            offset=off,
            size_hint=meta.save_size,
            pid=value,
            fid=fid,
            object_type_hint=meta.type_name,
            confidence=confidence,
            reason=reason,
        ))
        if len(candidates) >= max_candidates:
            warnings.append("candidate list truncated")
            break
    return MapObjectScan(
        file_name=p.name,
        size=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        parser_status="heuristic-read-only",
        candidates=candidates,
        warnings=warnings,
    )
