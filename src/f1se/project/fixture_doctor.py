from __future__ import annotations

from pathlib import Path
from typing import Any

from f1se.format.slot import SaveSlot
from f1se.project.fixture_workflow import fixture_status

_ALLOWED_NAMES = {"SAVE.DAT", "AUTOMAP.SAV", "fixtures.json"}
_ALLOWED_SUFFIXES = {".sav"}
_IGNORED = {".f1se-backups", "__pycache__"}


def fixture_doctor(fixture_root: str | Path) -> dict[str, Any]:
    root = Path(fixture_root)
    status = fixture_status(root)
    issues: list[str] = list(status.get("issues", []))
    warnings: list[str] = []
    checked_slots: list[dict[str, Any]] = []
    if not root.exists():
        return {"fixture_root": str(root), "ok": False, "issues": ["fixture root missing"], "warnings": [], "checked_slots": [], "status": status}
    for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if child.name in _IGNORED or child.name == "fixtures.json":
            continue
        if not child.is_dir():
            continue
        slot_issues: list[str] = []
        junk: list[str] = []
        for item in sorted(child.iterdir(), key=lambda p: p.name.lower()):
            if item.name in _IGNORED:
                continue
            if item.is_dir():
                junk.append(item.name)
                continue
            if item.name.upper() not in _ALLOWED_NAMES and item.suffix.lower() not in _ALLOWED_SUFFIXES:
                junk.append(item.name)
        if junk:
            slot_issues.append("unexpected fixture files: " + ", ".join(junk))
        try:
            slot = SaveSlot.open(child)
            verify = slot.save_dat.verify()
            slot_issues.extend(verify)
            checked_slots.append({"name": child.name, "ok": not slot_issues, "artifact_count": len(slot.artifacts), "issues": slot_issues})
        except Exception as exc:
            slot_issues.append(str(exc))
            checked_slots.append({"name": child.name, "ok": False, "artifact_count": 0, "issues": slot_issues})
        issues.extend(f"{child.name}: {issue}" for issue in slot_issues)
    if status.get("missing_recommended"):
        warnings.append("recommended fixtures missing: " + ", ".join(status["missing_recommended"]))
    return {"fixture_root": str(root), "ok": not issues, "issues": issues, "warnings": warnings, "checked_slots": checked_slots, "status": status}
