from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from f1se.cli_v31 import main as previous_main
from f1se.format.fallout2.save_dat import Fallout2SaveDat
from f1se.format.slot import SaveSlot
from f1se.project.compatibility import compatibility_payload
from f1se.project.game_detection import detect_game, resolve_save_dat_path
from f1se.project.game_profile import GameKind

GAME_CHOICES = ("fallout1", "fallout2", "auto")


def _json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _detect_kind(path: str | Path, requested: str) -> GameKind:
    if requested == "fallout1":
        return GameKind.FALLOUT1
    if requested == "fallout2":
        return GameKind.FALLOUT2
    return detect_game(path).game_kind


def _load_fo2(path: str | Path) -> Fallout2SaveDat:
    return Fallout2SaveDat.from_path(resolve_save_dat_path(path))


def _print_fo2_inspect(save: Fallout2SaveDat) -> None:
    print(f"Game: Fallout 2 (read-only)")
    print(f"SAVE.DAT: {save.path}")
    print(f"Size: {len(save.data)} / 0x{len(save.data):X}")
    print(f"sha256: {save.sha256}")
    print(f"Signature: {save.header.signature}")
    print(f"Version: {save.header.version}")
    print(f"Player: {save.header.player_name}")
    print(f"Save name: {save.header.save_name}")
    print(f"Current map: {save.header.current_map_file}")
    print(f"Parser status: {save.parser_status}")
    print("Sections:")
    for section in save.sections.values():
        print(f"  {section.name}: 0x{section.start:X}..0x{section.end:X} confidence={section.confidence}")
    print("Key fields:")
    for key in ("pc.level", "pc.experience", "pc.skill_points", "player.current_hp"):
        if key in save.fields:
            field = save.fields[key]
            print(f"  {key}: {field.value} @ 0x{field.abs_offset:X} confidence={field.confidence}")
    if save.warnings:
        print("Warnings:")
        for warning in sorted(set(save.warnings)):
            print(f"  - {warning}")


def _cmd_detect(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se detect")
    parser.add_argument("slot")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = detect_game(args.slot)
    if args.json:
        _json(result.to_dict())
    else:
        print(f"{result.game_kind.value} confidence={result.confidence} read_only={result.read_only}")
        print(result.reason)
    return 0 if result.game_kind is not GameKind.UNKNOWN else 1


def _cmd_compatibility(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se compatibility")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    payload = compatibility_payload()
    if args.json:
        _json(payload)
    else:
        for game, matrix in payload["games"].items():
            print(game)
            for command, row in matrix.items():
                if command == "profile":
                    continue
                print(f"  {command:12s} {row['status']:13s} {row['reason']}")
    return 0


def _cmd_dump_or_inspect(command: str, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog=f"f1se {command}")
    parser.add_argument("slot")
    parser.add_argument("--game", choices=GAME_CHOICES, default="fallout1")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    kind = _detect_kind(args.slot, args.game)
    if kind is GameKind.FALLOUT2:
        save = _load_fo2(args.slot)
        if args.json:
            _json(save.to_dict())
        else:
            _print_fo2_inspect(save)
        return 0
    if args.game == "auto" and kind is GameKind.UNKNOWN:
        result = detect_game(args.slot)
        if args.json:
            _json(result.to_dict())
        else:
            print(result.reason, file=sys.stderr)
        return 1
    legacy_args = [command, args.slot]
    if args.json:
        legacy_args.append("--json")
    return previous_main(legacy_args)


def _cmd_fields(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se fields")
    parser.add_argument("slot")
    parser.add_argument("--game", choices=GAME_CHOICES, default="fallout1")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    kind = _detect_kind(args.slot, args.game)
    if kind is GameKind.FALLOUT2:
        save = _load_fo2(args.slot)
        payload = save.fields_payload()
        if args.json:
            _json(payload)
        else:
            for field in payload["fields"].values():
                print(
                    f"{field['name']:34s} {field['risk']:12s} {field['type']:8s} {field['endian']:6s} "
                    f"0x{field['abs_offset']:08X} rel=0x{field['rel_offset']:04X} size={field['size']:<2d} "
                    f"confidence={field['confidence']:6s} writable={field['writable']} value={field['value']}"
                )
        return 0
    legacy_args = ["fields", args.slot]
    return previous_main(legacy_args)


def _cmd_get(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se get")
    parser.add_argument("slot")
    parser.add_argument("field")
    parser.add_argument("--game", choices=GAME_CHOICES, default="fallout1")
    args = parser.parse_args(argv)
    kind = _detect_kind(args.slot, args.game)
    if kind is GameKind.FALLOUT2:
        save = _load_fo2(args.slot)
        if args.field not in save.fields:
            print(f"unknown field: {args.field}", file=sys.stderr)
            return 2
        print(save.fields[args.field].value)
        return 0
    return previous_main(["get", args.slot, args.field])


def _cmd_inventory(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se inventory")
    parser.add_argument("slot")
    parser.add_argument("--game", choices=GAME_CHOICES, default="fallout1")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    kind = _detect_kind(args.slot, args.game)
    if kind is GameKind.FALLOUT2:
        save = _load_fo2(args.slot)
        payload = save.inventory_payload()
        if args.json:
            _json(payload)
        else:
            for item in payload["inventory"]:
                print(f"#{item['index']:>2} 0x{item['raw_object_offset']:X} qty={item['quantity']} pid={item['pid']} confidence={item['confidence']}")
                for warning in item["warnings"]:
                    print(f"    warning: {warning}")
        return 0
    legacy_args = ["inventory", args.slot]
    if args.json:
        legacy_args.append("--json")
    return previous_main(legacy_args)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "detect":
        return _cmd_detect(args[1:])
    if args and args[0] == "compatibility":
        return _cmd_compatibility(args[1:])
    if args and args[0] in {"dump", "inspect"}:
        return _cmd_dump_or_inspect(args[0], args[1:])
    if args and args[0] == "fields":
        return _cmd_fields(args[1:])
    if args and args[0] == "get":
        return _cmd_get(args[1:])
    if args and args[0] == "inventory":
        return _cmd_inventory(args[1:])
    return previous_main(args)
