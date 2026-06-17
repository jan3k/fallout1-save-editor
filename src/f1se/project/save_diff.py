from __future__ import annotations

from pathlib import Path
from typing import Any

from f1se.format.slot import SaveSlot


def _field_value_map(slot: SaveSlot) -> dict[str, int | str]:
    return {name: field.value for name, field in slot.save_dat.fields.items() if field.type_name in {"i32", "cstring"}}


def _artifact_map(slot: SaveSlot) -> dict[str, dict[str, Any]]:
    return {artifact.name: {"kind": artifact.kind, "sha256": artifact.sha256, "size": artifact.size} for artifact in slot.artifacts}


def diff_slots(left: str | Path, right: str | Path) -> dict[str, Any]:
    a = SaveSlot.open(left)
    b = SaveSlot.open(right)
    av = _field_value_map(a)
    bv = _field_value_map(b)
    names = sorted(set(av) | set(bv))
    field_diffs = [{"field": name, "left": av.get(name), "right": bv.get(name)} for name in names if av.get(name) != bv.get(name)]
    aa = _artifact_map(a)
    ba = _artifact_map(b)
    artifact_names = sorted(set(aa) | set(ba))
    artifact_diffs = [{"name": name, "left": aa.get(name), "right": ba.get(name)} for name in artifact_names if aa.get(name) != ba.get(name)]
    block_diffs = []
    for l_block, r_block in zip(a.save_dat.blocks, b.save_dat.blocks, strict=False):
        l_hash = l_block.sha256(a.save_dat.data)
        r_hash = r_block.sha256(b.save_dat.data)
        if l_hash != r_hash or l_block.start != r_block.start or l_block.end != r_block.end:
            block_diffs.append({"index": l_block.index, "name": l_block.name, "left": {"start": l_block.start, "end": l_block.end, "sha256": l_hash}, "right": {"start": r_block.start, "end": r_block.end, "sha256": r_hash}})
    return {"left_slot": str(a.path), "right_slot": str(b.path), "field_diffs": field_diffs, "artifact_diffs": artifact_diffs, "block_diffs": block_diffs, "summary": {"field_diff_count": len(field_diffs), "artifact_diff_count": len(artifact_diffs), "block_diff_count": len(block_diffs)}, "read_only": True}
