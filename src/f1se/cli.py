"""Command-line interface for f1se."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

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


def _load_save(slot_path: str | Path) -> SaveDat:
    return SaveSlot.open(slot_path).save_dat


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
        print(f"  #{item.index}: 0x{item.start:X} qty={item.quantity} pid={item.pid} type={item.type_name} name={item.object_name} size=0x{item.size:X}")
    if slot.artifacts:
        print("Slot artifacts:")
        for art in slot.artifacts:
            print(f"  {art.name}: {art.size} bytes sha256={art.sha256}")
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
