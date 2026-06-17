"""Feature parity and roadmap metadata for f1se.

The matrix is intentionally conservative. F12se entries are coarse capability
notes, not reverse-engineered claims about its internal implementation.
"""
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
            raise ValueError(f"invalid f1se_status for {self.id}: {self.f1se_status}")
        if self.risk_level not in RISK_LEVELS:
            raise ValueError(f"invalid risk_level for {self.id}: {self.risk_level}")
        unknown = set(self.interface) - INTERFACES
        if unknown:
            raise ValueError(f"invalid interface for {self.id}: {sorted(unknown)}")

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


def _f(id: str, category: str, name: str, status: str, f12se: str, risk: str, interface: list[str], source: str, fixture: str, notes: str) -> FeatureStatus:
    return FeatureStatus(id, category, name, status, f12se, risk, interface, source, fixture, notes)


FEATURES: tuple[FeatureStatus, ...] = (
    _f("save.metadata", "save metadata", "Header and save metadata", "implemented", "present in F12se scope; exact behavior needs verification", "READ_ONLY", ["CLI", "GUI", "MODEL"], "SAVE.DAT header parser", "SLOT01", "Header strings are currently read-only to avoid C-string size mistakes."),
    _f("player.status", "player stats", "Player HP/radiation/poison/status", "implemented", "present in F12se scope; exact behavior needs verification", "SAFE", ["CLI", "GUI", "MODEL"], "Function 5 player object", "SLOT01", "Fixed-width local edits with validators."),
    _f("special.base", "SPECIAL", "Base S.P.E.C.I.A.L.", "implemented", "present in F12se scope; exact behavior needs verification", "SAFE", ["CLI", "GUI", "MODEL"], "Function 6 critter stats", "SLOT01", "Big-endian i32 fields with conservative limits."),
    _f("derived.stats", "derived stats", "Derived/stat bonus fields", "partial", "present in F12se scope; exact behavior needs verification", "ADVANCED", ["CLI", "GUI", "MODEL"], "Function 6 critter stats", "SLOT01", "Some values can have engine-side recalculation effects."),
    _f("skills.points", "skills", "Skill point over-base values", "implemented", "present in F12se scope; exact behavior needs verification", "SAFE", ["CLI", "GUI", "MODEL"], "Function 6 skill array", "SLOT01", "Saved over-base values, not full derived skill emulation."),
    _f("skills.tags", "tag skills", "Tagged skill ids", "implemented", "present in F12se scope; exact behavior needs verification", "SAFE", ["CLI", "GUI", "MODEL"], "Function 8 tag skills", "SLOT01", "Validated ids and duplicate checks."),
    _f("traits.selected", "traits", "Selected traits", "implemented", "present in F12se scope; exact behavior needs verification", "SAFE", ["CLI", "GUI", "MODEL"], "Function 16 traits", "SLOT01", "Trait side effects are exposed as notes/preview, not blindly applied."),
    _f("perks.ranks", "perks", "Perk ranks", "partial", "present in F12se scope; exact behavior needs verification", "ADVANCED", ["CLI", "GUI", "MODEL"], "Function 10 perk rank array", "SLOT01", "Raw rank editing only; full engine side effects are not emulated."),
    _f("kills.counts", "kills", "Kill counters", "implemented", "present in F12se scope; exact behavior needs verification", "SAFE", ["CLI", "GUI", "MODEL"], "Function 7 kill counters", "SLOT01", "Labels are stable source-order indices to avoid localization guesses."),
    _f("inventory.existing", "inventory", "Existing player inventory quantities/ammo", "implemented", "present in F12se scope; exact behavior needs verification", "SAFE", ["CLI", "GUI", "MODEL"], "Function 5 object inventory", "SLOT01", "Only existing fixed-width fields are writable."),
    _f("inventory.structure", "inventory", "Add/remove/change item identity", "planned", "present in F12se scope; exact behavior needs verification", "EXPERIMENTAL", ["DOCS"], "not source-aligned enough", "none", "Deliberately blocked until object serialization is fully mapped and fixture-covered."),
    _f("items.metadata", "item metadata", "Read-only item/proto metadata", "read-only", "unknown/needs verification", "READ_ONLY", ["CLI", "GUI", "MODEL", "DOCS"], "curated proto constants and fixture observations", "SLOT01", "Improves display and inference; does not authorize PID/FID/type mutation."),
    _f("raw.access", "raw read/write", "Explicit raw read/write", "implemented", "unknown/needs verification", "RAW", ["CLI", "GUI", "MODEL"], "byte offset access", "SLOT01", "Writes require explicit experimental gate."),
    _f("artifacts.inspect", "artifacts", "Slot artifacts", "read-only", "unknown/needs verification", "READ_ONLY", ["CLI", "GUI", "MODEL", "DOCS"], "slot file fingerprinting", "SLOT01", "AUTOMAP.SAV and map .SAV are classified and fingerprinted."),
    _f("map.sav.scan", "map .SAV", "Map .SAV scan", "diagnostic", "present in F12se scope; exact behavior needs verification", "READ_ONLY", ["CLI", "GUI", "MODEL", "DOCS"], "heuristic read-only scan", "SLOT01", "Candidates are not semantic truth and do not enable writes."),
    _f("automap.inspect", "automap", "AUTOMAP.SAV fingerprint", "read-only", "unknown/needs verification", "READ_ONLY", ["CLI", "GUI", "MODEL", "DOCS"], "raw fingerprint", "SLOT01", "No reveal/clear writes."),
    _f("raw.blocks", "raw blocks", "Raw block inspection", "diagnostic", "not known; needs verification", "READ_ONLY", ["CLI", "GUI", "MODEL", "DOCS"], "FunctionBlock registry", "SLOT01", "Structural hints only; no quest/global naming."),
    _f("global.scan", "global/script state", "Global/script candidate scan", "diagnostic", "present in F12se scope; exact behavior needs verification", "READ_ONLY", ["CLI", "GUI", "MODEL", "DOCS"], "raw Function 2/4/20 diagnostics", "SLOT01", "No semantic writes and no named quest claims."),
    _f("quest.state", "quest state", "Quest state editing", "planned", "present in F12se scope; exact behavior needs verification", "EXPERIMENTAL", ["DOCS"], "not mapped", "none", "Requires source-aligned names and fixture corpus before writes."),
    _f("worldmap.state", "worldmap", "Worldmap state", "diagnostic", "present in F12se scope; exact behavior needs verification", "READ_ONLY", ["CLI", "GUI", "MODEL", "DOCS"], "late raw Function 20", "SLOT01", "Currently raw/diagnostic only."),
    _f("party.state", "party", "Party/companion state", "planned", "present in F12se scope; exact behavior needs verification", "EXPERIMENTAL", ["DOCS"], "late raw blocks", "none", "No semantic parser yet."),
    _f("map.objects", "map objects", "Map object candidates", "diagnostic", "present in F12se scope; exact behavior needs verification", "READ_ONLY", ["CLI", "GUI", "MODEL", "DOCS"], "heuristic .SAV scan", "SLOT01", "Candidate discovery only."),
    _f("containers.map", "containers", "Map/container inventory", "planned", "present in F12se scope; exact behavior needs verification", "EXPERIMENTAL", ["DOCS"], "not safely mapped", "none", "No item transfer/container edits until map object layout is proven."),
    _f("gui.safety", "GUI safety workflow", "Guided GUI safety workflow", "implemented", "F12se has GUI; exact safety model needs verification", "N/A", ["GUI", "MODEL", "DOCS"], "model facade", "GUI model tests", "Risk labels, dirty state, preview diff and advanced acknowledgement."),
    _f("backup.slot", "backups", "Slot backup before write", "implemented", "unknown/needs verification", "N/A", ["CLI", "GUI", "MODEL"], "backup module", "tests", "Backup created before write paths."),
    _f("write.atomic", "atomic write", "Atomic SAVE.DAT replacement", "implemented", "unknown/needs verification", "N/A", ["CLI", "GUI", "MODEL"], "atomic write module", "tests", "Temp file + fsync + rename."),
    _f("fixtures.matrix", "fixture matrix", "Real save fixture matrix", "implemented", "not known; needs verification", "N/A", ["CLI", "MODEL", "DOCS"], "fixtures.json", "SLOT01", "Currently too small; next milestone should expand corpus."),
    _f("source.alignment", "source alignment", "Source-aligned handler registry", "implemented", "not known; needs verification", "N/A", ["MODEL", "DOCS"], "fallout1-ce load/save handlers", "tests", "Separates known semantic blocks from raw-preserved blocks."),
    _f("validation.verify", "validation", "Structural verification", "implemented", "unknown/needs verification", "N/A", ["CLI", "GUI", "MODEL"], "SaveDat.verify", "negative tests", "Checks structure, anchors, duplicates, options and round-trip invariants."),
)

RECOMMENDED_NEXT_MILESTONES = [
    "v0.12.0 - real fixture corpus expansion and guided import workflow",
    "v0.13.0 - safer inventory UX for existing-item operations",
    "v0.14.0 - read-only quest/global naming groundwork",
    "v0.15.0 - map object deep scan",
    "v1.0.0 - stable safe editor",
]


def filter_features(*, category: str | None = None, status: str | None = None) -> list[FeatureStatus]:
    rows: Iterable[FeatureStatus] = FEATURES
    if category:
        c = category.lower()
        rows = [row for row in rows if row.category.lower() == c]
    if status:
        s = status.lower()
        rows = [row for row in rows if row.f1se_status.lower() == s]
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
