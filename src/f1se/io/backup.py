"""Slot backup helpers."""
from __future__ import annotations

import shutil
import time
from pathlib import Path


def backup_slot(slot_path: str | Path) -> Path:
    slot = Path(slot_path).resolve()
    if not slot.is_dir():
        raise ValueError(f"slot path is not a directory: {slot}")
    root = slot / ".f1se-backups"
    root.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dst = root / stamp
    n = 0
    while dst.exists():
        n += 1
        dst = root / f"{stamp}-{n}"
    dst.mkdir()
    for child in slot.iterdir():
        if child.name == ".f1se-backups":
            continue
        if child.is_file():
            shutil.copy2(child, dst / child.name)
        elif child.is_dir():
            shutil.copytree(child, dst / child.name)
    return dst
