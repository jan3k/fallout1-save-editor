from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from f1se.cli_v12 import main as previous_main
from f1se.format.slot import SaveSlot
from f1se.io.atomic_write import atomic_write_bytes
from f1se.io.backup import backup_slot
from f1se.project.inventory_workflow import build_inventory_quantity_patch, inventory_workflow_payload
from f1se.schema.fields import Diff


def _diff_to_dict(diff: Diff) -> dict[str, Any]:
    return {"file_name": diff.file_name, "offset": diff.offset, "offset_hex": f"0x{diff.offset:X}", "old": diff.old.hex(), "new": diff.new.hex(), "field_name": diff.field_name}


def _cmd_inventory_editable(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se inventory-editable")
    parser.add_argument("slot")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    slot = SaveSlot.open(args.slot)
    payload = inventory_workflow_payload(slot)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    for item in payload["items"]:
        print(f"#{item['index']} {item['name']} qty={item['quantity']} pid={item['pid']} type={item['type_name']} confidence={item['confidence']}")
    return 0


def _cmd_inventory_set_quantity(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="f1se inventory-set-quantity")
    parser.add_argument("slot")
    parser.add_argument("--index", type=int, required=True)
    parser.add_argument("--quantity", type=int, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.dry_run and args.write:
        parser.error("choose --dry-run or --write")
    slot = SaveSlot.open(args.slot)
    plan = build_inventory_quantity_patch(slot, args.index, args.quantity)
    staged = slot.save_dat.clone()
    diffs = staged.apply_patch(plan.patch)
    payload: dict[str, Any] = {"slot_path": str(slot.path), "mode": "write" if args.write else "dry-run", "written": False, "plan": plan.to_dict(), "diffs": [_diff_to_dict(diff) for diff in diffs], "backup_path": None}
    if args.write:
        backup = backup_slot(slot.path)
        slot.save_dat.apply_patch(plan.patch)
        atomic_write_bytes(Path(slot.path) / "SAVE.DAT", bytes(slot.save_dat.data))
        payload["written"] = True
        payload["backup_path"] = str(backup)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "inventory-editable":
        return _cmd_inventory_editable(args[1:])
    if args and args[0] == "inventory-set-quantity":
        return _cmd_inventory_set_quantity(args[1:])
    return previous_main(args)
