from __future__ import annotations

import argparse
import json
import sys

from f1se.cli_v16 import main as previous_main
from f1se.project.json_contracts import contracts_payload


def _cmd_json_contracts(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se json-contracts")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    payload = contracts_payload()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    for row in payload["contracts"]:
        print(f"{row['id']}: {row['command']} required={','.join(row['required_keys'])}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "json-contracts":
        return _cmd_json_contracts(args[1:])
    return previous_main(args)
