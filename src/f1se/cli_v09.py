from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from f1se.cli_v08 import main as previous_main
from f1se.format.map_objects import scan_map_objects
from f1se.format.slot import ARTIFACT_MAP_SAV, SaveSlot


def _hex_or_int(value: str | int) -> int:
    if isinstance(value, int):
        return value
    return int(value, 0)


def _map_scans(slot: SaveSlot, file_name: str | None) -> list[dict]:
    rows: list[dict] = []
    for artifact in slot.artifacts:
        if artifact.kind != ARTIFACT_MAP_SAV:
            continue
        if file_name is not None and artifact.name.lower() != file_name.lower():
            continue
        rows.append(scan_map_objects(slot.path / artifact.name).to_dict())
    return rows


def _cmd_map_scan(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se map-scan")
    parser.add_argument("slot")
    parser.add_argument("--file")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    slot = SaveSlot.open(args.slot)
    rows = _map_scans(slot, args.file)
    payload = {"slot_path": str(slot.path), "maps": rows}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    for row in rows:
        print(f"{row['file_name']}: size={row['size']} sha256={row['sha256']} candidates={row['candidate_count']}")
        for candidate in row["candidates"][:20]:
            print(f"  0x{candidate['offset']:X} pid={candidate['pid']} fid={candidate['fid']} confidence={candidate['confidence']} reason={candidate['reason']}")
    return 0


def _check_fixture(root: Path, slot_name: str, expected: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    slot_path = root / slot_name
    result: dict[str, Any] = {"slot": slot_name, "path": str(slot_path), "issues": issues}
    if not slot_path.is_dir():
        issues.append("slot directory missing")
        result["ok"] = False
        return result
    if not (slot_path / "SAVE.DAT").is_file():
        issues.append("SAVE.DAT missing")
        result["ok"] = False
        return result
    try:
        slot = SaveSlot.open(slot_path)
    except Exception as exc:
        issues.append(f"SaveSlot.open failed: {exc}")
        result["ok"] = False
        return result
    sd = slot.save_dat
    if len(sd.data) != expected.get("save_dat_size"):
        issues.append("save_dat_size mismatch")
    if sd.header.version != expected.get("version"):
        issues.append("version mismatch")
    if sd.header.player_name != expected.get("player_name"):
        issues.append("player_name mismatch")
    if sd.header.current_map_file != expected.get("current_map_file"):
        issues.append("current_map_file mismatch")
    if sd.player_object.start != _hex_or_int(expected["function5_start"]):
        issues.append("function5_start mismatch")
    if sd.critter_stats.start != _hex_or_int(expected["function6_start"]):
        issues.append("function6_start mismatch")
    if sd.player_object.inventory_count != expected.get("inventory_count"):
        issues.append("inventory_count mismatch")
    if sd.kill_count_count != expected.get("kill_count_count"):
        issues.append("kill_count_count mismatch")
    artifact_by_name = {artifact.name: artifact for artifact in slot.artifacts}
    if set(artifact_by_name) != set(expected.get("expected_artifacts", [])):
        issues.append("expected_artifacts mismatch")
    for name, kind in expected.get("expected_artifact_kinds", {}).items():
        if name not in artifact_by_name or artifact_by_name[name].kind != kind:
            issues.append(f"artifact kind mismatch: {name}")
    for name, row in expected.get("expected_map_artifacts", {}).items():
        artifact = artifact_by_name.get(name)
        if artifact is None:
            issues.append(f"map artifact missing: {name}")
            continue
        if artifact.kind != row.get("kind"):
            issues.append(f"map artifact kind mismatch: {name}")
        if artifact.parser_status != row.get("parser_status"):
            issues.append(f"map artifact parser_status mismatch: {name}")
        if artifact.size < int(row.get("min_size", 0)):
            issues.append(f"map artifact min_size mismatch: {name}")
    for index, row in expected.get("expected_raw_blocks", {}).items():
        block = sd.blocks[int(index)]
        if block.name != row["name"] or block.start != _hex_or_int(row["start"]) or block.end != _hex_or_int(row["end"]):
            issues.append(f"raw block mismatch: {index}")
    for issue in sd.verify():
        issues.append(f"verify: {issue}")
    result["ok"] = not issues
    result["artifacts"] = [artifact.to_dict() for artifact in slot.artifacts]
    return result


def _fixture_check_payload(root_path: str | Path) -> dict[str, Any]:
    root = Path(root_path)
    manifest_path = root / "fixtures.json"
    payload: dict[str, Any] = {"fixture_root": str(root), "manifest": str(manifest_path), "ok": False, "slots": {}}
    if not root.is_dir():
        payload["issues"] = ["fixture root missing"]
        return payload
    if not manifest_path.is_file():
        payload["issues"] = ["fixtures.json missing"]
        return payload
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["ok"] = True
    for slot_name, expected in manifest.items():
        result = _check_fixture(root, slot_name, expected)
        payload["slots"][slot_name] = result
        payload["ok"] = payload["ok"] and result["ok"]
    return payload


def _cmd_fixture_check(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se fixture-check")
    parser.add_argument("fixture_root")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    payload = _fixture_check_payload(args.fixture_root)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for slot_name, result in payload.get("slots", {}).items():
            print(f"{'OK' if result['ok'] else 'FAIL'}: {slot_name}")
            for issue in result.get("issues", []):
                print(f"  - {issue}")
    return 0 if payload.get("ok") else 1


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "map-scan":
        return _cmd_map_scan(args[1:])
    if args and args[0] == "fixture-check":
        return _cmd_fixture_check(args[1:])
    return previous_main(args)
