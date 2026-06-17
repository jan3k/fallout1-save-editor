"""Read-only labels for global/script-state diagnostic regions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

VALID_CONFIDENCES = {"high", "medium", "low", "hypothesis", "unknown"}


@dataclass(frozen=True, slots=True)
class GlobalLabel:
    id: str
    block_index: int
    block_name: str
    label: str
    description: str
    confidence: str
    source: str
    notes: str

    def __post_init__(self) -> None:
        if self.confidence not in VALID_CONFIDENCES:
            raise ValueError(f"invalid confidence: {self.confidence}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "block_index": self.block_index,
            "block_name": self.block_name,
            "label": self.label,
            "description": self.description,
            "confidence": self.confidence,
            "source": self.source,
            "notes": self.notes,
        }


GLOBAL_LABELS: tuple[GlobalLabel, ...] = (
    GlobalLabel(
        id="block2.script_state_region",
        block_index=2,
        block_name="scripts_game_save_1",
        label="script_state_region",
        description="Primary source-order script/game-state area before the player object.",
        confidence="low",
        source="fallout1-ce load/save handler order plus fixture block layout",
        notes="Diagnostic region label only; values are not named variables.",
    ),
    GlobalLabel(
        id="block4.script_state_region_secondary",
        block_index=4,
        block_name="scripts_game_save_2",
        label="script_state_region_secondary",
        description="Secondary source-order script/game-state area before the player object.",
        confidence="low",
        source="fallout1-ce load/save handler order plus fixture block layout",
        notes="Diagnostic region label only; split is coarse and preserved byte-for-byte.",
    ),
    GlobalLabel(
        id="block20.world_or_late_state_region",
        block_index=20,
        block_name="worldmap",
        label="world_or_late_state_region",
        description="Late game-state area currently associated with the worldmap save handler range.",
        confidence="low",
        source="source-order handler registry and SLOT01 fixture anchors",
        notes="May contain mixed late-state payload; no semantic field names are assigned.",
    ),
)


def global_labels(block_index: int | None = None) -> list[GlobalLabel]:
    if block_index is None:
        return list(GLOBAL_LABELS)
    return [label for label in GLOBAL_LABELS if label.block_index == block_index]


def labels_by_block(block_index: int) -> list[dict[str, Any]]:
    return [label.to_dict() for label in global_labels(block_index)]


def global_labels_payload(block_index: int | None = None) -> dict[str, Any]:
    labels = global_labels(block_index)
    return {
        "labels": [label.to_dict() for label in labels],
        "count": len(labels),
        "block_index": block_index,
        "read_only": True,
        "confidence_values": sorted(VALID_CONFIDENCES),
    }
