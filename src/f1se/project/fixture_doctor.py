from __future__ import annotations

from pathlib import Path
from typing import Any

from f1se.format.slot import SaveSlot
from f1se.project.fixture_workflow import fixture_status

_ALLOWED_NAMES = {"SAVE.DAT", "AUTOMAP.SAV", "fixtures.json"}
_ALLOWED_SUFFIXES = {".sav"}
_IGNORED = {".f1se-backups", "__pycache__"}


def _finding(severity: str, code: str, message: str, *, slot: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"severity": severity, "code": code, "message": message}
    if slot is not None:
        row["slot"] = slot
    return row


def fixture_doctor(fixture_root: str | Path) -> dict[str, Any]:
    root = Path(fixture_root)
    status = fixture_status(root)
    issues: list[str] = list(status.get("issues", []))
    warnings: list[str] = []
    findings: list[dict[str, Any]] = []
    checked_slots: list[dict[str, Any]] = []
    for issue in status.get("issues", []):
        findings.append(_finding("error", "fixture_status", issue))
    if not root.exists():
        findings.append(_finding("error", "fixture_root_missing", "fixture root missing"))
        return {"fixture_root": str(root), "ok": False, "issues": ["fixture root missing"], "warnings": [], "findings": findings, "checked_slots": [], "status": status}
    for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if child.name in _IGNORED or child.name == "fixtures.json":
            continue
        if not child.is_dir():
            continue
        slot_issues: list[str] = []
        slot_findings: list[dict[str, Any]] = []
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
            msg = "unexpected fixture files: " + ", ".join(junk)
            slot_issues.append(msg)
            slot_findings.append(_finding("warning", "unexpected_fixture_file", msg, slot=child.name))
        try:
            slot = SaveSlot.open(child)
            verify = slot.save_dat.verify()
            slot_issues.extend(verify)
            for issue in verify:
                slot_findings.append(_finding("error", "save_verify", issue, slot=child.name))
            checked_slots.append({"name": child.name, "ok": not slot_issues, "artifact_count": len(slot.artifacts), "issues": slot_issues, "findings": slot_findings})
        except Exception as exc:
            msg = str(exc)
            slot_issues.append(msg)
            slot_findings.append(_finding("error", "slot_open", msg, slot=child.name))
            checked_slots.append({"name": child.name, "ok": False, "artifact_count": 0, "issues": slot_issues, "findings": slot_findings})
        findings.extend(slot_findings)
        issues.extend(f"{child.name}: {issue}" for issue in slot_issues)
    if status.get("missing_recommended"):
        msg = "recommended fixtures missing: " + ", ".join(status["missing_recommended"])
        warnings.append(msg)
        findings.append(_finding("info", "recommended_missing", msg))
    return {"fixture_root": str(root), "ok": not any(row["severity"] == "error" for row in findings), "issues": issues, "warnings": warnings, "findings": findings, "checked_slots": checked_slots, "status": status}
