from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from f1se.cli_v32 import main as previous_main
from f1se.project.character_summary import character_summary
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


def _cmd_character_summary(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se character-summary")
    parser.add_argument("slot")
    parser.add_argument("--game", choices=GAME_CHOICES, default="fallout1")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.game == "fallout2":
        reason = "character-summary is currently implemented for Fallout 1 only"
        if args.json:
            _json(_unsupported_payload(args.slot, reason))
        else:
            print(reason, file=sys.stderr)
        return 2

    try:
        payload = character_summary(args.slot)
    except Exception as exc:
        if args.game == "auto":
            reason = f"character-summary could not parse this slot as Fallout 1: {exc}"
            if args.json:
                _json(_unsupported_payload(args.slot, reason))
            else:
                print(reason, file=sys.stderr)
            return 2
        raise

    if args.json:
        _json(payload)
        return 0

    identity = payload["identity"]
    progression = payload["progression"]
    status = payload["status_effects"]
    inv = payload["inventory_summary"]
    print(f"Game: Fallout 1")
    print(f"Slot: {payload['slot_path']}")
    print(f"Player: {identity['player_name']}  Save: {identity['save_name']}")
    print(f"Map: {identity['current_map_file']}  Saved: {identity['saved_date']}")
    print(f"Level: {progression['level']}  XP: {progression['experience']}  Skill points: {progression['skill_points']}")
    print(f"HP: {status['current_hp']}/{status['max_hp']}  Radiation: {status['radiation']}  Poison: {status['poison']}")
    print("SPECIAL:")
    for name, row in payload["special"].items():
        print(f"  {name:12s} base={row['base']:>3} bonus={row['bonus']:>3} trait={row['static_trait']:>3} effective={row['effective_static']:>3}")
    print(f"Inventory: {inv['parsed_item_count']} parsed item(s), unknown PID count={inv['unknown_pid_count']}")
    if payload["active_perks"]:
        print("Active perks:")
        for perk in payload["active_perks"]:
            print(f"  {perk['name']} rank={perk['rank']}")
    if payload["warnings"]:
        print("Warnings:")
        for warning in payload["warnings"]:
            print(f"  - {warning}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "character-summary":
        return _cmd_character_summary(args[1:])
    return previous_main(args)
