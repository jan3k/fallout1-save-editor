from __future__ import annotations

import argparse
import json
import sys

from f1se.cli_v33 import main as previous_main
from f1se.project.game_detection import detect_game
from f1se.project.game_profile import GameKind
from f1se.project.progression import progression_summary

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


def _cmd_progression(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se progression")
    parser.add_argument("slot")
    parser.add_argument("--game", choices=GAME_CHOICES, default="fallout1")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.game == "fallout2":
        reason = "progression is currently implemented for Fallout 1 only"
        if args.json:
            _json(_unsupported_payload(args.slot, reason))
        else:
            print(reason, file=sys.stderr)
        return 2

    try:
        payload = progression_summary(args.slot)
    except Exception as exc:
        if args.game == "auto":
            reason = f"progression could not parse this slot as Fallout 1: {exc}"
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
    level = payload["level"]
    perk = payload["perk_cadence"]
    print("Game: Fallout 1")
    print(f"Slot: {payload['slot_path']}")
    print(f"Player: {ident['player_name']}  Save: {ident['save_name']}")
    print(f"Level: {level['current']}/{level['max']}  XP: {payload['experience']}  Skill points: {payload['skill_points']}")
    if level["next"] is None:
        print("Next level: max level reached")
    else:
        print(f"Next level: {level['next']} at {level['next_threshold']} XP, remaining={level['xp_to_next']}")
    if perk["next_perk_level"] is None:
        print(f"Next perk: none before level cap, cadence={perk['interval_levels']} levels ({perk['reason']})")
    else:
        print(
            f"Next perk: level {perk['next_perk_level']} at {perk['next_perk_xp_threshold']} XP, "
            f"remaining={perk['xp_to_next_perk_level']}, cadence={perk['interval_levels']} levels ({perk['reason']})"
        )
    print(f"Karma: {payload['karma']}  Reputation: {payload['reputation']}")
    if payload["traits"]:
        print("Traits: " + ", ".join(payload["traits"]))
    if payload["warnings"]:
        print("Warnings:")
        for warning in payload["warnings"]:
            print(f"  - {warning}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "progression":
        return _cmd_progression(args[1:])
    return previous_main(args)
