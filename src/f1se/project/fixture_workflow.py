"""Guided real-save fixture import workflow."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import shutil
from typing import Any

from f1se.format.slot import SaveSlot

IGNORED_SUFFIXES = {".bak", ".tmp"}
IGNORED_NAMES = {".f1se-backups", "__pycache__"}

RECOMMENDED_FIXTURES: tuple[dict[str, str], ...] = (
    {"name": "SLOT01_BASELINE", "goal": "baseline parser regression", "requirements": "basic vault or early-game save", "coverage": "header, Function 5/6, small inventory", "source": "real save"},
    {"name": "SLOT02_AFTER_COMBAT", "goal": "post-combat state", "requirements": "recent combat with changed HP/kills", "coverage": "HP, kills, combat/raw blocks", "source": "real save"},
    {"name": "SLOT03_BIG_INVENTORY", "goal": "large player inventory", "requirements": "many item types and ammo/drugs", "coverage": "inventory size inference", "source": "real save"},
    {"name": "SLOT04_WITH_PERKS", "goal": "perk rank coverage", "requirements": "leveled character with perks", "coverage": "perk raw ranks", "source": "real save"},
    {"name": "SLOT05_POISON_RAD_CRIPPLED", "goal": "status effects", "requirements": "poison/radiation/crippled bits", "coverage": "player status fields", "source": "real save"},
    {"name": "SLOT06_WORLD_MAP_TRAVEL", "goal": "world map state", "requirements": "save after world map travel", "coverage": "late raw worldstate", "source": "real save"},
    {"name": "SLOT07_MAP_TRANSITION", "goal": "map transition state", "requirements": "different current map/elevation", "coverage": "header map and map artifacts", "source": "real save"},
    {"name": "SLOT08_WITH_COMPANION", "goal": "party/companion coverage", "requirements": "save with companion", "coverage": "party/raw late blocks", "source": "real save"},
    {"name": "SLOT09_LATE_GAME", "goal": "late game state", "requirements": "high level and broad quest state", "coverage": "many raw/global regions", "source": "real save"},
    {"name": "SLOT10_CORRUPTION_NEGATIVE", "goal": "negative validation", "requirements": "temporary mutation of a real fixture", "coverage": "verify rejection paths", "source": "synthetic negative mutation"},
)


@dataclass(slots=True)
class FixtureImportPlan:
    source: Path
    fixture_root: Path
    name: str
    destination: Path
    manifest_entry: dict[str, Any]
    files: list[str]
    verify_issues: list[str]
    issues: list[str]

    @property
    def ok(self) -> bool:
        return not self.issues and not self.verify_issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": str(self.source),
            "fixture_root": str(self.fixture_root),
            "name": self.name,
            "destination": str(self.destination),
            "manifest_entry": self.manifest_entry,
            "files": list(self.files),
            "verify_issues": list(self.verify_issues),
            "issues": list(self.issues),
            "ok": self.ok,
        }


def _hex(value: int) -> str:
    return f"0x{value:X}"


def _copyable_files(slot_path: Path) -> list[Path]:
    files: list[Path] = []
    for child in sorted(slot_path.iterdir(), key=lambda p: p.name.lower()):
        if child.name in IGNORED_NAMES or child.is_dir():
            continue
        if child.suffix.lower() in IGNORED_SUFFIXES:
            continue
        if child.name.upper() == "SAVE.DAT" or child.name.upper() == "AUTOMAP.SAV" or child.suffix.upper() == ".SAV":
            files.append(child)
    return files


def build_manifest_entry(slot: SaveSlot, description: str = "Imported real Fallout 1 save fixture") -> dict[str, Any]:
    sd = slot.save_dat
    return {
        "description": description,
        "save_dat_size": len(sd.data),
        "version": sd.header.version,
        "player_name": sd.header.player_name,
        "current_map_file": sd.header.current_map_file,
        "function5_start": _hex(sd.player_object.start),
        "function6_start": _hex(sd.critter_stats.start),
        "inventory_count": sd.player_object.inventory_count,
        "kill_count_count": sd.kill_count_count,
        "expected_artifacts": [artifact.name for artifact in slot.artifacts],
        "expected_artifact_kinds": {artifact.name: artifact.kind for artifact in slot.artifacts},
    }


def fixture_import_plan(source: str | Path, fixture_root: str | Path, name: str, *, force: bool = False, description: str = "Imported real Fallout 1 save fixture") -> FixtureImportPlan:
    slot = SaveSlot.open(source)
    src_slot = slot.path
    root = Path(fixture_root)
    dest = root / name
    issues: list[str] = []
    if dest.exists() and not force:
        issues.append("destination fixture already exists; use --force to replace it")
    files = _copyable_files(src_slot)
    names = {file.name.upper() for file in files}
    if "SAVE.DAT" not in names:
        issues.append("SAVE.DAT is not in copy plan")
    verify_issues = slot.save_dat.verify()
    entry = build_manifest_entry(slot, description=description)
    return FixtureImportPlan(src_slot, root, name, dest, entry, [file.name for file in files], verify_issues, issues)


def write_fixture_import(plan: FixtureImportPlan, *, force: bool = False) -> None:
    if plan.issues and not force:
        raise ValueError("cannot write fixture import with unresolved issues")
    if plan.verify_issues:
        raise ValueError("cannot import fixture with verify issues")
    plan.fixture_root.mkdir(parents=True, exist_ok=True)
    if plan.destination.exists():
        if not force:
            raise FileExistsError(plan.destination)
        shutil.rmtree(plan.destination)
    plan.destination.mkdir(parents=True)
    for file_name in plan.files:
        shutil.copy2(plan.source / file_name, plan.destination / file_name)
    manifest_path = plan.fixture_root / "fixtures.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    if plan.name in manifest and not force:
        raise ValueError("manifest entry already exists; use --force")
    manifest[plan.name] = plan.manifest_entry
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def recommended_fixture_plan() -> list[dict[str, str]]:
    return [dict(row) for row in RECOMMENDED_FIXTURES]


def fixture_status(fixture_root: str | Path) -> dict[str, Any]:
    root = Path(fixture_root)
    manifest_path = root / "fixtures.json"
    if not manifest_path.exists():
        return {"fixture_root": str(root), "ok": False, "issues": ["fixtures.json missing"], "manifest_count": 0}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    present = set(manifest)
    recommended = [row["name"] for row in RECOMMENDED_FIXTURES]
    equivalent_present = set(present)
    if "SLOT01" in present:
        equivalent_present.add("SLOT01_BASELINE")
    present_recommended = [name for name in recommended if name in equivalent_present]
    missing_recommended = [name for name in recommended if name not in equivalent_present]
    categories: set[str] = {"baseline"} if "SLOT01" in present or "SLOT01_BASELINE" in present else set()
    for name in present:
        low = name.lower()
        for marker, category in [("combat", "combat"), ("inventory", "inventory"), ("perk", "perks"), ("poison", "status_effects"), ("rad", "status_effects"), ("crippled", "status_effects"), ("world", "worldmap"), ("transition", "map_transition"), ("companion", "party"), ("late", "late_game"), ("corruption", "negative"), ("negative", "negative")]:
            if marker in low:
                categories.add(category)
    issues = [f"{name}: SAVE.DAT missing" for name in present if not (root / name / "SAVE.DAT").is_file()]
    score = round(len(present_recommended) / len(recommended), 3) if recommended else 1.0
    return {
        "fixture_root": str(root),
        "ok": not issues,
        "issues": issues,
        "manifest_count": len(manifest),
        "present": sorted(present),
        "recommended": recommended,
        "present_recommended": present_recommended,
        "missing_recommended": missing_recommended,
        "coverage_categories": sorted(categories),
        "coverage_score": score,
    }
