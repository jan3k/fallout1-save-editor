from __future__ import annotations

from pathlib import Path
import hashlib
import json
import shutil
from typing import Any

from f1se.io.backup import backup_slot

MANIFEST_NAME = ".f1se-manifest.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _backup_root(slot_path: str | Path) -> Path:
    return Path(slot_path).resolve() / ".f1se-backups"


def _file_entry(path: Path, *, root: Path) -> dict[str, Any]:
    rel = path.relative_to(root).as_posix()
    return {"name": rel, "size": path.stat().st_size, "sha256": _sha(path)}


def build_backup_manifest(backup_path: str | Path) -> dict[str, Any]:
    backup = Path(backup_path).resolve()
    files = [
        _file_entry(child, root=backup)
        for child in sorted(backup.rglob("*"), key=lambda p: p.as_posix().lower())
        if child.is_file() and child.name != MANIFEST_NAME
    ]
    return {"backup": backup.name, "file_count": len(files), "files": files}


def write_backup_manifest(backup_path: str | Path) -> dict[str, Any]:
    backup = Path(backup_path).resolve()
    manifest = build_backup_manifest(backup)
    (backup / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def create_slot_backup(slot_path: str | Path) -> dict[str, Any]:
    backup = backup_slot(slot_path)
    manifest = write_backup_manifest(backup)
    return {"slot_path": str(Path(slot_path).resolve()), "backup": backup.name, "path": str(backup), "manifest": manifest}


def _read_manifest(backup: Path) -> dict[str, Any] | None:
    manifest_path = backup / MANIFEST_NAME
    if not manifest_path.is_file():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def list_backups(slot_path: str | Path) -> dict[str, Any]:
    slot = Path(slot_path).resolve()
    root = _backup_root(slot)
    rows: list[dict[str, Any]] = []
    if root.exists():
        for child in sorted(root.iterdir(), key=lambda p: p.name, reverse=True):
            if not child.is_dir():
                continue
            save = child / "SAVE.DAT"
            manifest = _read_manifest(child)
            rows.append({
                "name": child.name,
                "path": str(child),
                "has_save_dat": save.is_file(),
                "save_dat_sha256": _sha(save) if save.is_file() else None,
                "manifest_present": manifest is not None,
                "manifest_file_count": manifest.get("file_count") if manifest else None,
            })
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
    manifest = _read_manifest(backup)
    files: list[dict[str, Any]] = []
    changed = 0
    missing = 0
    for child in sorted(backup.rglob("*"), key=lambda p: p.as_posix().lower()):
        if not child.is_file() or child.name == MANIFEST_NAME:
            continue
        rel = child.relative_to(backup)
        dst = slot / rel
        dst_hash = _sha(dst) if dst.is_file() else None
        src_hash = _sha(child)
        if dst_hash != src_hash:
            changed += 1
        if not dst.exists():
            missing += 1
        files.append({"name": rel.as_posix(), "source_sha256": src_hash, "destination_exists": dst.exists(), "destination_sha256": dst_hash})
    return {
        "slot_path": str(slot),
        "backup": backup.name,
        "files": files,
        "can_restore": True,
        "write_required": True,
        "safety_backup_before_restore": True,
        "manifest_present": manifest is not None,
        "manifest_file_count": manifest.get("file_count") if manifest else None,
        "diff_summary": {"changed_or_missing_files": changed, "missing_destination_files": missing},
    }


def restore_backup(slot_path: str | Path, name: str) -> dict[str, Any]:
    slot = Path(slot_path).resolve()
    backup = _resolve_backup(slot, name)
    preview = restore_preview(slot, name)
    safety = create_slot_backup(slot)
    for child in list(slot.iterdir()):
        if child.name == ".f1se-backups":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    for child in sorted(backup.iterdir(), key=lambda p: p.name.lower()):
        if child.name == MANIFEST_NAME:
            continue
        if child.is_file():
            shutil.copy2(child, slot / child.name)
        elif child.is_dir():
            shutil.copytree(child, slot / child.name)
    return {"slot_path": str(slot), "backup": backup.name, "safety_backup": safety, "restored": True, "preview": preview}
