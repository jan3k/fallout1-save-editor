from __future__ import annotations

import argparse
import json
import sys

from f1se.cli_v11 import main as previous_main
from f1se.project.fixture_workflow import fixture_import_plan, fixture_status, recommended_fixture_plan, write_fixture_import


def _cmd_fixture_plan(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se fixture-plan")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    rows = recommended_fixture_plan()
    if args.json:
        print(json.dumps({"recommended_fixtures": rows}, indent=2, sort_keys=True))
        return 0
    for row in rows:
        print(f"{row['name']}: {row['goal']} | requires={row['requirements']} | coverage={row['coverage']} | source={row['source']}")
    return 0


def _cmd_fixture_status(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se fixture-status")
    parser.add_argument("fixture_root")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    payload = fixture_status(args.fixture_root)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload.get("ok") else 1
    print(f"Fixture root: {payload['fixture_root']}")
    print(f"Manifest count: {payload.get('manifest_count', 0)}")
    print(f"Coverage score: {payload.get('coverage_score', 0)}")
    for name in payload.get("missing_recommended", []):
        print(f"missing: {name}")
    for issue in payload.get("issues", []):
        print(f"FAIL: {issue}")
    return 0 if payload.get("ok") else 1


def _cmd_fixture_import(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se fixture-import")
    parser.add_argument("source")
    parser.add_argument("--fixture-root", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--description", default="Imported real Fallout 1 save fixture")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.dry_run and args.write:
        parser.error("choose only one of --dry-run or --write")
    plan = fixture_import_plan(args.source, args.fixture_root, args.name, force=args.force, description=args.description)
    payload = plan.to_dict()
    payload["mode"] = "write" if args.write else "dry-run"
    payload["written"] = False
    if args.write:
        write_fixture_import(plan, force=args.force)
        payload["written"] = True
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Fixture import {payload['mode']}: {plan.name}")
        print(f"Source: {plan.source}")
        print(f"Destination: {plan.destination}")
        for name in plan.files:
            print(f"file: {name}")
        for issue in plan.issues + plan.verify_issues:
            print(f"issue: {issue}")
        print("Written." if payload["written"] else "Dry-run only; no files modified.")
    return 0 if (payload["written"] or plan.ok) else 1


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "fixture-plan":
        return _cmd_fixture_plan(args[1:])
    if args and args[0] == "fixture-status":
        return _cmd_fixture_status(args[1:])
    if args and args[0] == "fixture-import":
        return _cmd_fixture_import(args[1:])
    return previous_main(args)
