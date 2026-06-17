from __future__ import annotations

import argparse
import json
import sys

from f1se.cli_v19 import main as previous_main
from f1se.project.release_audit import audit_exit_code, run_release_audit


def _cmd_release_audit(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se release-audit")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    payload = run_release_audit()
    payload["strict"] = bool(args.strict)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"status: {payload['status']}")
        print(f"strict: {payload['strict']}")
        for check in payload["checks"]:
            print(f"{check['status']} {check['id']}: {check['summary']}")
    return audit_exit_code(payload, strict=args.strict)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "release-audit":
        return _cmd_release_audit(args[1:])
    return previous_main(args)
