from __future__ import annotations

import argparse
import json
import sys

from f1se.cli_v20 import main as previous_main
from f1se.project.backup_restore import list_backups, restore_backup, restore_preview
from f1se.project.fixture_doctor import fixture_doctor
from f1se.project.save_diff import diff_slots
from f1se.project.smoke import smoke_payload


def _print(payload: dict, as_json: bool) -> int:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _cmd_fixture_doctor(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se fixture-doctor")
    parser.add_argument("fixture_root")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    payload = fixture_doctor(args.fixture_root)
    _print(payload, args.json)
    return 0 if payload.get("ok") else 1


def _cmd_backups(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se backups")
    parser.add_argument("slot")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    return _print(list_backups(args.slot), args.json)


def _cmd_restore_preview(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se restore-preview")
    parser.add_argument("slot")
    parser.add_argument("--backup", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    return _print(restore_preview(args.slot, args.backup), args.json)


def _cmd_restore(argv: list[str]) -> int:
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
        return _print(payload, args.json)
    return _print(restore_backup(args.slot, args.backup), args.json)


def _cmd_diff(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se diff")
    parser.add_argument("left")
    parser.add_argument("right")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    return _print(diff_slots(args.left, args.right), args.json)


def _cmd_smoke(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se smoke")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    payload = smoke_payload()
    _print(payload, args.json)
    return 0 if payload.get("ok") else 1


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "fixture-doctor":
        return _cmd_fixture_doctor(args[1:])
    if args and args[0] == "backups":
        return _cmd_backups(args[1:])
    if args and args[0] == "restore-preview":
        return _cmd_restore_preview(args[1:])
    if args and args[0] == "restore":
        return _cmd_restore(args[1:])
    if args and args[0] == "diff":
        return _cmd_diff(args[1:])
    if args and args[0] == "smoke":
        return _cmd_smoke(args[1:])
    return previous_main(args)
