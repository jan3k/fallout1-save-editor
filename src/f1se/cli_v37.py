from __future__ import annotations

import argparse
import json
import sys

from f1se.cli_v36 import main as previous_main
from f1se.project.fallout2_write import set_field as fallout2_set_field
from f1se.project.fallout2_write import writable_fields_payload
from f1se.project.game_detection import detect_game
from f1se.project.game_profile import GameKind

GAME_CHOICES = ("fallout1", "fallout2", "auto")


def _json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _kind(slot: str, requested: str) -> GameKind:
    if requested == "fallout1":
        return GameKind.FALLOUT1
    if requested == "fallout2":
        return GameKind.FALLOUT2
    return detect_game(slot).game_kind


def _cmd_fallout2_writable_fields(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se fallout2-writable-fields")
    parser.add_argument("slot")
    parser.add_argument("--allow-advanced", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    payload = writable_fields_payload(args.slot, allow_advanced=args.allow_advanced)
    if args.json:
        _json(payload)
    else:
        for field in payload["fields"].values():
            if field["writable"]:
                print(f"{field['name']:36s} {field['write_category']:9s} {field['type']:4s} 0x{field['abs_offset']:08X} value={field['value']}")
    return 0


def _cmd_set(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se set")
    parser.add_argument("slot")
    parser.add_argument("field")
    parser.add_argument("value")
    parser.add_argument("--game", choices=GAME_CHOICES, default="fallout1")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--allow-advanced", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    kind = _kind(args.slot, args.game)
    if kind is not GameKind.FALLOUT2:
        legacy_args = ["set", args.slot, args.field, args.value]
        if args.write:
            legacy_args.append("--write")
        if args.json:
            legacy_args.append("--json")
        return previous_main(legacy_args)

    try:
        value = int(args.value, 0)
        payload = fallout2_set_field(
            args.slot,
            args.field,
            value,
            write=args.write,
            allow_advanced=args.allow_advanced,
        )
    except Exception as exc:
        if args.json:
            _json({"game_kind": "fallout2", "ok": False, "error": str(exc), "written": False})
        else:
            print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        _json(payload)
    else:
        diff = payload["diff"]
        mode = "written" if payload["written"] else "dry-run"
        print(f"{mode}: {diff['field']} {diff['old_value']} -> {diff['new_value']} at {diff['offset_hex']}")
        if not payload["written"]:
            print("Add --write to modify SAVE.DAT. A slot backup will be created first.")
        elif payload.get("backup_path"):
            print(f"backup: {payload['backup_path']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "fallout2-writable-fields":
        return _cmd_fallout2_writable_fields(args[1:])
    if args and args[0] == "set":
        return _cmd_set(args[1:])
    return previous_main(args)
