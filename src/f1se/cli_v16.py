from __future__ import annotations

import argparse
import json
import sys

from f1se.cli_v15 import main as previous_main
from f1se.project.cli_index import commands_payload


def _cmd_commands(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se commands")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    payload = commands_payload()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    for row in payload["commands"]:
        suffix = " json" if row["json"] else ""
        print(f"{row['name']}{suffix}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "commands":
        return _cmd_commands(args[1:])
    return previous_main(args)
