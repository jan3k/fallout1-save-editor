from __future__ import annotations

import argparse
import json
import sys

from f1se.cli_v14 import main as previous_main
from f1se.format.slot import ARTIFACT_MAP_SAV, SaveSlot
from f1se.project.map_summary import summarize_map


def _map_rows(slot: SaveSlot, file_name: str | None) -> list[dict]:
    rows = []
    for artifact in slot.artifacts:
        if artifact.kind != ARTIFACT_MAP_SAV:
            continue
        if file_name is not None and artifact.name.lower() != file_name.lower():
            continue
        rows.append(summarize_map(slot.path / artifact.name).to_dict())
    return rows


def _cmd_map_summary(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se map-summary")
    parser.add_argument("slot")
    parser.add_argument("--file")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    slot = SaveSlot.open(args.slot)
    payload = {"slot_path": str(slot.path), "maps": _map_rows(slot, args.file)}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    for row in payload["maps"]:
        print(f"{row['file_name']}: candidates={row['candidate_count']} pids={len(row['pids'])} regions={len(row['regions'])} status={row['parser_status']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "map-summary":
        return _cmd_map_summary(args[1:])
    return previous_main(args)
