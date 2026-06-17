from __future__ import annotations

import argparse
import json
import sys

from f1se.cli import main as base_main
from f1se.format.global_state import discover_global_state_candidates
from f1se.format.raw_inspection import inspect_raw_blocks
from f1se.format.slot import SaveSlot


def _raw_blocks(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="f1se raw-blocks")
    p.add_argument("slot")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    slot = SaveSlot.open(args.slot)
    rows = [row.to_dict() for row in inspect_raw_blocks(slot.save_dat.data, slot.save_dat.blocks)]
    if args.json:
        print(json.dumps({"slot_path": str(slot.path), "raw_blocks": rows}, indent=2, sort_keys=True))
    else:
        for row in rows:
            print(f"#{row['index']:>2} {row['name']}: 0x{row['start']:X}..0x{row['end']:X} size=0x{row['size']:X} {row['entropy_hint']}")
    return 0


def _globals_scan(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="f1se globals-scan")
    p.add_argument("slot")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    slot = SaveSlot.open(args.slot)
    rows = [row.to_dict() for row in discover_global_state_candidates(slot.save_dat.data, slot.save_dat.blocks)]
    if args.json:
        print(json.dumps({"slot_path": str(slot.path), "candidates": rows}, indent=2, sort_keys=True))
    else:
        for row in rows:
            print(f"#{row['block_index']:>2} {row['block_name']}: 0x{row['start']:X}..0x{row['end']:X} confidence={row['confidence']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "raw-blocks":
        return _raw_blocks(args[1:])
    if args and args[0] == "globals-scan":
        return _globals_scan(args[1:])
    return base_main(args)
