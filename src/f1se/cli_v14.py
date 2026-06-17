from __future__ import annotations

import argparse
import json
import sys

from f1se.cli_v13 import main as previous_main
from f1se.format.global_state import discover_global_state_candidates
from f1se.format.slot import SaveSlot
from f1se.project.global_labels import global_labels_payload, labels_by_block


def _cmd_global_labels(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se global-labels")
    parser.add_argument("--block", type=int)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    payload = global_labels_payload(args.block)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    for label in payload["labels"]:
        print(f"#{label['block_index']} {label['block_name']}: {label['label']} confidence={label['confidence']} source={label['source']}")
        print(f"  {label['description']}")
    return 0


def _cmd_globals_scan(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se globals-scan")
    parser.add_argument("slot")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    slot = SaveSlot.open(args.slot)
    rows = []
    for item in discover_global_state_candidates(slot.save_dat.data, slot.save_dat.blocks):
        row = item.to_dict()
        row["labels"] = labels_by_block(item.block_index)
        rows.append(row)
    payload = {"slot_path": str(slot.path), "candidates": rows}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    for row in rows:
        names = ",".join(label["label"] for label in row["labels"]) or "none"
        print(f"#{row['block_index']:>2} {row['block_name']}: 0x{row['start']:X}..0x{row['end']:X} confidence={row['confidence']} labels={names}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "global-labels":
        return _cmd_global_labels(args[1:])
    if args and args[0] == "globals-scan":
        return _cmd_globals_scan(args[1:])
    return previous_main(args)
