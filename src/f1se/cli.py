"""Command-line interface for f1se."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

from f1se.format.global_state import discover_global_state_candidates
from f1se.format.raw_inspection import inspect_raw_blocks
from f1se.format.slot import SaveSlot
from f1se.format.save_dat import SaveDat
from f1se.io.atomic_write import atomic_write_bytes
from f1se.io.backup import backup_slot
from f1se.schema.fields import Diff
from f1se.schema.enums import SPECIAL_NAMES


def _print_diffs(diffs: Iterable[Diff]) -> None:
    diffs = list(diffs)
    if not diffs:
        print("No byte changes.")
        return
    for d in diffs:
        print(f"{d.file_name}:0x{d.offset:X} {d.old.hex()} -> {d.new.hex()}  {d.field_name}")


def _hex_or_int(value: str | int) -> int:
    if isinstance(value, int):
        return value
    return int(value, 0)


def _load_save(slot_path: str | Path) -> SaveDat:
    return SaveSlot.open(slot_path).save_dat


def _inventory_payload(slot: SaveSlot) -> dict:
    return {
        "slot_path": str(slot.path),
        "inventory_count": slot.save_dat.player_object.inventory_count,
        "inventory": [item.to_dict() for item in slot.save_dat.player_object.inventory],
    }


def _artifacts_payload(slot: SaveSlot) -> dict:
    return {
        "slot_path": str(slot.path),
        "artifacts": [artifact.to_dict() for artifact in slot.artifacts],
    }


def _raw_blocks_payload(slot: SaveSlot) -> dict:
    return {
        "slot_path": str(slot.path),
        "raw_blocks": [item.to_dict() for item in inspect_raw_blocks(slot.save_dat.data, slot.save_dat.blocks)],
    }


def _globals_scan_payload(slot: SaveSlot) -> dict:
    return {
        "slot_path": str(slot.path),
        "candidates": [item.to_dict() for item in discover_global_state_candidates(slot.save_dat.data, slot.save_dat.blocks)],
    }


def _fixture_snapshot(slot: SaveSlot, *, name: str | None, description: str, include_sha256: bool, include_warnings: bool) -> dict:
    sd = slot.save_dat
    h = sd.header
    entry: dict[str, Any] = {
        "description": description,
        "save_dat_size": len(sd.data),
        "version": h.version,
        "player_name": h.player_name,
        "current_map_file": h.current_map_file,
        "function5_start": f"0x{sd.player_object.start:X}",
        "function6_start": f"0x{sd.critter_stats.start:X}",
        "inventory_count": sd.player_object.inventory_count,
        "kill_count_count": sd.kill_count_count,
        "expected_artifacts": [artifact.name for artifact in slot.artifacts],
        "expected_artifact_kinds": {artifact.name: artifact.kind for artifact in slot.artifacts},
    }
    if include_sha256:
        entry["sha256"] = sd.sha256
    warnings = list(dict.fromkeys(sd.warnings))
    if include_warnings and warnings:
        entry["warnings"] = warnings
    issues = sd.verify()
    if issues:
        entry["verify_issues"] = issues
    slot_name = name or slot.path.name
    return {slot_name: entry}


def _check_fixture(root: Path, slot_name: str, expected: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    slot_path = root / slot_name
    save_path = slot_path / "SAVE.DAT"
    result: dict[str, Any] = {"slot": slot_name, "path": str(slot_path), "issues": issues}
    if not slot_path.is_dir():
        issues.append("slot directory missing")
        result["ok"] = False
        return result
    if not save_path.is_file():
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
        issues.append(f"save_dat_size mismatch: {len(sd.data)} != {expected.get('save_dat_size')}")
    if sd.header.version != expected.get("version"):
        issues.append(f"version mismatch: {sd.header.version!r} != {expected.get('version')!r}")
    if sd.header.player_name != expected.get("player_name"):
        issues.append(f"player_name mismatch: {sd.header.player_name!r} != {expected.get('player_name')!r}")
    if sd.header.current_map_file != expected.get("current_map_file"):
        issues.append(f"current_map_file mismatch: {sd.header.current_map_file!r} != {expected.get('current_map_file')!r}")
    if sd.player_object.start != _hex_or_int(expected["function5_start"]):
        issues.append(f"function5_start mismatch: 0x{sd.player_object.start:X} != {expected['function5_start']}")
    if sd.critter_stats.start != _hex_or_int(expected["function6_start"]):
        issues.append(f"function6_start mismatch: 0x{sd.critter_stats.start:X} != {expected['function6_start']}")
    if sd.player_object.inventory_count != expected.get("inventory_count"):
        issues.append(f"inventory_count mismatch: {sd.player_object.inventory_count} != {expected.get('inventory_count')}")
    if sd.kill_count_count != expected.get("kill_count_count"):
        issues.append(f"kill_count_count mismatch: {sd.kill_count_count} != {expected.get('kill_count_count')}")
    if expected.get("sha256") and sd.sha256 != expected["sha256"]:
        issues.append("sha256 mismatch")
    expected_artifacts = set(expected.get("expected_artifacts", []))
    actual_artifacts = {artifact.name for artifact in slot.artifacts}
    if actual_artifacts != expected_artifacts:
        issues.append(f"expected_artifacts mismatch: {sorted(actual_artifacts)!r} != {sorted(expected_artifacts)!r}")
    expected_kinds = expected.get("expected_artifact_kinds", {})
    if expected_kinds:
        actual_kinds = {artifact.name: artifact.kind for artifact in slot.artifacts}
        if actual_kinds != expected_kinds:
            issues.append(f"expected_artifact_kinds mismatch: {actual_kinds!r} != {expected_kinds!r}")
    for index, row in expected.get("expected_raw_blocks", {}).items():
        idx = int(index)
        if idx >= len(sd.blocks):
            issues.append(f"expected_raw_blocks index {idx} missing")
            continue
        block = sd.blocks[idx]
        if block.name != row["name"]:
            issues.append(f"raw block {idx} name mismatch: {block.name!r} != {row['name']!r}")
        if block.start != _hex_or_int(row["start"]):
            issues.append(f"raw block {idx} start mismatch: 0x{block.start:X} != {row['start']}")
        if block.end != _hex_or_int(row["end"]):
            issues.append(f"raw block {idx} end mismatch: 0x{block.end:X} != {row['end']}")
    for row in expected.get("expected_inventory", []):
        idx = int(row["index"])
        if idx >= len(sd.player_object.inventory):
            issues.append(f"expected_inventory index {idx} missing")
            continue
        item = sd.player_object.inventory[idx]
        if item.start != _hex_or_int(row["offset"]):
            issues.append(f"inventory[{idx}] offset mismatch: 0x{item.start:X} != {row['offset']}")
        if item.pid != row["pid"]:
            issues.append(f"inventory[{idx}] pid mismatch: {item.pid} != {row['pid']}")
        if item.size != _hex_or_int(row["size"]):
            issues.append(f"inventory[{idx}] size mismatch: 0x{item.size:X} != {row['size']}")
        if item.quantity != row["quantity"]:
            issues.append(f"inventory[{idx}] quantity mismatch: {item.quantity} != {row['quantity']}")
        if item.known_pid != row["known_pid"]:
            issues.append(f"inventory[{idx}] known_pid mismatch: {item.known_pid} != {row['known_pid']}")
        if item.type_name != row["type"]:
            issues.append(f"inventory[{idx}] type mismatch: {item.type_name!r} != {row['type']!r}")
    verify_issues = sd.verify()
    if verify_issues:
        issues.extend(f"verify: {issue}" for issue in verify_issues)
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
    all_ok = True
    for slot_name, expected in manifest.items():
        result = _check_fixture(root, slot_name, expected)
        payload["slots"][slot_name] = result
        all_ok = all_ok and bool(result["ok"])
    payload["ok"] = all_ok
    return payload


def cmd_inspect(args: argparse.Namespace) -> int:
    slot = SaveSlot.open(args.slot)
    sd = slot.save_dat
    h = sd.header
    print(f"Slot: {slot.path}")
    print(f"SAVE.DAT size: {len(sd.data)} / 0x{len(sd.data):X}")
    print(f"SAVE.DAT sha256: {sd.sha256}")
    print(f"Signature: {h.signature}")
    print(f"Version: {h.version}")
    print(f"Player: {h.player_name}")
    print(f"Current map: {h.current_map_file} (map_id={h.map_id}, elevation={h.elevation})")
    print(f"Saved date: {h.real_year:04d}-{h.real_month:02d}-{h.real_day:02d}")
    print(f"Function 5: 0x{sd.player_object.start:X}")
    print(f"Function 6: 0x{sd.critter_stats.start:X}")
    print("SPECIAL:")
    for name in SPECIAL_NAMES:
        f = sd.fields[f"player.base_{name}"]
        print(f"  {name:12s} 0x{f.abs_offset:X} = {f.value}")
    print("Inventory:")
    for item in sd.player_object.inventory:
        print(
            f"  #{item.index}: 0x{item.start:X} qty={item.quantity} pid={item.pid} "
            f"known={item.known_pid} type={item.type_name} name={item.object_name} "
            f"size=0x{item.size:X} source={item.size_source} confidence={item.confidence}"
        )
    if slot.artifacts:
        print("Slot artifacts:")
        for art in slot.artifacts:
            print(f"  {art.name}: {art.kind} {art.size} bytes sha256={art.sha256}")
    if sd.warnings:
        print("Warnings:")
        for w in sorted(set(sd.warnings)):
            print(f"  - {w}")
    return 0


def cmd_dump(args: argparse.Namespace) -> int:
    slot = SaveSlot.open(args.slot)
    if args.json:
        print(json.dumps(slot.to_dict(), indent=2, sort_keys=True))
    else:
        return cmd_inspect(args)
    return 0


def cmd_inventory(args: argparse.Namespace) -> int:
    slot = SaveSlot.open(args.slot)
    payload = _inventory_payload(slot)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    for item in payload["inventory"]:
        print(
            f"#{item['index']:>2} 0x{item['start']:X} "
            f"qty={item['quantity']} pid={item['pid']} known={item['known_pid']} "
            f"type={item['type']} name={item['name']} size=0x{item['size']:X} "
            f"source={item['size_source']} confidence={item['confidence']} "
            f"ammo={item['ammo_or_charges']} ammo_type={item['ammo_type']}"
        )
        for warning in item["warnings"]:
            print(f"    warning: {warning}")
    return 0


def cmd_artifacts(args: argparse.Namespace) -> int:
    slot = SaveSlot.open(args.slot)
    payload = _artifacts_payload(slot)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    for artifact in payload["artifacts"]:
        print(
            f"{artifact['name']}: kind={artifact['kind']} size={artifact['size']} "
            f"sha256={artifact['sha256']} parser_status={artifact['parser_status']}"
        )
        for warning in artifact["warnings"]:
            print(f"  warning: {warning}")
    return 0


def cmd_raw_blocks(args: argparse.Namespace) -> int:
    slot = SaveSlot.open(args.slot)
    payload = _raw_blocks_payload(slot)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    for block in payload["raw_blocks"]:
        print(
            f"#{block['index']:>2} {block['name']}: 0x{block['start']:X}..0x{block['end']:X} "
            f"size=0x{block['size']:X} status={block['parser_status']} "
            f"entropy={block['entropy_hint']} zero={block['zero_ratio']:.3f} "
            f"plausible_i32={block['plausible_i32_count']}/{block['i32_count']}"
        )
    return 0


def cmd_globals_scan(args: argparse.Namespace) -> int:
    slot = SaveSlot.open(args.slot)
    payload = _globals_scan_payload(slot)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    for candidate in payload["candidates"]:
        print(
            f"#{candidate['block_index']:>2} {candidate['block_name']}: "
            f"0x{candidate['start']:X}..0x{candidate['end']:X} "
            f"i32={candidate['i32_count']} nonzero={candidate['nonzero_i32_count']} "
            f"min={candidate['min_i32']} max={candidate['max_i32']} "
            f"confidence={candidate['confidence']} notes={candidate['notes']}"
        )
    return 0


def cmd_fixture_snapshot(args: argparse.Namespace) -> int:
    slot = SaveSlot.open(args.slot)
    payload = _fixture_snapshot(
        slot,
        name=args.name,
        description=args.description,
        include_sha256=args.include_sha256,
        include_warnings=args.include_warnings,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    entry = next(iter(payload.values()))
    if entry.get("verify_issues") and not args.allow_invalid:
        return 1
    return 0


def cmd_fixture_check(args: argparse.Namespace) -> int:
    payload = _fixture_check_payload(args.fixture_root)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Fixture root: {payload['fixture_root']}")
        for issue in payload.get("issues", []):
            print(f"FAIL: {issue}")
        for slot_name, result in payload.get("slots", {}).items():
            prefix = "OK" if result["ok"] else "FAIL"
            print(f"{prefix}: {slot_name}")
            for issue in result.get("issues", []):
                print(f"  - {issue}")
    return 0 if payload.get("ok") else 1


def cmd_fields(args: argparse.Namespace) -> int:
    sd = _load_save(args.slot)
    for field in sorted(sd.fields.values(), key=lambda f: (f.abs_offset, f.name)):
        value = field.value
        print(f"{field.name:34s} {field.risk:12s} {field.type_name:8s} {field.endian:6s} 0x{field.abs_offset:08X} rel=0x{field.rel_offset:04X} size={field.size:<2d} value={value}")
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    sd = _load_save(args.slot)
    if args.field not in sd.fields:
        print(f"unknown field: {args.field}", file=sys.stderr)
        return 2
    f = sd.fields[args.field]
    print(f.value)
    return 0


def _ensure_write_mode(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "write", False))


def _write_if_requested(slot_path: str | Path, sd: SaveDat, args: argparse.Namespace) -> None:
    if _ensure_write_mode(args):
        backup_dir = backup_slot(slot_path)
        atomic_write_bytes(Path(slot_path) / "SAVE.DAT", bytes(sd.data))
        print(f"Backup: {backup_dir}")
        print("Written atomically: SAVE.DAT")
    else:
        print("Dry-run only; no files modified. Add --write to persist.")


def cmd_set(args: argparse.Namespace) -> int:
    sd = _load_save(args.slot)
    diffs = sd.set_field(args.field, int(args.value, 0), allow_out_of_range=args.allow_out_of_range, mode=args.mode)
    _print_diffs(diffs)
    _write_if_requested(args.slot, sd, args)
    return 0


def cmd_patch(args: argparse.Namespace) -> int:
    sd = _load_save(args.slot)
    patch = json.loads(Path(args.patch_json).read_text())
    if not isinstance(patch, dict):
        raise ValueError("patch JSON must be an object")
    diffs = sd.apply_patch(patch, allow_out_of_range=args.allow_out_of_range, mode=args.mode)
    _print_diffs(diffs)
    _write_if_requested(args.slot, sd, args)
    return 0


def cmd_backup(args: argparse.Namespace) -> int:
    dst = backup_slot(args.slot)
    print(dst)
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    slot = SaveSlot.open(args.slot)
    issues = slot.save_dat.verify()
    if not issues:
        print("OK")
        return 0
    for issue in issues:
        print(f"FAIL: {issue}")
    return 1


def _parse_raw_spec(spec: str) -> tuple[str, int, int | bytes]:
    try:
        file_name, offset_hex, tail = spec.split(":", 2)
    except ValueError as exc:
        raise ValueError("raw spec must be FILE:OFFSET:SIZE_OR_HEX") from exc
    if file_name.upper() != "SAVE.DAT":
        raise ValueError("this version supports raw access only to SAVE.DAT")
    offset = int(offset_hex, 0)
    return file_name, offset, tail


def cmd_raw_read(args: argparse.Namespace) -> int:
    _file, offset, tail = _parse_raw_spec(args.spec)
    size = int(str(tail), 0)
    sd = _load_save(args.slot)
    print(sd.raw_read(offset, size).hex())
    return 0


def cmd_raw_write(args: argparse.Namespace) -> int:
    if not args.experimental:
        print("raw-write requires --experimental", file=sys.stderr)
        return 2
    _file, offset, tail = _parse_raw_spec(args.spec)
    payload = bytes.fromhex(str(tail))
    sd = _load_save(args.slot)
    diffs = sd.raw_write(offset, payload, "raw-write")
    _print_diffs(diffs)
    _write_if_requested(args.slot, sd, args)
    return 0


def cmd_gui(args: argparse.Namespace) -> int:
    # Import Tk only when the GUI command is executed. This follows Python 3
    # stdlib guidance and keeps ordinary CLI/test paths display-independent.
    from f1se.gui import run_gui

    return run_gui(args.slot)


def cmd_preset(args: argparse.Namespace) -> int:
    sd = _load_save(args.slot)
    patch = sd.preset_patch(args.preset)
    diffs = sd.apply_patch(patch, allow_out_of_range=args.allow_out_of_range, mode=args.mode)
    _print_diffs(diffs)
    _write_if_requested(args.slot, sd, args)
    return 0


def cmd_effective(args: argparse.Namespace) -> int:
    sd = _load_save(args.slot)
    payload = {
        "selected_traits": sd.selected_traits(),
        "effective_special_static": sd.effective_special(),
        "trait_effect_notes": sd.trait_effect_notes(),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    print("Selected traits:")
    notes = payload["trait_effect_notes"]
    if notes:
        for note in notes:
            print(f"  - {note}")
    else:
        print("  none")
    print("SPECIAL effective static view: base + bonus + always-on trait adjustment")
    for stat, row in payload["effective_special_static"].items():
        print(f"  {stat:12s} base={row['base']:>3} bonus={row['bonus']:>3} trait={row['static_trait']:>3} => {row['effective_static']:>3}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="f1se", description="Fallout 1 save editor, round-trip-safe by default")
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("inspect")
    q.add_argument("slot")
    q.set_defaults(func=cmd_inspect)

    q = sub.add_parser("dump")
    q.add_argument("slot")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_dump)

    q = sub.add_parser("inventory", help="show read-only inventory/proto metadata")
    q.add_argument("slot")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_inventory)

    q = sub.add_parser("artifacts", help="show read-only slot artifact fingerprints")
    q.add_argument("slot")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_artifacts)

    q = sub.add_parser("raw-blocks", help="inspect preserved raw SAVE.DAT blocks")
    q.add_argument("slot")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_raw_blocks)

    q = sub.add_parser("globals-scan", help="read-only global/script state discovery")
    q.add_argument("slot")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_globals_scan)

    q = sub.add_parser("fixture-snapshot", help="emit a fixtures.json entry for a real save slot")
    q.add_argument("slot")
    q.add_argument("--name", help="manifest key to use; defaults to the slot directory name")
    q.add_argument("--description", default="Real Fallout 1 save fixture")
    q.add_argument("--json", action="store_true", help="accepted for explicitness; output is JSON")
    q.add_argument("--include-sha256", action="store_true")
    q.add_argument("--include-warnings", action="store_true")
    q.add_argument("--allow-invalid", action="store_true", help="return zero even if verify issues are included in the output")
    q.set_defaults(func=cmd_fixture_snapshot)

    q = sub.add_parser("fixture-check", help="validate fixtures.json against real fixture slots")
    q.add_argument("fixture_root")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_fixture_check)

    q = sub.add_parser("fields")
    q.add_argument("slot")
    q.set_defaults(func=cmd_fields)

    q = sub.add_parser("get")
    q.add_argument("slot")
    q.add_argument("field")
    q.set_defaults(func=cmd_get)

    q = sub.add_parser("set")
    q.add_argument("slot")
    q.add_argument("field")
    q.add_argument("value")
    q.add_argument("--dry-run", action="store_true", help="accepted for explicitness; dry-run is default unless --write is set")
    q.add_argument("--write", action="store_true")
    q.add_argument("--allow-out-of-range", action="store_true")
    q.add_argument("--mode", choices=["raw", "semantic"], default="raw")
    q.set_defaults(func=cmd_set)

    q = sub.add_parser("patch")
    q.add_argument("slot")
    q.add_argument("patch_json")
    q.add_argument("--dry-run", action="store_true", help="accepted for explicitness; dry-run is default unless --write is set")
    q.add_argument("--write", action="store_true")
    q.add_argument("--allow-out-of-range", action="store_true")
    q.add_argument("--mode", choices=["raw", "semantic"], default="raw")
    q.set_defaults(func=cmd_patch)

    q = sub.add_parser("backup")
    q.add_argument("slot")
    q.set_defaults(func=cmd_backup)

    q = sub.add_parser("verify")
    q.add_argument("slot")
    q.set_defaults(func=cmd_verify)

    q = sub.add_parser("raw-read")
    q.add_argument("slot")
    q.add_argument("spec", help="SAVE.DAT:0xOFFSET:SIZE")
    q.set_defaults(func=cmd_raw_read)

    q = sub.add_parser("raw-write")
    q.add_argument("slot")
    q.add_argument("spec", help="SAVE.DAT:0xOFFSET:HEX")
    q.add_argument("--experimental", action="store_true")
    q.add_argument("--dry-run", action="store_true", help="accepted for explicitness; dry-run is default unless --write is set")
    q.add_argument("--write", action="store_true")
    q.set_defaults(func=cmd_raw_write)

    q = sub.add_parser("preset", help="apply a conservative built-in patch")
    q.add_argument("slot")
    q.add_argument("preset", choices=["max-special", "heal", "clear-crippled"])
    q.add_argument("--dry-run", action="store_true", help="accepted for explicitness; dry-run is default unless --write is set")
    q.add_argument("--write", action="store_true")
    q.add_argument("--allow-out-of-range", action="store_true")
    q.add_argument("--mode", choices=["raw", "semantic"], default="raw")
    q.set_defaults(func=cmd_preset)

    q = sub.add_parser("effective", help="show trait-adjusted static SPECIAL preview")
    q.add_argument("slot")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_effective)

    q = sub.add_parser("gui", help="launch Tkinter GUI")
    q.add_argument("slot", nargs="?", help="optional save slot directory containing SAVE.DAT")
    q.set_defaults(func=cmd_gui)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
