from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from f1se.format.map_objects import scan_map_objects
from f1se.schema.items import get_item_meta


@dataclass(frozen=True, slots=True)
class MapPidSummary:
    pid: int
    name: str
    type_name: str
    count: int
    offsets: list[int]

    def to_dict(self) -> dict[str, Any]:
        return {"pid": self.pid, "name": self.name, "type_name": self.type_name, "count": self.count, "offsets": list(self.offsets), "offsets_hex": [f"0x{x:X}" for x in self.offsets]}


@dataclass(frozen=True, slots=True)
class MapRegionSummary:
    index: int
    start: int
    end: int
    count: int
    confidence: str
    type_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {"index": self.index, "start": self.start, "start_hex": f"0x{self.start:X}", "end": self.end, "end_hex": f"0x{self.end:X}", "count": self.count, "confidence": self.confidence, "type_counts": dict(self.type_counts)}


@dataclass(frozen=True, slots=True)
class MapSummary:
    file_name: str
    size: int
    sha256: str
    parser_status: str
    candidate_count: int
    pids: list[MapPidSummary]
    regions: list[MapRegionSummary]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {"file_name": self.file_name, "size": self.size, "size_hex": f"0x{self.size:X}", "sha256": self.sha256, "parser_status": self.parser_status, "candidate_count": self.candidate_count, "pids": [x.to_dict() for x in self.pids], "regions": [x.to_dict() for x in self.regions], "warnings": list(self.warnings), "read_only": True}


def _pid_rows(rows) -> list[MapPidSummary]:
    grouped: dict[int, list[int]] = defaultdict(list)
    names: dict[int, str] = {}
    types: dict[int, str] = {}
    for row in rows:
        if row.pid is None:
            continue
        grouped[row.pid].append(row.offset)
        meta = get_item_meta(row.pid)
        names[row.pid] = meta.name if meta is not None else f"pid_{row.pid}"
        types[row.pid] = meta.type_name if meta is not None else row.object_type_hint
    return sorted([MapPidSummary(pid, names[pid], types[pid], len(offsets), sorted(offsets)[:16]) for pid, offsets in grouped.items()], key=lambda item: (-item.count, item.pid))


def _regions(rows, gap: int = 0x80) -> list[MapRegionSummary]:
    ordered = sorted(rows, key=lambda row: row.offset)
    if not ordered:
        return []
    groups = [[ordered[0]]]
    for row in ordered[1:]:
        if row.offset - groups[-1][-1].offset <= gap:
            groups[-1].append(row)
        else:
            groups.append([row])
    out: list[MapRegionSummary] = []
    for idx, group in enumerate(groups):
        out.append(MapRegionSummary(idx, group[0].offset, group[-1].offset + 4, len(group), "medium" if len(group) >= 3 else "low", dict(Counter(row.object_type_hint for row in group))))
    return out


def summarize_map(path: str | Path, *, max_candidates: int = 512) -> MapSummary:
    scan = scan_map_objects(path, max_candidates=max_candidates)
    return MapSummary(scan.file_name, scan.size, scan.sha256, "deep-heuristic-read-only", scan.candidate_count, _pid_rows(scan.candidates), _regions(scan.candidates), list(scan.warnings))
