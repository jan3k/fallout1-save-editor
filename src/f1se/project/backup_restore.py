from __future__ import annotations

from pathlib import Path
import hashlib
import shutil
from typing import Any

from f1se.io.backup import backup_slot


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _backup_root(slot_path: str | Path) -> Path:
    return Path(slot_path).resolve() / ".f1se-backups"


def list_backups(slot_path: str | Path) -> dict[str, Any]:
    slot = Path(slot_path).resolve()
    root = _backup_root(slot)
    rows: list[dict[str, Any]] = []
    if root.exists():
        for child in sorted(root.iterdir(), key=lambda p: p.name, reverse=True):
            if not child.is_dir():
                continue
            save = child / "SAVE.DAT"
            rows.append({"name": child.name, "path": str(child), "has_save_dat": save.is_file(), "save_dat_sha256": _sha(save) if save.is_file() else None})
    return {"slot_path": str(slot), "backup_root": str(root), "backups": rows, "count": len(rows)}


def _resolve_backup(slot_path: str | Path, name: str) -> Path:
    root = _backup_root(slot_path).resolve()
    target = (root / name).resolve()
    if root not in target.parents:
        raise ValueError("backup path escapes backup root")
    if not target.is_dir():
        raise FileNotFoundError(f"backup not found: {name}")
    if not (target / "SAVE.DAT").is_file():
        raise FileNotFoundError("backup SAVE.DAT missing")
    return target


def restore_preview(slot_path: str | Path, name: str) -> dict[str, Any]:
    slot = Path(slot_path).resolve()
    backup = _resolve_backup(slot, name)
    files: list[dict[str, Any]] = []
    for child in sorted(backup.iterdir(), key=lambda p: p.name.lower()):
        if child.is_file():
            dst = slot / child.name
            files.append({"name": child.name, "source_sha256": _sha(child), "destination_exists": dst.exists(), "destination_sha256": _sha(dst) if dst.is_file() else None})
    return {"slot_path": str(slot), "backup": backup.name, "files": files, "can_restore": True, "write_required": True}


def restore_backup(slot_path: str | Path, name: str) -> dict[str, Any]:
    slot = Path(slot_path).resolve()
    backup = _resolve_backup(slot, name)
    safety_backup = backup_slot(slot)
    for child in list(slot.iterdir()):
        if child.name == ".f1se-backups":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    for child in sorted(backup.iterdir(), key=lambda p: p.name.lower()):
        if child.is_file():
            shutil.copy2(child, slot / child.name)
        elif child.is_dir():
            shutil.copytree(child, slot / child.name)
    return {"slot_path": str(slot), "backup": backup.name, "safety_backup": str(safety_backup), "restored": True}
