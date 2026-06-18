from __future__ import annotations

import argparse
import json
import sys

from f1se.cli_v30 import main as previous_main
from f1se.project.fixture_coverage import fixture_coverage


def _cmd_fixture_coverage(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se fixture-coverage")
    parser.add_argument("fixture_root")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    print(json.dumps(fixture_coverage(args.fixture_root), indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "fixture-coverage":
        return _cmd_fixture_coverage(args[1:])
    return previous_main(args)
