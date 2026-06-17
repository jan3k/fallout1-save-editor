from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
from typing import Iterable

F1SE_STATUSES = {"implemented", "partial", "read-only", "diagnostic", "planned", "out-of-scope"}
RISK_LEVELS = {"SAFE", "ADVANCED", "EXPERIMENTAL", "RAW", "READ_ONLY", "N/A"}
INTERFACES = {"CLI", "GUI", "MODEL", "DOCS"}


@dataclass(frozen=True, slots=True)
class FeatureStatus:
    id: str
    category: str
    name: str
    f1se_status: str
    f12se_status: str
    risk_level: str
    interface: list[str]
    source_alignment: str
    fixture_coverage: str
    notes: str

    def __post_init__(self) -> None:
        if self.f1se_status not in F1SE_STATUSES:
            raise ValueError(self.f1se_status)
        if self.risk_level not in RISK_LEVELS:
            raise ValueError(self.risk_level)
        if not set(self.interface).issubset(INTERFACES):
            raise ValueError(self.interface)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "name": self.name,
            "f1se_status": self.f1se_status,
            "f12se_status": self.f12se_status,
            "risk_level": self.risk_level,
            "interface": list(self.interface),
            "source_alignment": self.source_alignment,
            "fixture_coverage": self.fixture_coverage,
            "notes": self.notes,
        }


def _f(id: str, category: str, name: str, status: str, risk: str, interface: list[str], notes: str, fixture: str = "SLOT01") -> FeatureStatus:
    return FeatureStatus(id, category, name, status, "unknown/needs verification", risk, interface, "documented", fixture, notes)


FEATURES: tuple[FeatureStatus, ...] = (
    _f("save.metadata", "save metadata", "Header and save metadata", "implemented", "READ_ONLY", ["CLI", "GUI", "MODEL"], "Header strings are visible."),
    _f("player.status", "player stats", "Player status fields", "implemented", "SAFE", ["CLI", "GUI", "MODEL"], "Fixed-width local fields."),
    _f("special.base", "SPECIAL", "Base SPECIAL", "implemented", "SAFE", ["CLI", "GUI", "MODEL"], "Validated i32 fields."),
    _f("derived.stats", "derived stats", "Derived stats", "partial", "ADVANCED", ["CLI", "GUI", "MODEL"], "Lower-level values."),
    _f("skills.points", "skills", "Skill values", "implemented", "SAFE", ["CLI", "GUI", "MODEL"], "Saved skill data."),
    _f("skills.tags", "tag skills", "Tagged skills", "implemented", "SAFE", ["CLI", "GUI", "MODEL"], "Validated ids."),
    _f("traits.selected", "traits", "Traits", "implemented", "SAFE", ["CLI", "GUI", "MODEL"], "Selected trait ids."),
    _f("perks.ranks", "perks", "Perk ranks", "partial", "ADVANCED", ["CLI", "GUI", "MODEL"], "Rank data only."),
    _f("kills.counts", "kills", "Kill counters", "implemented", "SAFE", ["CLI", "GUI", "MODEL"], "Counter fields."),
    _f("inventory.existing", "inventory", "Existing inventory values", "implemented", "SAFE", ["CLI", "GUI", "MODEL"], "Existing fixed-width fields."),
    _f("inventory.structure", "inventory", "Inventory structure operations", "planned", "EXPERIMENTAL", ["DOCS"], "Needs more fixtures.", "none"),
    _f("items.metadata", "item metadata", "Item metadata", "read-only", "READ_ONLY", ["CLI", "GUI", "MODEL", "DOCS"], "Display and confidence data."),
    _f("raw.access", "raw read/write", "Raw access", "implemented", "RAW", ["CLI", "GUI", "MODEL"], "Explicit raw workflow."),
    _f("artifacts.inspect", "artifacts", "Slot artifacts", "read-only", "READ_ONLY", ["CLI", "GUI", "MODEL", "DOCS"], "Fingerprint data."),
    _f("map.sav.scan", "map .SAV", "Map scan", "diagnostic", "READ_ONLY", ["CLI", "GUI", "MODEL", "DOCS"], "Candidate scan only."),
    _f("automap.inspect", "automap", "Automap fingerprint", "read-only", "READ_ONLY", ["CLI", "GUI", "MODEL", "DOCS"], "Artifact inspection."),
    _f("raw.blocks", "raw blocks", "Raw block inspection", "diagnostic", "READ_ONLY", ["CLI", "GUI", "MODEL", "DOCS"], "Structural hints."),
    _f("global.scan", "global/script state", "Global/script scan", "diagnostic", "READ_ONLY", ["CLI", "GUI", "MODEL", "DOCS"], "Candidate scan."),
    _f("quest.state", "quest state", "Quest state", "planned", "EXPERIMENTAL", ["DOCS"], "Needs naming and fixtures.", "none"),
    _f("worldmap.state", "worldmap", "Worldmap state", "diagnostic", "READ_ONLY", ["CLI", "GUI", "MODEL", "DOCS"], "Raw diagnostics."),
    _f("party.state", "party", "Party state", "planned", "EXPERIMENTAL", ["DOCS"], "Future parser area.", "none"),
    _f("map.objects", "map objects", "Map object candidates", "diagnostic", "READ_ONLY", ["CLI", "GUI", "MODEL", "DOCS"], "Candidate scan."),
    _f("containers.map", "containers", "Container data", "planned", "EXPERIMENTAL", ["DOCS"], "Needs map object layout.", "none"),
    _f("gui.safety", "GUI safety workflow", "Guided GUI safety", "implemented", "N/A", ["GUI", "MODEL", "DOCS"], "Risk labels and acknowledgement."),
    _f("backup.slot", "backups", "Slot backups", "implemented", "N/A", ["CLI", "GUI", "MODEL"], "Backup path."),
    _f("write.atomic", "atomic write", "Atomic SAVE.DAT replace", "implemented", "N/A", ["CLI", "GUI", "MODEL"], "Atomic file operation."),
    _f("fixtures.matrix", "fixture matrix", "Fixture matrix", "implemented", "N/A", ["CLI", "MODEL", "DOCS"], "Regression corpus."),
    _f("fixtures.import_workflow", "fixture matrix", "Guided fixture import workflow", "implemented", "N/A", ["CLI", "MODEL", "DOCS"], "Dry-run and import for real save slots."),
    _f("source.alignment", "source alignment", "Source-aligned registry", "implemented", "N/A", ["MODEL", "DOCS"], "Handler block order."),
    _f("validation.verify", "validation", "Validation", "implemented", "N/A", ["CLI", "GUI", "MODEL"], "Structural checks."),
)

RECOMMENDED_NEXT_MILESTONES = [
    "v0.12.0 - real fixture corpus expansion and guided import workflow",
    "v0.13.0 - safer existing-inventory UX and item quantity workflows",
    "v0.14.0 - read-only quest/global naming groundwork",
    "v0.15.0 - map object deep scan",
    "v1.0.0 - stable safe editor",
]


def filter_features(*, category: str | None = None, status: str | None = None) -> list[FeatureStatus]:
    rows: Iterable[FeatureStatus] = FEATURES
    if category:
        rows = [row for row in rows if row.category.lower() == category.lower()]
    if status:
        rows = [row for row in rows if row.f1se_status.lower() == status.lower()]
    return list(rows)


def feature_counts_by_status(features: Iterable[FeatureStatus] = FEATURES) -> dict[str, int]:
    return dict(Counter(row.f1se_status for row in features))


def feature_counts_by_risk(features: Iterable[FeatureStatus] = FEATURES) -> dict[str, int]:
    return dict(Counter(row.risk_level for row in features))


def feature_matrix_payload() -> dict:
    return {
        "features": [row.to_dict() for row in FEATURES],
        "counts_by_status": feature_counts_by_status(),
        "counts_by_risk": feature_counts_by_risk(),
        "recommended_next_milestones": list(RECOMMENDED_NEXT_MILESTONES),
    }
