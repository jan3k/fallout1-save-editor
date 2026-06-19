from __future__ import annotations

import argparse
import json
import sys

from f1se.cli_v35 import main as previous_main
from f1se.project.combat import combat_summary
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


def _cmd_combat_summary(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se combat-summary")
    parser.add_argument("slot")
    parser.add_argument("--game", choices=GAME_CHOICES, default="fallout1")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.game == "fallout2":
        reason = "combat-summary is currently implemented for Fallout 1 only"
        if args.json:
            _json(_unsupported_payload(args.slot, reason))
        else:
            print(reason, file=sys.stderr)
        return 2

    try:
        payload = combat_summary(args.slot)
    except Exception as exc:
        if args.game == "auto":
            reason = f"combat-summary could not parse this slot as Fallout 1: {exc}"
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
    hp = payload["hp"]
    status = payload["status_effects"]
    print("Game: Fallout 1")
    print(f"Slot: {payload['slot_path']}")
    print(f"Player: {ident['player_name']}  Save: {ident['save_name']}")
    print(f"HP: {hp['current']}/{hp['max']} missing={hp['missing']} percent={hp['percent']}")
    print(
        f"AP={payload['action_points']} AC={payload['armor_class']} melee={payload['melee_damage']} "
        f"carry={payload['carry_weight']} sequence={payload['sequence']}"
    )
    print(
        f"heal={payload['healing_rate']} crit={payload['critical_chance']} "
        f"rad_res={payload['resistances']['radiation']} poison_res={payload['resistances']['poison']}"
    )
    print(f"Radiation={status['radiation']} Poison={status['poison']}")
    if status["crippled_body_parts"]["active"]:
        print("Crippled: " + ", ".join(status["crippled_body_parts"]["active"]))
    else:
        print("Crippled: none")
    if payload["warnings"]:
        print("Warnings:")
        for warning in payload["warnings"]:
            print(f"  - {warning}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "combat-summary":
        return _cmd_combat_summary(args[1:])
    return previous_main(args)
