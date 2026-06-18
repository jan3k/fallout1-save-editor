from __future__ import annotations

import argparse
import json
from collections.abc import Callable

from f1se.project.backup_restore import create_slot_backup, list_backups, restore_backup, restore_preview
from f1se.project.fixture_doctor import fixture_doctor
from f1se.project.save_diff import diff_slots
from f1se.project.smoke import smoke_payload

CommandHandler = Callable[[list[str]], int]
FallbackHandler = Callable[[list[str]], int]


def _print_payload(payload: dict, as_json: bool) -> int:
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_fixture_doctor(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se fixture-doctor")
    parser.add_argument("fixture_root")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    payload = fixture_doctor(args.fixture_root)
    _print_payload(payload, args.json)
    return 0 if payload.get("ok") else 1


def cmd_backup(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se backup")
    parser.add_argument("slot")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    payload = create_slot_backup(args.slot)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(payload["path"])
    return 0


def cmd_backups(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se backups")
    parser.add_argument("slot")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    return _print_payload(list_backups(args.slot), args.json)


def cmd_restore_preview(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se restore-preview")
    parser.add_argument("slot")
    parser.add_argument("--backup", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    return _print_payload(restore_preview(args.slot, args.backup), args.json)


def cmd_restore(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se restore")
    parser.add_argument("slot")
    parser.add_argument("--backup", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.write:
        payload = restore_preview(args.slot, args.backup)
        payload["written"] = False
        payload["write_required"] = True
        return _print_payload(payload, args.json)
    return _print_payload(restore_backup(args.slot, args.backup), args.json)


def cmd_diff(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se diff")
    parser.add_argument("left")
    parser.add_argument("right")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    return _print_payload(diff_slots(args.left, args.right), args.json)


def cmd_smoke(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se smoke")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    payload = smoke_payload()
    _print_payload(payload, args.json)
    return 0 if payload.get("ok") else 1


COMMAND_HANDLERS: dict[str, CommandHandler] = {
    "fixture-doctor": cmd_fixture_doctor,
    "backup": cmd_backup,
    "backups": cmd_backups,
    "restore-preview": cmd_restore_preview,
    "restore": cmd_restore,
    "diff": cmd_diff,
    "smoke": cmd_smoke,
}


def dispatch(args: list[str], fallback: FallbackHandler) -> int:
    if args:
        handler = COMMAND_HANDLERS.get(args[0])
        if handler is not None:
            return handler(args[1:])
    return fallback(args)
