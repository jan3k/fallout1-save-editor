from __future__ import annotations

import argparse
import json
import sys

from f1se.cli_v34 import main as previous_main
from f1se.project.derived_stats import derived_stats_report
from f1se.project.game_detection import detect_game

GAME_CHOICES = ("fallout1", "fallout2", "auto")


def _json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _unsupported_payload(slot: str, reason: str) -> dict:
    detection = detect_game(slot)
    return {
        "game_kind": detection.game_kind.value,
        "read_only": True,
        "supported": False,
        "reason": reason,
        "detection": detection.to_dict(),
    }


def _cmd_derived_stats(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se derived-stats")
    parser.add_argument("slot")
    parser.add_argument("--game", choices=GAME_CHOICES, default="fallout1")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.game == "fallout2":
        reason = "derived-stats is currently implemented for Fallout 1 only"
        if args.json:
            _json(_unsupported_payload(args.slot, reason))
        else:
            print(reason, file=sys.stderr)
        return 2

    try:
        payload = derived_stats_report(args.slot)
    except Exception as exc:
        if args.game == "auto":
            reason = f"derived-stats could not parse this slot as Fallout 1: {exc}"
            if args.json:
                _json(_unsupported_payload(args.slot, reason))
            else:
                print(reason, file=sys.stderr)
            return 2
        raise

    if args.json:
        _json(payload)
        return 0

    ident = payload["identity"]
    summary = payload["summary"]
    print("Game: Fallout 1")
    print(f"Slot: {payload['slot_path']}")
    print(f"Player: {ident['player_name']}  Save: {ident['save_name']}")
    print("Source SPECIAL:")
    for stat, value in payload["source_special"].items():
        print(f"  {stat:12s} {value}")
    print(f"Derived stats checked: {summary['checked_count']}  mismatches: {summary['mismatch_count']}")
    if payload["mismatches"]:
        print("Mismatches:")
        for row in payload["mismatches"]:
            print(f"  {row['field']}: actual={row['actual']} expected={row['expected']} delta={row['delta']} ({row['reason']})")
    else:
        print("All checked derived stats match formula targets.")
    if payload["warnings"]:
        print("Warnings:")
        for warning in payload["warnings"]:
            print(f"  - {warning}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "derived-stats":
        return _cmd_derived_stats(args[1:])
    return previous_main(args)
