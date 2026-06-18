from __future__ import annotations

from pathlib import Path
from typing import Any

from f1se.project.fixture_workflow import fixture_status, recommended_fixture_plan

CATEGORY_TARGETS: tuple[str, ...] = (
    "baseline",
    "combat",
    "inventory",
    "perks",
    "status_effects",
    "worldmap",
    "map_transition",
    "party",
    "late_game",
    "negative",
    "fallout1.baseline",
    "fallout2.baseline",
    "fallout2.inventory",
    "fallout2.perks",
    "fallout2.status_effects",
    "fallout2.late_game",
    "fallout2.negative",
)


def _equivalent_present(name: str, present: set[str]) -> bool:
    if name == "SLOT01_BASELINE" and "SLOT01" in present:
        return True
    return name in present


def _priority(row: dict[str, str]) -> str:
    name = row["name"]
    if name in {"SLOT01_BASELINE", "SLOT03_BIG_INVENTORY", "SLOT04_WITH_PERKS"}:
        return "high"
    if name in {"SLOT02_AFTER_COMBAT", "SLOT05_POISON_RAD_CRIPPLED", "SLOT06_WORLD_MAP_TRAVEL", "SLOT07_MAP_TRANSITION"}:
        return "medium"
    return "low"


def fixture_coverage(fixture_root: str | Path) -> dict[str, Any]:
    status = fixture_status(fixture_root)
    present = set(status.get("present", []))
    categories = set(status.get("coverage_categories", []))
    if "baseline" in categories:
        categories.add("fallout1.baseline")
    for name in present:
        low = name.lower()
        if "fallout2" in low or low.startswith("fo2") or low.startswith("f2"):
            if "baseline" in low or "base" in low:
                categories.add("fallout2.baseline")
            if "inventory" in low:
                categories.add("fallout2.inventory")
            if "perk" in low:
                categories.add("fallout2.perks")
            if "poison" in low or "rad" in low or "crippled" in low or "status" in low:
                categories.add("fallout2.status_effects")
            if "late" in low:
                categories.add("fallout2.late_game")
            if "negative" in low or "corrupt" in low:
                categories.add("fallout2.negative")
    recommended = recommended_fixture_plan()
    rows: list[dict[str, Any]] = []
    expansion_plan: list[dict[str, Any]] = []
    for row in recommended:
        present_flag = _equivalent_present(row["name"], present)
        item = dict(row)
        item["present"] = present_flag
        item["priority"] = _priority(row)
        rows.append(item)
        if not present_flag:
            expansion_plan.append(item)
    missing_categories = [category for category in CATEGORY_TARGETS if category not in categories]
    return {
        "fixture_root": str(Path(fixture_root)),
        "status": status,
        "recommended": rows,
        "expansion_plan": expansion_plan,
        "coverage_categories": sorted(categories),
        "missing_categories": missing_categories,
        "summary": {
            "present_count": len(present),
            "recommended_count": len(recommended),
            "missing_recommended_count": len(expansion_plan),
            "coverage_score": status.get("coverage_score", 0),
            "missing_category_count": len(missing_categories),
        },
        "read_only": True,
    }
