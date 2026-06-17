from __future__ import annotations

import argparse
import json
import sys

from f1se.cli_v09 import main as previous_main
from f1se.project.features import FEATURES, filter_features


def _cmd_features(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se features")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--category")
    parser.add_argument("--status")
    args = parser.parse_args(argv)
    rows = filter_features(category=args.category, status=args.status)
    if args.json:
        print(json.dumps({"features": [row.to_dict() for row in rows]}, indent=2, sort_keys=True))
        return 0
    if not rows:
        print("No features matched.")
        return 0
    for row in rows:
        interface = ",".join(row.interface)
        print(f"{row.category:20s} | {row.name:38s} | f1se={row.f1se_status:12s} | f12se={row.f12se_status} | risk={row.risk_level:10s} | interface={interface} | {row.notes}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "features":
        return _cmd_features(args[1:])
    return previous_main(args)
