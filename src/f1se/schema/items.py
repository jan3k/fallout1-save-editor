"""Read-only Fallout 1 item/proto metadata.

This module intentionally describes existing item/proto ids; it does not make
PID, FID, object type, or inventory structure edits safe.  High-level inventory
mutation remains out of scope because changing object identity or list length can
invalidate surrounding save structure.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ItemProtoMeta:
    pid: int
    name: str
    type_name: str
    save_size: int
    source: str = "curated"
    notes: str = ""

    def to_dict(self) -> dict[str, int | str]:
        return {
            "pid": self.pid,
            "name": self.name,
            "type": self.type_name,
            "save_size": self.save_size,
            "save_size_hex": f"0x{self.save_size:X}",
            "source": self.source,
            "notes": self.notes,
        }


ITEM_TYPE_SIZES = {
    "weapon": 0x64,
    "ammo": 0x60,
    "armor": 0x5C,
    "drug": 0x5C,
    "misc": 0x60,
    "key": 0x5C,
    "container": 0x5C,
    "unknown": 0x5C,
}


def _meta(pid: int, name: str, type_name: str, source: str, notes: str = "") -> ItemProtoMeta:
    return ItemProtoMeta(
        pid=pid,
        name=name,
        type_name=type_name,
        save_size=ITEM_TYPE_SIZES[type_name],
        source=source,
        notes=notes,
    )


_F1CE_PROTO_TYPES = "fallout1-ce src/game/proto_types.h"
_F1SE_FIXTURE = "f1se curated from SLOT01 fixture"

ITEM_PROTO_META: dict[int, ItemProtoMeta] = {
    3: _meta(3, "Power Armor", "armor", _F1CE_PROTO_TYPES, "PROTO_ID_POWER_ARMOR"),
    4: _meta(4, "Knife", "weapon", _F1SE_FIXTURE),
    8: _meta(8, "10mm Pistol", "weapon", _F1SE_FIXTURE),
    29: _meta(29, "10mm JHP", "ammo", _F1SE_FIXTURE),
    30: _meta(30, "10mm AP", "ammo", _F1SE_FIXTURE),
    38: _meta(38, "Small Energy Cell", "ammo", _F1CE_PROTO_TYPES, "PROTO_ID_SMALL_ENERGY_CELL"),
    39: _meta(39, "Micro Fusion Cell", "ammo", _F1CE_PROTO_TYPES, "PROTO_ID_MICRO_FUSION_CELL"),
    40: _meta(40, "Stimpak", "drug", _F1CE_PROTO_TYPES, "PROTO_ID_STIMPACK"),
    41: _meta(41, "Money", "misc", _F1CE_PROTO_TYPES, "PROTO_ID_MONEY"),
    47: _meta(47, "First Aid Kit", "misc", _F1CE_PROTO_TYPES, "PROTO_ID_FIRST_AID_KIT"),
    48: _meta(48, "RadAway", "drug", _F1CE_PROTO_TYPES, "PROTO_ID_RADAWAY"),
    51: _meta(51, "Dynamite", "misc", _F1CE_PROTO_TYPES, "PROTO_ID_DYNAMITE_I"),
    52: _meta(52, "Geiger Counter", "misc", _F1CE_PROTO_TYPES, "PROTO_ID_GEIGER_COUNTER_I"),
    53: _meta(53, "Mentats", "drug", _F1CE_PROTO_TYPES, "PROTO_ID_MENTATS"),
    54: _meta(54, "Stealth Boy", "misc", _F1CE_PROTO_TYPES, "PROTO_ID_STEALTH_BOY_I"),
    59: _meta(59, "Motion Sensor", "misc", _F1CE_PROTO_TYPES, "PROTO_ID_MOTION_SENSOR"),
    73: _meta(73, "Big Book of Science", "misc", _F1CE_PROTO_TYPES, "PROTO_ID_BIG_BOOK_OF_SCIENCE"),
    76: _meta(76, "Dean's Electronics", "misc", _F1CE_PROTO_TYPES, "PROTO_ID_DEANS_ELECTRONICS"),
    79: _meta(79, "Flare", "weapon", _F1CE_PROTO_TYPES, "PROTO_ID_FLARE"),
    80: _meta(80, "First Aid Book", "misc", _F1CE_PROTO_TYPES, "PROTO_ID_FIRST_AID_BOOK"),
    85: _meta(85, "Plastic Explosives", "misc", _F1CE_PROTO_TYPES, "PROTO_ID_PLASTIC_EXPLOSIVES_I"),
    86: _meta(86, "Scout Handbook", "misc", _F1CE_PROTO_TYPES, "PROTO_ID_SCOUT_HANDBOOK"),
    87: _meta(87, "Buffout", "drug", _F1CE_PROTO_TYPES, "PROTO_ID_BUFF_OUT"),
    91: _meta(91, "Doctor's Bag", "misc", _F1CE_PROTO_TYPES, "PROTO_ID_DOCTORS_BAG"),
    102: _meta(102, "Guns and Bullets", "misc", _F1CE_PROTO_TYPES, "PROTO_ID_GUNS_AND_BULLETS"),
    106: _meta(106, "Nuka-Cola", "drug", _F1CE_PROTO_TYPES, "PROTO_ID_NUKA_COLA"),
    110: _meta(110, "Psycho", "drug", _F1CE_PROTO_TYPES, "PROTO_ID_PSYCHO"),
    144: _meta(144, "Super Stimpak", "drug", _F1CE_PROTO_TYPES, "PROTO_ID_SUPER_STIMPACK"),
    159: _meta(159, "Molotov Cocktail", "weapon", _F1CE_PROTO_TYPES, "PROTO_ID_MOLOTOV_COCKTAIL"),
    205: _meta(205, "Lit Flare", "weapon", _F1CE_PROTO_TYPES, "PROTO_ID_LIT_FLARE"),
    206: _meta(206, "Dynamite (armed)", "misc", _F1CE_PROTO_TYPES, "PROTO_ID_DYNAMITE_II"),
    207: _meta(207, "Geiger Counter", "misc", _F1CE_PROTO_TYPES, "PROTO_ID_GEIGER_COUNTER_II"),
    209: _meta(209, "Plastic Explosives (armed)", "misc", _F1CE_PROTO_TYPES, "PROTO_ID_PLASTIC_EXPLOSIVES_II"),
    210: _meta(210, "Stealth Boy", "misc", _F1CE_PROTO_TYPES, "PROTO_ID_STEALTH_BOY_II"),
    232: _meta(232, "Hardened Power Armor", "armor", _F1CE_PROTO_TYPES, "PROTO_ID_HARDENED_POWER_ARMOR"),
}

# Compatibility alias used by older parser code/tests: pid -> (name, type, save_size).
ITEM_PID_NAMES: dict[int, tuple[str, str, int]] = {
    pid: (meta.name, meta.type_name, meta.save_size)
    for pid, meta in ITEM_PROTO_META.items()
}


def get_item_meta(pid: int) -> ItemProtoMeta | None:
    return ITEM_PROTO_META.get(pid)


def item_size_options(pid: int) -> list[int]:
    meta = get_item_meta(pid)
    if meta is not None:
        return [meta.save_size]
    # Fallout object payload is type-dependent. These are the common terminal
    # sizes encountered in Fallout 1/Fallout 2 object serialization.
    return [ITEM_TYPE_SIZES["weapon"], ITEM_TYPE_SIZES["ammo"], ITEM_TYPE_SIZES["armor"]]
