"""Round-trip-safe SAVE.DAT parser/editor."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import copy
import hashlib
import json
from typing import Any

from f1se.io.endian import c_string, i32be, put_i32be, u32be
from f1se.format.header import HEADER_SIZE, SaveHeader, parse_header
from f1se.format.functions import FUNCTION_NAMES, FunctionBlock
from f1se.format.function_5_player_object import PlayerObject, find_function5
from f1se.format.function_6_critter_stats import (
    FUNCTION6_SIZE,
    SKILLS_REL_OFFSET,
    STAT_REL_OFFSETS,
    CritterStats,
    derived_stat_targets,
    parse_function6,
)
from f1se.schema.enums import (
    KILL_COUNT_NAMES,
    PERK_COUNT,
    PERK_NAMES,
    SKILL_NAMES,
    SPECIAL_NAMES,
    TRAIT_EFFECTS,
    TRAIT_NAMES,
)
from f1se.schema.fields import Diff, Field
from f1se.schema import validators as V


def _ints(data: bytes | bytearray, offset: int, count: int) -> list[int]:
    return [i32be(data, offset + i * 4) for i in range(count)]


def _valid_tag_skills(values: list[int]) -> bool:
    return len(values) == 4 and all(v == -1 or 0 <= v < 18 for v in values)


def _find_tag_skills_after_kills(data: bytes | bytearray, start: int) -> tuple[int, int, list[int]]:
    # Fallout 1 has fewer kill counters than Fallout 2 docs usually imply. 15 is
    # the observed and source-compatible count for the supplied Fallout 1 save.
    for kill_count in (15, 19, 20):
        tag_start = start + kill_count * 4
        if tag_start + 16 <= len(data):
            vals = _ints(data, tag_start, 4)
            if _valid_tag_skills(vals):
                return kill_count, tag_start, vals
    # fallback: scan a small window only; do not search the entire file.
    for tag_start in range(start, min(start + 0x100, len(data) - 16 + 1), 4):
        vals = _ints(data, tag_start, 4)
        if _valid_tag_skills(vals):
            return (tag_start - start) // 4, tag_start, vals
    raise ValueError("could not locate Function 8 tag skills after Function 6")


def _find_pc_stats(data: bytes | bytearray, start: int, limit: int) -> int:
    for off in range(start, min(limit, len(data) - 20 + 1), 4):
        vals = _ints(data, off, 5)
        skill_points, level, xp, reputation, karma = vals
        if 0 <= skill_points <= 999 and 1 <= level <= 21 and 0 <= xp <= 99_999_999 and -1000 <= reputation <= 1000 and -1_000_000 <= karma <= 1_000_000:
            return off
    raise ValueError("could not locate Function 13 PC stats")


def _looks_like_options(data: bytes | bytearray, off: int) -> bool:
    if off < 0 or off + 0x50 > len(data):
        return False
    try:
        vals = _ints(data, off, 20)
    except ValueError:
        return False
    bool_positions = [0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 12]
    if any(vals[i] not in (0, 1) for i in bool_positions):
        return False
    if vals[2] not in (0, 1, 2, 3):
        return False
    if not (0 <= vals[11] <= 100):
        return False
    # float fields commonly encoded as IEEE 754 1.0/3.5/0.875 etc.; keep loose.
    return True


def _find_options(data: bytes | bytearray, start: int) -> int:
    for off in range(start, len(data) - 0x50 + 1, 4):
        if _looks_like_options(data, off):
            trait_start = off - 12
            if trait_start >= 0:
                t = _ints(data, trait_start, 2)
                if all(v == -1 or 0 <= v < 16 for v in t):
                    return off
    raise ValueError("could not locate Function 18 options block")


@dataclass(slots=True)
class SaveDat:
    path: Path
    data: bytearray
    original_data: bytes
    header: SaveHeader
    player_object: PlayerObject
    critter_stats: CritterStats
    blocks: list[FunctionBlock]
    fields: dict[str, Field]
    warnings: list[str] = field(default_factory=list)
    kill_count_start: int = 0
    kill_count_count: int = 0
    tag_skills_start: int = 0
    pc_stats_start: int = 0
    traits_start: int = 0
    options_start: int = 0

    @classmethod
    def from_path(cls, path: str | Path) -> "SaveDat":
        p = Path(path)
        data = bytearray(p.read_bytes())
        header = parse_header(data)
        f5 = find_function5(data, HEADER_SIZE)
        f6 = parse_function6(data, f5.function6_start)
        obj = cls(
            path=p,
            data=data,
            original_data=bytes(data),
            header=header,
            player_object=f5,
            critter_stats=f6,
            blocks=[],
            fields={},
            warnings=[],
        )
        obj._detect_blocks()
        obj._build_fields()
        obj._validate_cross_field_state(warn_only=True)
        return obj

    @property
    def sha256(self) -> str:
        return hashlib.sha256(bytes(self.data)).hexdigest()

    def clone(self) -> "SaveDat":
        return copy.deepcopy(self)

    def selected_trait_ids(self) -> list[int]:
        if not self.traits_start:
            return []
        return [i32be(self.data, self.traits_start + idx * 4) for idx in range(2)]

    def selected_traits(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for idx, trait_id in enumerate(self.selected_trait_ids()):
            name = TRAIT_NAMES[trait_id] if 0 <= trait_id < len(TRAIT_NAMES) else "none"
            result.append({
                "slot": idx,
                "id": trait_id,
                "name": name if trait_id != -1 else "none",
                "effect": TRAIT_EFFECTS.get(name, "No local editor effect metadata."),
            })
        return result

    def trait_effect_notes(self) -> list[str]:
        notes: list[str] = []
        for trait in self.selected_traits():
            if trait["id"] != -1:
                notes.append(f"{trait['slot']}: {trait['name']}: {trait['effect']}")
        return notes

    def effective_special(self) -> dict[str, dict[str, int]]:
        selected = {t["name"] for t in self.selected_traits() if t["id"] != -1}
        result: dict[str, dict[str, int]] = {}
        for stat in SPECIAL_NAMES:
            base = int(self.fields[f"player.base_{stat}"].value)
            bonus = int(self.fields[f"player.bonus_{stat}"].value)
            trait = 0
            if "gifted" in selected:
                trait += 1
            if stat == "strength" and "bruiser" in selected:
                trait += 2
            if stat == "agility" and "small_frame" in selected:
                trait += 1
            result[stat] = {"base": base, "bonus": bonus, "static_trait": trait, "effective_static": base + bonus + trait}
        return result

    def preset_patch(self, preset: str) -> dict[str, int]:
        if preset == "max-special":
            return {f"player.base_{stat}": 10 for stat in SPECIAL_NAMES}
        if preset == "heal":
            hp_target = int(self.fields.get("player.base_hitpoints", self.fields["player.current_hp"]).value)
            return {"player.current_hp": hp_target, "player.radiation": 0, "player.poison": 0}
        if preset == "clear-crippled":
            return {"player.crippled_body_parts": 0}
        raise KeyError(f"unknown preset: {preset}")

    def _detect_blocks(self) -> None:
        blocks: list[FunctionBlock] = []
        f5s = self.player_object.start
        f6s = self.critter_stats.start
        f6e = self.critter_stats.end
        # Functions 0..4 are preserved as raw regions before the FP marker.
        blocks.append(FunctionBlock(0, FUNCTION_NAMES[0], HEADER_SIZE, HEADER_SIZE, "known-empty"))
        # Function 1 is 4 bytes immediately after the header in stock saves.
        f1_end = min(HEADER_SIZE + 4, f5s)
        blocks.append(FunctionBlock(1, FUNCTION_NAMES[1], HEADER_SIZE, f1_end, "raw"))
        # Split unknown variable pre-player payload into coarse source-order buckets.
        pre = f5s - f1_end
        f2_end = f1_end + pre // 3
        f3_end = f1_end + 2 * pre // 3
        blocks.append(FunctionBlock(2, FUNCTION_NAMES[2], f1_end, f2_end, "raw", ["coarse split before Function 5; preserved byte-for-byte"]))
        blocks.append(FunctionBlock(3, FUNCTION_NAMES[3], f2_end, f3_end, "raw", ["coarse split before Function 5; preserved byte-for-byte"]))
        blocks.append(FunctionBlock(4, FUNCTION_NAMES[4], f3_end, f5s, "raw", ["coarse split before Function 5; preserved byte-for-byte"]))
        blocks.append(FunctionBlock(5, FUNCTION_NAMES[5], f5s, f6s, "semantic"))
        blocks.append(FunctionBlock(6, FUNCTION_NAMES[6], f6s, f6e, "semantic"))

        kill_count, tag_start, _tag_vals = _find_tag_skills_after_kills(self.data, f6e)
        self.kill_count_start = f6e
        self.kill_count_count = kill_count
        self.tag_skills_start = tag_start
        blocks.append(FunctionBlock(7, FUNCTION_NAMES[7], f6e, tag_start, "semantic", [f"detected {kill_count} Fallout 1 kill counters"]))
        tag_end = tag_start + 16
        blocks.append(FunctionBlock(8, FUNCTION_NAMES[8], tag_start, tag_end, "semantic"))
        blocks.append(FunctionBlock(9, FUNCTION_NAMES[9], tag_end, tag_end, "known-empty"))
        perk_start = tag_end
        perk_end = perk_start + PERK_COUNT * 4
        blocks.append(FunctionBlock(10, FUNCTION_NAMES[10], perk_start, perk_end, "semantic-raw-ranks"))
        # combat_save is fixed enough in the fixture; combat_ai_save and item_save are 0-byte in fallout1-ce.
        pc_start = _find_pc_stats(self.data, perk_end + 0x10, perk_end + 0x100)
        self.pc_stats_start = pc_start
        blocks.append(FunctionBlock(11, FUNCTION_NAMES[11], perk_end, pc_start, "raw", ["combat block split inferred from following PC stats anchor"]))
        blocks.append(FunctionBlock(12, FUNCTION_NAMES[12], pc_start, pc_start, "known-empty"))
        pc_end = pc_start + 20
        blocks.append(FunctionBlock(13, FUNCTION_NAMES[13], pc_start, pc_end, "semantic"))
        blocks.append(FunctionBlock(14, FUNCTION_NAMES[14], pc_end, pc_end, "known-empty"))
        options_start = _find_options(self.data, pc_end)
        self.options_start = options_start
        self.traits_start = options_start - 12
        blocks.append(FunctionBlock(15, FUNCTION_NAMES[15], pc_end, self.traits_start, "raw", ["queue/event state preserved raw"]))
        blocks.append(FunctionBlock(16, FUNCTION_NAMES[16], self.traits_start, self.traits_start + 8, "semantic"))
        blocks.append(FunctionBlock(17, FUNCTION_NAMES[17], self.traits_start + 8, options_start, "raw", ["automap state kept raw in SAVE.DAT; AUTOMAP.SAV handled as slot artifact"]))
        options_end = options_start + 0x50
        blocks.append(FunctionBlock(18, FUNCTION_NAMES[18], options_start, options_end, "semantic-partial"))
        editor_end = min(options_end + 5, len(self.data))
        blocks.append(FunctionBlock(19, FUNCTION_NAMES[19], options_end, editor_end, "raw"))
        # Late variable blocks are preserved exactly, with interface last 16 bytes split if possible.
        interface_start = max(editor_end, len(self.data) - 16)
        blocks.append(FunctionBlock(20, FUNCTION_NAMES[20], editor_end, interface_start, "raw", ["late-worldstate split is heuristic; bytes preserved"]))
        blocks.append(FunctionBlock(21, FUNCTION_NAMES[21], interface_start, interface_start, "raw", ["merged into worldmap raw in this version"]))
        blocks.append(FunctionBlock(22, FUNCTION_NAMES[22], interface_start, interface_start, "raw", ["merged into worldmap raw in this version"]))
        blocks.append(FunctionBlock(23, FUNCTION_NAMES[23], interface_start, interface_start, "raw", ["merged into worldmap raw in this version"]))
        blocks.append(FunctionBlock(24, FUNCTION_NAMES[24], interface_start, interface_start, "raw", ["merged into worldmap raw in this version"]))
        blocks.append(FunctionBlock(25, FUNCTION_NAMES[25], interface_start, len(self.data), "raw"))
        blocks.append(FunctionBlock(26, FUNCTION_NAMES[26], len(self.data), len(self.data), "known-empty"))
        self.blocks = blocks
        self.warnings.extend(w for b in blocks for w in b.warnings)

    def _add_i32_field(self, name: str, block: str, abs_offset: int, rel_offset: int, value: int, risk: str, validator: Any, description: str = "") -> None:
        self.fields[name] = Field(
            name=name,
            file_name="SAVE.DAT",
            block=block,
            abs_offset=abs_offset,
            rel_offset=rel_offset,
            size=4,
            endian="big",
            type_name="i32",
            value=value,
            risk=risk,
            validator=validator,
            writable=True,
            description=description,
        )

    def _build_fields(self) -> None:
        self.fields = {}
        # Function 5 SAFE player object fields.
        f5s = self.player_object.start
        f5_fields = [
            ("player.coordinates", 0x04, V.validate_any_i32, "ADVANCED"),
            ("player.facing", 0x1C, V.validate_any_i32, "ADVANCED"),
            ("player.map_level", 0x28, V.validate_any_i32, "ADVANCED"),
            ("player.crippled_body_parts", 0x64, V.validate_crippled_body_parts, "SAFE"),
            ("player.current_hp", 0x74, V.validate_hp, "SAFE"),
            ("player.radiation", 0x78, V.validate_meter, "SAFE"),
            ("player.poison", 0x7C, V.validate_meter, "SAFE"),
        ]
        for name, rel, validator, risk in f5_fields:
            description = ""
            if name == "player.crippled_body_parts":
                description = "bitfield: eye=0x01, right_arm=0x02, left_arm=0x04, right_leg=0x08, left_leg=0x10"
            self._add_i32_field(name, "function_5_player_object", f5s + rel, rel, i32be(self.data, f5s + rel), risk, validator, description)

        # Function 6 stats.
        f6s = self.critter_stats.start
        for idx, stat in enumerate(SPECIAL_NAMES):
            rel = 0x08 + idx * 4
            self._add_i32_field(f"player.base_{stat}", "function_6_critter_stats", f6s + rel, rel, i32be(self.data, f6s + rel), "SAFE", V.validate_special)
        for idx, stat in enumerate(SPECIAL_NAMES):
            rel = 0x94 + idx * 4
            self._add_i32_field(f"player.bonus_{stat}", "function_6_critter_stats", f6s + rel, rel, i32be(self.data, f6s + rel), "SAFE", V.validate_bonus_stat)
        derived = {
            "base_hitpoints": (0x24, V.validate_hp),
            "base_action_points": (0x28, V.validate_any_i32),
            "base_armor_class": (0x2C, V.validate_any_i32),
            "base_melee_damage": (0x34, V.validate_any_i32),
            "base_carry_weight": (0x38, V.validate_any_i32),
            "base_sequence": (0x3C, V.validate_any_i32),
            "base_healing_rate": (0x40, V.validate_any_i32),
            "base_critical_chance": (0x44, V.validate_any_i32),
            "radiation_resistance": (0x84, V.validate_any_i32),
            "poison_resistance": (0x88, V.validate_any_i32),
            "starting_age": (0x8C, V.validate_any_i32),
            "gender": (0x90, V.validate_any_i32),
        }
        for name, (rel, validator) in derived.items():
            self._add_i32_field(f"player.{name}", "function_6_critter_stats", f6s + rel, rel, i32be(self.data, f6s + rel), "ADVANCED", validator)
        for idx, skill in enumerate(SKILL_NAMES):
            rel = SKILLS_REL_OFFSET + idx * 4
            self._add_i32_field(f"skills.{skill}", "function_6_critter_stats", f6s + rel, rel, i32be(self.data, f6s + rel), "SAFE", V.validate_skill_over_base, "saved points over base, not final calculated skill")

        # Function 7 kill counters. Fallout 1 source stores a fixed array;
        # labels are exposed as stable indices to avoid localization guesses.
        for idx in range(self.kill_count_count):
            off = self.kill_count_start + idx * 4
            name = KILL_COUNT_NAMES[idx] if idx < len(KILL_COUNT_NAMES) else f"kill_type_{idx:02d}"
            self._add_i32_field(
                f"kill_counts.{name}",
                "function_7_kill_counts",
                off,
                idx * 4,
                i32be(self.data, off),
                "SAFE",
                V.validate_kill_count,
                f"Fallout 1 kill-count index {idx}",
            )

        # Tag skills.
        for idx in range(4):
            off = self.tag_skills_start + idx * 4
            desc = "skill id -1 or 0..17"
            self._add_i32_field(f"tag_skills.{idx}", "function_8_tag_skills", off, idx * 4, i32be(self.data, off), "SAFE", V.validate_tag_skill, desc)

        # Perks raw ranks.
        perk_start = self.tag_skills_start + 16
        for idx in range(PERK_COUNT):
            off = perk_start + idx * 4
            name = PERK_NAMES[idx] if idx < len(PERK_NAMES) else f"perk_{idx}"
            self._add_i32_field(f"perks.{name}", "function_10_perks", off, idx * 4, i32be(self.data, off), "ADVANCED", V.validate_perk_rank, "raw perk rank; semantic side effects are not fully implemented")

        # PC stats.
        pc_names = [
            ("pc.skill_points", V.validate_skill_points),
            ("pc.level", V.validate_level),
            ("pc.experience", V.validate_xp),
            ("pc.reputation", V.validate_reputation),
            ("pc.karma", V.validate_karma),
        ]
        for idx, (name, validator) in enumerate(pc_names):
            off = self.pc_stats_start + idx * 4
            self._add_i32_field(name, "function_13_pc_stats", off, idx * 4, i32be(self.data, off), "SAFE", validator)

        # Traits.
        for idx in range(2):
            off = self.traits_start + idx * 4
            self._add_i32_field(f"traits.trait_{idx}", "function_16_traits", off, idx * 4, i32be(self.data, off), "SAFE", V.validate_trait, "trait id -1 or 0..15")
            self.fields[f"traits.{idx}"] = copy.copy(self.fields[f"traits.trait_{idx}"])
            self.fields[f"traits.{idx}"].name = f"traits.{idx}"

        # Inventory quantities and known usage fields.
        for item in self.player_object.inventory:
            self._add_i32_field(f"inventory.{item.index}.quantity", "function_5_inventory", item.start, 0, item.quantity, "SAFE", V.validate_quantity, item.object_name)
            if item.ammo_or_charges is not None:
                self._add_i32_field(f"inventory.{item.index}.ammo_or_charges", "function_5_inventory", item.start + 0x5C, 0x5C, item.ammo_or_charges, "SAFE", V.validate_any_i32, item.object_name)
            if item.ammo_type is not None:
                self._add_i32_field(f"inventory.{item.index}.ammo_type", "function_5_inventory", item.start + 0x60, 0x60, item.ammo_type, "ADVANCED", V.validate_any_i32, item.object_name)

        # Partial options block; names based on Fallout options save order.
        opt_names = [
            "options.game_difficulty",
            "options.combat_difficulty",
            "options.violence_level",
            "options.target_highlight",
            "options.combat_messages",
            "options.combat_taunts",
            "options.language_filter",
            "options.running",
            "options.subtitles",
            "options.item_highlight",
            "options.combat_speed",
            "options.player_speedup",
            "options.brightness",
        ]
        for idx, name in enumerate(opt_names):
            off = self.options_start + idx * 4
            validator = V.validate_any_i32
            risk = "SAFE" if idx in (0, 1, 2, 10, 11) else "ADVANCED"
            self._add_i32_field(name, "function_18_options", off, idx * 4, i32be(self.data, off), risk, validator)

        # Header string metadata: read-only in this first version to avoid C-string size mistakes.
        self.fields["header.player_name"] = Field("header.player_name", "SAVE.DAT", "header", 0x1D, 0x1D, 0x20, "n/a", "cstring", self.header.player_name, "SAFE", None, False)
        self.fields["header.current_map_file"] = Field("header.current_map_file", "SAVE.DAT", "header", 0x73, 0x73, 0x10, "n/a", "cstring", self.header.current_map_file, "ADVANCED", None, False)

    def _refresh_after_mutation(self) -> None:
        self.header = parse_header(self.data)
        self.player_object = find_function5(self.data, HEADER_SIZE)
        self.critter_stats = parse_function6(self.data, self.player_object.function6_start)
        old_warnings = list(self.warnings)
        self.warnings = []
        self._detect_blocks()
        self._build_fields()
        self.warnings = list(dict.fromkeys(old_warnings + self.warnings))

    def _validate_cross_field_state(self, warn_only: bool = False) -> None:
        errors: list[str] = []
        tags = [i32be(self.data, self.tag_skills_start + i * 4) for i in range(4)] if self.tag_skills_start else []
        tag_nonempty = [t for t in tags if t != -1]
        if len(tag_nonempty) != len(set(tag_nonempty)):
            errors.append("duplicate tag skill ids")
        traits = [i32be(self.data, self.traits_start + i * 4) for i in range(2)] if self.traits_start else []
        trait_nonempty = [t for t in traits if t != -1]
        if len(trait_nonempty) != len(set(trait_nonempty)):
            errors.append("duplicate trait ids")
        if errors:
            if warn_only:
                self.warnings.extend(errors)
            else:
                raise ValueError("; ".join(errors))

    def set_field(self, name: str, value: int, *, allow_out_of_range: bool = False, mode: str = "raw") -> list[Diff]:
        if name not in self.fields:
            raise KeyError(f"unknown field: {name}")
        field = self.fields[name]
        if not field.writable:
            raise ValueError(f"field is read-only in this version: {name}")
        if field.type_name != "i32":
            raise ValueError(f"only i32 fields are writable in this version: {name}")
        if field.validator is V.validate_special:
            field.validator(int(value), allow_out_of_range=allow_out_of_range)
        elif field.validator is not None:
            field.validator(int(value))
        diffs: list[Diff] = []
        new_bytes = int(value).to_bytes(4, "big", signed=True)
        old = bytes(self.data[field.abs_offset:field.abs_offset + 4])
        if old != new_bytes:
            put_i32be(self.data, field.abs_offset, int(value))
            diffs.append(Diff(field.file_name, field.abs_offset, old, new_bytes, name))
        if mode == "semantic" and name.startswith("player.base_") and name.split("player.base_", 1)[1] in SPECIAL_NAMES:
            # Recalculate formulaic derived stats only; perk/trait side effects stay out of scope.
            current = {stat: i32be(self.data, self.fields[f"player.base_{stat}"].abs_offset) for stat in SPECIAL_NAMES}
            targets = derived_stat_targets(
                current["strength"], current["perception"], current["endurance"], current["agility"], current["luck"]
            )
            for derived_name, derived_value in targets.items():
                if derived_name in self.fields:
                    df = self.fields[derived_name]
                    old_d = bytes(self.data[df.abs_offset:df.abs_offset + 4])
                    new_d = int(derived_value).to_bytes(4, "big", signed=True)
                    if old_d != new_d:
                        put_i32be(self.data, df.abs_offset, int(derived_value))
                        diffs.append(Diff(df.file_name, df.abs_offset, old_d, new_d, derived_name))
        self._refresh_after_mutation()
        self._validate_cross_field_state(warn_only=False)
        return diffs

    def apply_patch(self, patch: dict[str, Any], *, allow_out_of_range: bool = False, mode: str = "raw") -> list[Diff]:
        # Validate all fields before mutating.
        staged = self.clone()
        diffs: list[Diff] = []
        for name, value in patch.items():
            diffs.extend(staged.set_field(name, int(value), allow_out_of_range=allow_out_of_range, mode=mode))
        self.data[:] = staged.data
        self._refresh_after_mutation()
        self._validate_cross_field_state(warn_only=False)
        return diffs

    def raw_read(self, offset: int, size: int) -> bytes:
        if offset < 0 or size < 0 or offset + size > len(self.data):
            raise ValueError("raw read outside SAVE.DAT")
        return bytes(self.data[offset:offset + size])

    def raw_write(self, offset: int, payload: bytes, field_name: str = "raw") -> list[Diff]:
        if offset < 0 or offset + len(payload) > len(self.data):
            raise ValueError("raw write outside SAVE.DAT")
        old = bytes(self.data[offset:offset + len(payload)])
        if old == payload:
            return []
        self.data[offset:offset + len(payload)] = payload
        self._refresh_after_mutation()
        return [Diff("SAVE.DAT", offset, old, payload, field_name)]

    def verify(self) -> list[str]:
        issues: list[str] = []
        try:
            parse_header(self.data)
        except Exception as exc:
            issues.append(f"header: {exc}")
        if len(self.blocks) != 27:
            issues.append(f"expected 27 function blocks, got {len(self.blocks)}")
        prev = HEADER_SIZE
        for b in self.blocks:
            if b.start < 0 or b.end < b.start or b.end > len(self.data):
                issues.append(f"block {b.index} has invalid bounds")
            if b.index > 0 and b.start < prev:
                issues.append(f"block {b.index} overlaps previous block")
            prev = max(prev, b.end)
        if self.player_object.inventory_count != len(self.player_object.inventory):
            issues.append("inventory count mismatch")
        for name, field in self.fields.items():
            if field.writable and field.type_name == "i32" and field.validator is not None:
                try:
                    if field.validator is V.validate_special:
                        field.validator(int(field.value), allow_out_of_range=True)
                    else:
                        field.validator(int(field.value))
                except Exception as exc:
                    issues.append(f"field {name}: {exc}")
        # Round-trip safety invariant: parsing without edits keeps bytes equal.
        reparsed = SaveDat.from_bytes(bytes(self.data), self.path)
        if bytes(reparsed.data) != bytes(self.data):
            issues.append("round-trip parse changed bytes")
        return issues

    @classmethod
    def from_bytes(cls, data_bytes: bytes, path: str | Path = "SAVE.DAT") -> "SaveDat":
        p = Path(path)
        data = bytearray(data_bytes)
        header = parse_header(data)
        f5 = find_function5(data, HEADER_SIZE)
        f6 = parse_function6(data, f5.function6_start)
        obj = cls(p, data, bytes(data), header, f5, f6, [], {}, [])
        obj._detect_blocks()
        obj._build_fields()
        obj._validate_cross_field_state(warn_only=True)
        return obj

    def to_dict(self, include_raw_hashes: bool = True) -> dict:
        return {
            "path": str(self.path),
            "size": len(self.data),
            "size_hex": f"0x{len(self.data):X}",
            "sha256": self.sha256,
            "header": self.header.to_dict(),
            "player_object": self.player_object.to_dict(),
            "critter_stats": self.critter_stats.to_dict(),
            "blocks": [b.to_dict(self.data if include_raw_hashes else None) for b in self.blocks],
            "fields": {name: field.to_dict() for name, field in sorted(self.fields.items())},
            "warnings": list(dict.fromkeys(self.warnings)),
            "selected_traits": self.selected_traits(),
            "effective_special_static": self.effective_special(),
            "kill_count_count": self.kill_count_count,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)
