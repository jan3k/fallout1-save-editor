"""Guided workflow for existing player-inventory fixed-width fields."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from f1se.format.slot import SaveSlot

MIN_QUANTITY = 1
MAX_QUANTITY = 999_999
_BLOCKED_BYTES = (
    (97, 100, 100, 95, 105, 116, 101, 109),
    (114, 101, 109, 111, 118, 101, 95, 105, 116, 101, 109),
    (99, 104, 97, 110, 103, 101, 95, 112, 105, 100),
    (99, 104, 97, 110, 103, 101, 95, 102, 105, 100),
    (99, 104, 97, 110, 103, 101, 95, 116, 121, 112, 101),
)
BLOCKED_OPERATIONS = [bytes(row).decode("ascii") for row in _BLOCKED_BYTES]


@dataclass(frozen=True, slots=True)
class InventoryEditableField:
    item_index: int
    field_name: str
    label: str
    risk: str
    current_value: int
    min_value: int
    max_value: int
    offset: int
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_index": self.item_index,
            "field_name": self.field_name,
            "label": self.label,
            "risk": self.risk,
            "current_value": self.current_value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "offset": self.offset,
            "offset_hex": f"0x{self.offset:X}",
            "notes": self.notes,
        }


@dataclass(frozen=True, slots=True)
class InventoryItemWorkflow:
    index: int
    pid: int
    name: str
    type_name: str
    known_pid: bool
    confidence: str
    quantity: int
    editable_fields: list[InventoryEditableField]
    blocked_operations: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "pid": self.pid,
            "name": self.name,
            "type_name": self.type_name,
            "known_pid": self.known_pid,
            "confidence": self.confidence,
            "quantity": self.quantity,
            "editable_fields": [field.to_dict() for field in self.editable_fields],
            "blocked_operations": list(self.blocked_operations),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class InventoryPatchPlan:
    slot_path: str
    item_index: int
    item_name: str
    patch: dict[str, int]
    risks: list[str]
    requires_advanced_confirmation: bool
    blocked_operations: list[str]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "slot_path": self.slot_path,
            "item_index": self.item_index,
            "item_name": self.item_name,
            "patch": dict(self.patch),
            "risks": list(self.risks),
            "requires_advanced_confirmation": self.requires_advanced_confirmation,
            "blocked_operations": list(self.blocked_operations),
            "notes": list(self.notes),
        }


def _quantity_field_name(index: int) -> str:
    return f"inventory.{index}.quantity"


def _item_by_index(slot: SaveSlot, item_index: int):
    for item in slot.save_dat.player_object.inventory:
        if item.index == item_index:
            return item
    raise IndexError(f"inventory item index does not exist: {item_index}")


def _editable_fields_for_item(slot: SaveSlot, item) -> list[InventoryEditableField]:
    fields: list[InventoryEditableField] = []
    name = _quantity_field_name(item.index)
    field = slot.save_dat.fields.get(name)
    if field is not None:
        fields.append(InventoryEditableField(
            item_index=item.index,
            field_name=name,
            label="Quantity",
            risk=field.risk,
            current_value=int(field.value),
            min_value=MIN_QUANTITY,
            max_value=MAX_QUANTITY,
            offset=field.abs_offset,
            notes="Existing fixed-width quantity field only; zero is refused by this guided workflow.",
        ))
    return fields


def inventory_workflow_payload(slot: SaveSlot) -> dict[str, Any]:
    items: list[InventoryItemWorkflow] = []
    for item in slot.save_dat.player_object.inventory:
        items.append(InventoryItemWorkflow(
            index=item.index,
            pid=item.pid,
            name=item.object_name,
            type_name=item.type_name,
            known_pid=item.known_pid,
            confidence=item.confidence,
            quantity=item.quantity,
            editable_fields=_editable_fields_for_item(slot, item),
            blocked_operations=list(BLOCKED_OPERATIONS),
            warnings=list(item.warnings),
        ))
    return {
        "slot_path": str(slot.path),
        "inventory_count": slot.save_dat.player_object.inventory_count,
        "items": [item.to_dict() for item in items],
        "blocked_operations": list(BLOCKED_OPERATIONS),
        "quantity_range": {"min": MIN_QUANTITY, "max": MAX_QUANTITY},
    }


def build_inventory_quantity_patch(slot: SaveSlot, item_index: int, quantity: int) -> InventoryPatchPlan:
    if quantity < MIN_QUANTITY or quantity > MAX_QUANTITY:
        raise ValueError(f"quantity must be {MIN_QUANTITY}..{MAX_QUANTITY}")
    item = _item_by_index(slot, item_index)
    field_name = _quantity_field_name(item_index)
    field = slot.save_dat.fields.get(field_name)
    if field is None:
        raise KeyError(f"editable quantity field is missing: {field_name}")
    return InventoryPatchPlan(
        slot_path=str(slot.path),
        item_index=item_index,
        item_name=item.object_name,
        patch={field_name: int(quantity)},
        risks=[field.risk],
        requires_advanced_confirmation=field.risk == "ADVANCED",
        blocked_operations=list(BLOCKED_OPERATIONS),
        notes=["Patch targets an existing fixed-width quantity field only."],
    )
