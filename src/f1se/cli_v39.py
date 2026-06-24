from __future__ import annotations

import argparse
import json
import sys

from f1se.cli_v38 import main as previous_main
from f1se.project.skill_write import set_skill

GAME_CHOICES = ("fallout1", "fallout2", "auto")


def _json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _cmd_skill_set(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se skill-set")
    parser.add_argument("slot")
    parser.add_argument("skill", help="skill name, e.g. speech or retoryka")
    parser.add_argument("value")
    parser.add_argument("--game", choices=GAME_CHOICES, default="auto")
    parser.add_argument("--allow-out-of-range", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = set_skill(
            args.slot,
            args.skill,
            int(args.value, 0),
            game=args.game,
            write=args.write,
            allow_out_of_range=args.allow_out_of_range,
        )
    except Exception as exc:
        if args.json:
            _json({"ok": False, "error": str(exc), "written": False})
        else:
            print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        _json(payload)
        return 0

    mode = "written" if payload.get("written") else "dry-run"
    field = payload.get("field")
    if isinstance(field, dict):
        field_name = field.get("name") or field.get("field") or payload.get("field")
    else:
        field_name = field
    old_value = payload.get("old_value", payload.get("diff", {}).get("old_value"))
    new_value = payload.get("new_value", payload.get("diff", {}).get("new_value"))
    print(f"{mode}: {payload['game_kind']} {payload.get('skill')} {old_value} -> {new_value} ({field_name})")
    if payload.get("diffs"):
        for diff in payload["diffs"]:
            print(f"  {diff['file']}:{diff['offset_hex']} {diff['old_bytes']} -> {diff['new_bytes']} {diff['field']}")
    elif payload.get("diff"):
        diff = payload["diff"]
        print(f"  SAVE.DAT:{diff['offset_hex']} {diff['old_bytes']} -> {diff['new_bytes']} {diff['field']}")
    if payload.get("note"):
        print(f"note: {payload['note']}")
    if not payload.get("written"):
        print("Add --write to modify SAVE.DAT. A slot backup will be created first.")
    elif payload.get("backup_path"):
        print(f"backup: {payload['backup_path']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "skill-set":
        return _cmd_skill_set(args[1:])
    return previous_main(args)
