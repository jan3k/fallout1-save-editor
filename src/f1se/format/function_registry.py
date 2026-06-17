"""Source-aligned Fallout 1 SAVE.DAT function registry.

The handler order mirrors Fallout 1's load/save master handler lists.  The
registry is metadata only: it does not parse or rebuild save data.  Parser code
uses it to label byte ranges and expose provenance without weakening the
round-trip preservation model.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SaveFunctionSpec:
    index: int
    name: str
    save_handler: str
    load_handler: str
    parser_status: str
    writable_policy: str
    notes: str = ""


SAVE_FUNCTION_SPECS: tuple[SaveFunctionSpec, ...] = (
    SaveFunctionSpec(0, "unused_0", "DummyFunc", "PrepLoad", "known-empty", "RAW", "source handler boundary only"),
    SaveFunctionSpec(1, "dude_cid", "SaveObjDudeCid", "LoadObjDudeCid", "raw", "RAW", "dude object cid metadata"),
    SaveFunctionSpec(2, "scripts_game_save_1", "scr_game_save", "scr_game_load", "raw", "RAW", "first scripts/global state pass"),
    SaveFunctionSpec(3, "maps", "GameMap2Slot", "SlotMap2Game", "raw", "RAW", "map slot file transfer/state"),
    SaveFunctionSpec(4, "scripts_game_save_2", "scr_game_save", "scr_game_load2", "raw", "RAW", "second scripts/global state pass"),
    SaveFunctionSpec(5, "player_object_inventory", "obj_save_dude", "obj_load_dude", "semantic", "SAFE", "player object and existing inventory entries"),
    SaveFunctionSpec(6, "player_critter_stats", "critter_save", "critter_load", "semantic", "SAFE", "player critter stats and skills"),
    SaveFunctionSpec(7, "kill_counts", "critter_kill_count_save", "critter_kill_count_load", "semantic", "SAFE", "Fallout 1 kill-count array"),
    SaveFunctionSpec(8, "tag_skills", "skill_save", "skill_load", "semantic", "SAFE", "tagged skill ids"),
    SaveFunctionSpec(9, "roll", "roll_save", "roll_load", "known-empty", "RAW", "empty in observed Fallout 1 save"),
    SaveFunctionSpec(10, "perks", "perk_save", "perk_load", "semantic-raw-ranks", "ADVANCED", "raw perk rank array"),
    SaveFunctionSpec(11, "combat", "combat_save", "combat_load", "raw", "RAW", "combat subsystem state"),
    SaveFunctionSpec(12, "combat_ai", "combat_ai_save", "combat_ai_load", "known-empty", "RAW", "empty in observed Fallout 1 save"),
    SaveFunctionSpec(13, "pc_stats", "stat_save", "stat_load", "semantic", "SAFE", "unspent skill points, level, xp, reputation, karma"),
    SaveFunctionSpec(14, "items_subsystem", "item_save", "item_load", "known-empty", "RAW", "empty in observed Fallout 1 save"),
    SaveFunctionSpec(15, "queue_events", "queue_save", "queue_load", "raw", "RAW", "queue/event state"),
    SaveFunctionSpec(16, "traits", "trait_save", "trait_load", "semantic", "SAFE", "selected trait ids"),
    SaveFunctionSpec(17, "automap_state", "automap_save", "automap_load", "raw", "RAW", "SAVE.DAT automap state; AUTOMAP.SAV is handled as a slot artifact"),
    SaveFunctionSpec(18, "options", "save_options", "load_options", "semantic-partial", "ADVANCED", "partially mapped options block"),
    SaveFunctionSpec(19, "editor", "editor_save", "editor_load", "raw", "RAW", "editor subsystem state"),
    SaveFunctionSpec(20, "worldmap", "save_world_map", "load_world_map", "raw", "RAW", "world map and late world state"),
    SaveFunctionSpec(21, "pipboy", "save_pipboy", "load_pipboy", "raw", "RAW", "currently merged into late raw world state"),
    SaveFunctionSpec(22, "movies", "gmovie_save", "gmovie_load", "raw", "RAW", "currently merged into late raw world state"),
    SaveFunctionSpec(23, "skill_use", "skill_use_slot_save", "skill_use_slot_load", "raw", "RAW", "currently merged into late raw world state"),
    SaveFunctionSpec(24, "party", "partyMemberSave", "partyMemberLoad", "raw", "EXPERIMENTAL", "party/companion state; raw preservation only"),
    SaveFunctionSpec(25, "interface", "intface_save", "intface_load", "raw", "RAW", "interface state tail"),
    SaveFunctionSpec(26, "unused_26", "DummyFunc", "EndLoad", "known-empty", "RAW", "source handler boundary only"),
)

if [spec.index for spec in SAVE_FUNCTION_SPECS] != list(range(27)):
    raise RuntimeError("SAVE_FUNCTION_SPECS must contain exactly 27 ordered Fallout 1 handlers")

FUNCTION_NAMES = [spec.name for spec in SAVE_FUNCTION_SPECS]


def get_function_spec(index: int) -> SaveFunctionSpec:
    try:
        return SAVE_FUNCTION_SPECS[index]
    except IndexError as exc:
        raise KeyError(f"unknown Fallout 1 save function index: {index}") from exc
