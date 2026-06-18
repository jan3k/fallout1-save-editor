"""Read-only Fallout 2 SAVE.DAT parser skeleton.

This module deliberately exposes Fallout 2 data as read-only. It reuses the
existing low-level Fallout 1 helpers only where the underlying Interplay save
serialization is shared, and annotates every Fallout 2 field with confidence and
risk metadata before any write support exists.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import hashlib
from typing import Any

from f1se.format.function_5_player_object import FP_SIGNATURE, PlayerObject, find_function5
from f1se.format.function_6_critter_stats import FUNCTION6_SIZE, SKILLS_REL_OFFSET, parse_function6
from f1se.format.header import HEADER_SIZE, SAVE_SIGNATURE, SaveHeader, parse_header
from f1se.format.inventory import ParsedInventoryItem
from f1se.io.endian import c_string, i32be
from f1se.schema.enums import KILL_COUNT_NAMES, PERK_NAMES, SKILL_NAMES, SPECIAL_NAMES

FUNCTION7_KILL_COUNT_SIZE = 0x4C
FUNCTION7_KILL_COUNT_COUNT = FUNCTION7_KILL_COUNT_SIZE // 4
FUNCTION8_TAG_SKILL_SIZE = 0x10
FUNCTION9_PERK_SIZE = 0x02C8
FUNCTION9_PERK_COUNT = FUNCTION9_PERK_SIZE // 4
FUNCTION13_PC_STATS_SIZE = 0x14
FUNCTION15_TRAITS_SIZE = 0x08


@dataclass(frozen=True, slots=True)
class Fallout2Section:
    name: str
    start: int
    end: int
    confidence: str
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "start": self.start,
            "start_hex": f"0x{self.start:X}",
            "end": self.end,
            "end_hex": f"0x{self.end:X}",
            "size": self.end - self.start,
            "size_hex": f"0x{self.end - self.start:X}",
            "confidence": self.confidence,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class Fallout2Field:
    name: str
    block: str
    abs_offset: int
    rel_offset: int
    size: int
    endian: str
    type_name: str
    value: int | str
    risk: str
    confidence: str
    writable: bool = False
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "file": "SAVE.DAT",
            "block": self.block,
            "abs_offset": self.abs_offset,
            "abs_offset_hex": f"0x{self.abs_offset:X}",
            "rel_offset": self.rel_offset,
            "rel_offset_hex": f"0x{self.rel_offset:X}",
            "size": self.size,
            "endian": self.endian,
            "type": self.type_name,
            "value": self.value,
            "risk": self.risk,
            "confidence": self.confidence,
            "writable": self.writable,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class Fallout2InventoryItem:
    index: int
    start: int
    end: int
    quantity: int
    pid: int
    confidence: str
    warnings: tuple[str, ...] = ()
    raw_fields: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "start": self.start,
            "start_hex": f"0x{self.start:X}",
            "end": self.end,
            "end_hex": f"0x{self.end:X}",
            "size": self.end - self.start,
            "size_hex": f"0x{self.end - self.start:X}",
            "quantity": self.quantity,
            "pid": self.pid,
            "raw_object_offset": self.start,
            "raw_object_offset_hex": f"0x{self.start:X}",
            "confidence": self.confidence,
            "warnings": list(self.warnings),
            "raw_fields": dict(self.raw_fields),
        }


@dataclass(slots=True)
class Fallout2SaveDat:
    path: Path
    data: bytearray
    original_data: bytes
    header: SaveHeader
    player_object: PlayerObject
    critter_stats_start: int
    sections: dict[str, Fallout2Section]
    fields: dict[str, Fallout2Field]
    inventory: list[Fallout2InventoryItem]
    warnings: list[str] = field(default_factory=list)
    parser_status: str = "read_only_partial"

    @classmethod
    def from_path(cls, path: str | Path) -> "Fallout2SaveDat":
        p = Path(path)
        return cls.from_bytes(p.read_bytes(), p)

    @classmethod
    def from_bytes(cls, data_bytes: bytes, path: str | Path = "SAVE.DAT") -> "Fallout2SaveDat":
        p = Path(path)
        data = bytearray(data_bytes)
        header = parse_header(data)
        player = find_function5(data, HEADER_SIZE)
        critter = parse_function6(data, player.function6_start)
        obj = cls(
            path=p,
            data=data,
            original_data=bytes(data),
            header=header,
            player_object=player,
            critter_stats_start=critter.start,
            sections={},
            fields={},
            inventory=[],
            warnings=list(player.warnings),
        )
        obj._locate_sections()
        obj._build_inventory()
        obj._build_fields()
        return obj

    @property
    def sha256(self) -> str:
        return hashlib.sha256(bytes(self.data)).hexdigest()

    def _add_section(self, name: str, start: int, end: int, confidence: str, warnings: tuple[str, ...] = ()) -> None:
        if start < 0 or end < start or end > len(self.data):
            self.warnings.append(f"section {name} has invalid bounds 0x{start:X}..0x{end:X}")
            return
        self.sections[name] = Fallout2Section(name, start, end, confidence, warnings)
        self.warnings.extend(warnings)

    def _locate_sections(self) -> None:
        f5s = self.player_object.start
        f6s = self.player_object.function6_start
        f6e = f6s + FUNCTION6_SIZE
        self._add_section("function_5_player_object", f5s, f6s, "high")
        self._add_section("function_6_critter_stats", f6s, f6e, "high")

        f7s = f6e
        f7e = f7s + FUNCTION7_KILL_COUNT_SIZE
        f8s = f7e
        f8e = f8s + FUNCTION8_TAG_SKILL_SIZE
        f9s = f8e
        f9e = f9s + FUNCTION9_PERK_SIZE
        self._add_section("function_7_kill_counts", f7s, f7e, "medium", ("Fallout 2 kill-count size assumed as 0x4C until curated fixtures confirm it",))
        self._add_section("function_8_tag_skills", f8s, f8e, "medium")
        self._add_section("function_9_perks", f9s, f9e, "medium", ("raw perk ranks only; semantic side effects are not modeled",))

        try:
            pc_start = _find_pc_stats(self.data, f9e, min(len(self.data), f9e + 0x5000))
            self._add_section("function_13_pc_stats", pc_start, pc_start + FUNCTION13_PC_STATS_SIZE, "medium", ("Function 13 anchor is heuristic until Fallout 2 fixtures confirm it",))
        except Exception as exc:
            self.warnings.append(f"could not locate Fallout 2 Function 13 PC stats: {exc}")
            return

        try:
            traits_start = _find_traits(self.data, pc_start + FUNCTION13_PC_STATS_SIZE, min(len(self.data), pc_start + 0x2000))
            self._add_section("function_15_traits", traits_start, traits_start + FUNCTION15_TRAITS_SIZE, "medium", ("Function 15 trait anchor is heuristic until Fallout 2 fixtures confirm it",))
        except Exception as exc:
            self.warnings.append(f"could not locate Fallout 2 Function 15 traits: {exc}")

    def _build_inventory(self) -> None:
        result: list[Fallout2InventoryItem] = []
        for item in self.player_object.inventory:
            result.append(_inventory_item_from_shared_parser(item))
        self.inventory = result

    def _add_i32_field(self, name: str, block: str, abs_offset: int, rel_offset: int, risk: str, confidence: str, description: str = "") -> None:
        try:
            value = i32be(self.data, abs_offset)
        except Exception as exc:
            self.warnings.append(f"field {name} could not be read at 0x{abs_offset:X}: {exc}")
            return
        self.fields[name] = Fallout2Field(
            name=name,
            block=block,
            abs_offset=abs_offset,
            rel_offset=rel_offset,
            size=4,
            endian="big",
            type_name="i32",
            value=value,
            risk=risk,
            confidence=confidence,
            writable=False,
            description=description,
        )

    def _add_string_field(self, name: str, abs_offset: int, size: int, value: str, confidence: str, description: str = "") -> None:
        self.fields[name] = Fallout2Field(
            name=name,
            block="header",
            abs_offset=abs_offset,
            rel_offset=abs_offset,
            size=size,
            endian="n/a",
            type_name="cstring",
            value=value,
            risk="SAFE",
            confidence=confidence,
            writable=False,
            description=description,
        )

    def _build_fields(self) -> None:
        self.fields = {}
        f5s = self.player_object.start
        for name, rel, risk, description in (
            ("player.crippled_body_parts", 0x64, "SAFE", "bitfield; raw interpretation kept read-only for Fallout 2"),
            ("player.current_hp", 0x74, "SAFE", "current hit points"),
            ("player.radiation", 0x78, "SAFE", "radiation meter"),
            ("player.poison", 0x7C, "SAFE", "poison meter"),
        ):
            self._add_i32_field(name, "function_5_player_object", f5s + rel, rel, risk, "high", description)

        f6s = self.critter_stats_start
        for idx, stat in enumerate(SPECIAL_NAMES):
            rel = 0x08 + idx * 4
            self._add_i32_field(f"player.base_{stat}", "function_6_critter_stats", f6s + rel, rel, "SAFE", "high", "base SPECIAL value")
        for idx, stat in enumerate(SPECIAL_NAMES):
            rel = 0x94 + idx * 4
            self._add_i32_field(f"player.bonus_{stat}", "function_6_critter_stats", f6s + rel, rel, "ADVANCED", "medium", "bonus SPECIAL value")
        for name, rel in {
            "base_hitpoints": 0x24,
            "bonus_hitpoints": 0xB0,
            "base_action_points": 0x28,
            "base_armor_class": 0x2C,
            "base_melee_damage": 0x34,
            "starting_age": 0x8C,
            "gender": 0x90,
        }.items():
            self._add_i32_field(f"player.{name}", "function_6_critter_stats", f6s + rel, rel, "ADVANCED", "high")
        for idx, skill in enumerate(SKILL_NAMES):
            rel = SKILLS_REL_OFFSET + idx * 4
            self._add_i32_field(f"skills.{skill}", "function_6_critter_stats", f6s + rel, rel, "SAFE", "high", "saved points over base, not final calculated skill")

        f7 = self.sections.get("function_7_kill_counts")
        if f7 is not None:
            for idx in range(FUNCTION7_KILL_COUNT_COUNT):
                name = KILL_COUNT_NAMES[idx] if idx < len(KILL_COUNT_NAMES) else f"kill_type_{idx:02d}"
                self._add_i32_field(f"kill_counts.{name}", "function_7_kill_counts", f7.start + idx * 4, idx * 4, "SAFE", "medium", f"Fallout 2 kill-count index {idx}")

        f8 = self.sections.get("function_8_tag_skills")
        if f8 is not None:
            for idx in range(4):
                self._add_i32_field(f"tag_skills.{idx}", "function_8_tag_skills", f8.start + idx * 4, idx * 4, "SAFE", "medium", "skill id -1 or 0..17")

        f9 = self.sections.get("function_9_perks")
        if f9 is not None:
            for idx in range(FUNCTION9_PERK_COUNT):
                name = PERK_NAMES[idx] if idx < len(PERK_NAMES) else f"perk_{idx:03d}"
                self._add_i32_field(f"perks.{name}", "function_9_perks", f9.start + idx * 4, idx * 4, "ADVANCED", "medium", "raw Fallout 2 perk rank; write disabled")

        f13 = self.sections.get("function_13_pc_stats")
        if f13 is not None:
            for name, rel, conf, desc in (
                ("pc.skill_points", 0x00, "medium", "unspent skill points"),
                ("pc.level", 0x04, "medium", "player level"),
                ("pc.experience", 0x08, "medium", "experience points"),
                ("pc.reputation_or_unknown", 0x0C, "low", "Function 13 offset 0x0C; label requires real fixtures"),
                ("pc.karma_or_unknown", 0x10, "low", "Function 13 offset 0x10; label requires real fixtures"),
            ):
                self._add_i32_field(name, "function_13_pc_stats", f13.start + rel, rel, "SAFE" if conf != "low" else "ADVANCED", conf, desc)

        f15 = self.sections.get("function_15_traits")
        if f15 is not None:
            for idx in range(2):
                self._add_i32_field(f"traits.{idx}", "function_15_traits", f15.start + idx * 4, idx * 4, "SAFE", "medium", "trait id -1 or 0..15")

        for item in self.inventory:
            self._add_i32_field(f"inventory.{item.index}.quantity", "function_5_inventory", item.start, 0, "SAFE", item.confidence, "read-only existing inventory quantity")
            self._add_i32_field(f"inventory.{item.index}.pid", "function_5_inventory", item.start + 0x30, 0x30, "RAW", item.confidence, "read-only object PID; object identity writes are disabled")

        self._add_string_field("header.player_name", 0x1D, 0x20, self.header.player_name, "high")
        self._add_string_field("header.save_name", 0x3D, 0x1E, self.header.save_name, "high")
        self._add_string_field("header.current_map_file", 0x73, 0x10, self.header.current_map_file, "medium")

    def to_dict(self, include_fields: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "game_kind": "fallout2",
            "path": str(self.path),
            "size": len(self.data),
            "size_hex": f"0x{len(self.data):X}",
            "sha256": self.sha256,
            "read_only": True,
            "parser_status": self.parser_status,
            "header": self.header.to_dict(),
            "metadata": {
                "player_name": self.header.player_name,
                "save_name": self.header.save_name,
                "real_date": self.header.to_dict()["real_date"],
                "game_date": self.header.to_dict()["game_date"],
                "game_time": self.header.game_time,
            },
            "sections": {name: section.to_dict() for name, section in sorted(self.sections.items())},
            "inventory_count": self.player_object.inventory_count,
            "inventory": [item.to_dict() for item in self.inventory],
            "warnings": list(dict.fromkeys(self.warnings)),
        }
        if include_fields:
            payload["fields"] = {name: field.to_dict() for name, field in sorted(self.fields.items())}
        return payload

    def fields_payload(self) -> dict[str, Any]:
        return {
            "game_kind": "fallout2",
            "path": str(self.path),
            "read_only": True,
            "parser_status": self.parser_status,
            "fields": {name: field.to_dict() for name, field in sorted(self.fields.items())},
            "warnings": list(dict.fromkeys(self.warnings)),
        }

    def inventory_payload(self) -> dict[str, Any]:
        return {
            "game_kind": "fallout2",
            "slot_path": str(self.path.parent if self.path.name.upper() == "SAVE.DAT" else self.path),
            "read_only": True,
            "inventory_count": self.player_object.inventory_count,
            "inventory": [item.to_dict() for item in self.inventory],
            "blocked_operations": ["add", "remove", "set-pid", "create-object", "write-quantity"],
            "warnings": list(dict.fromkeys(self.warnings)),
        }


def _ints(data: bytes | bytearray, offset: int, count: int) -> list[int]:
    return [i32be(data, offset + i * 4) for i in range(count)]


def _valid_tag_skills(values: list[int]) -> bool:
    return len(values) == 4 and all(v == -1 or 0 <= v < len(SKILL_NAMES) for v in values)


def _plausible_pc_stats(values: list[int]) -> bool:
    if len(values) < 3:
        return False
    skill_points, level, xp = values[:3]
    return 0 <= skill_points <= 999 and 1 <= level <= 99 and 0 <= xp <= 999_999_999


def _find_pc_stats(data: bytes | bytearray, start: int, limit: int) -> int:
    for off in range(start, min(limit, len(data) - FUNCTION13_PC_STATS_SIZE + 1), 4):
        vals = _ints(data, off, 5)
        if _plausible_pc_stats(vals):
            return off
    raise ValueError("could not locate plausible Function 13 PC stats")


def _find_traits(data: bytes | bytearray, start: int, limit: int) -> int:
    for off in range(start, min(limit, len(data) - FUNCTION15_TRAITS_SIZE + 1), 4):
        traits = _ints(data, off, 2)
        if all(v == -1 or 0 <= v < 16 for v in traits):
            return off
    raise ValueError("could not locate plausible Function 15 traits")


def _inventory_item_from_shared_parser(item: ParsedInventoryItem) -> Fallout2InventoryItem:
    raw_fields = {
        "location": item.raw_fields.get("location", 0),
        "frm_id": item.raw_fields.get("frm_id", 0),
        "object_flags": item.raw_fields.get("object_flags", 0),
        "map_level": item.raw_fields.get("map_level", 0),
        "script_id": item.raw_fields.get("script_id", 0),
        "container_count": item.raw_fields.get("container_count", 0),
    }
    if item.ammo_or_charges is not None:
        raw_fields["ammo_or_charges"] = item.ammo_or_charges
    if item.ammo_type is not None:
        raw_fields["ammo_type"] = item.ammo_type
    warnings = list(item.warnings)
    warnings.append("Fallout 2 inventory is read-only; object graph and item creation are disabled")
    return Fallout2InventoryItem(
        index=item.index,
        start=item.start,
        end=item.end,
        quantity=item.quantity,
        pid=item.pid,
        confidence=item.confidence,
        warnings=tuple(dict.fromkeys(warnings)),
        raw_fields=raw_fields,
    )


def _probe_score(data: bytes | bytearray) -> tuple[int, list[str], str, str | None]:
    reasons: list[str] = []
    if len(data) < HEADER_SIZE:
        return 0, [f"SAVE.DAT too small for Fallout header: {len(data)} bytes"], "", None
    raw_sig = bytes(data[:24])
    if not raw_sig.startswith(SAVE_SIGNATURE):
        return 0, [f"missing Fallout SAVE.DAT signature: {raw_sig!r}"], raw_sig.decode("ascii", errors="replace"), None
    signature = c_string(data, 0x00, 0x18).strip()
    reasons.append("Fallout SAVE.DAT signature present")
    score = 25
    try:
        header = parse_header(data)
        version = header.version
        reasons.append(f"header parsed as {version}")
        score += 10
    except Exception as exc:
        version = None
        reasons.append(f"header parse warning: {exc}")
    fp_count = bytes(data).count(FP_SIGNATURE)
    if fp_count:
        score += 20
        reasons.append(f"Function 5 FP marker present ({fp_count} occurrence(s))")
    try:
        player = find_function5(data, HEADER_SIZE)
        if player.function6_start > player.start:
            score += 20
            reasons.append("Function 5 inventory walk located Function 6")
        parse_function6(data, player.function6_start)
        score += 10
        reasons.append("Function 6 critter stats block parsed")
        f6e = player.function6_start + FUNCTION6_SIZE
        tag = _ints(data, f6e + FUNCTION7_KILL_COUNT_SIZE, 4)
        if _valid_tag_skills(tag):
            score += 10
            reasons.append("Fallout 2-sized Function 7 followed by plausible Function 8 tag skills")
        f9e = f6e + FUNCTION7_KILL_COUNT_SIZE + FUNCTION8_TAG_SKILL_SIZE + FUNCTION9_PERK_SIZE
        pc = _ints(data, f9e, 5) if f9e + FUNCTION13_PC_STATS_SIZE <= len(data) else []
        if _plausible_pc_stats(pc):
            score += 5
            reasons.append("Function 13 appears at canonical post-perk offset")
    except Exception as exc:
        reasons.append(f"Fallout 2 structural probe failed: {exc}")
    return min(score, 100), reasons, signature, version


def probe_fallout2(data: bytes | bytearray) -> dict[str, Any]:
    score, reasons, signature, version = _probe_score(data)
    return {
        "game_kind": "fallout2" if score >= 60 else "unknown",
        "confidence": score,
        "signature": signature,
        "version": version,
        "reason": "; ".join(reasons),
        "read_only": True,
    }
