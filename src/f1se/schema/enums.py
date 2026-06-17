"""Fallout 1 constants and display names."""
from __future__ import annotations

from f1se.schema.items import ITEM_PID_NAMES, ITEM_TYPE_SIZES

PRIMARY_STAT_MIN = 1
PRIMARY_STAT_MAX = 10
PRIMARY_STAT_COUNT = 7
SAVEABLE_STAT_COUNT = 35
SKILL_COUNT = 18
TAG_SKILL_COUNT = 4
TRAIT_COUNT = 16
PC_TRAIT_MAX = 2
PERK_COUNT = 64
PC_LEVEL_MAX = 21
KILL_TYPE_COUNT = 15

SPECIAL_NAMES = [
    "strength",
    "perception",
    "endurance",
    "charisma",
    "intelligence",
    "agility",
    "luck",
]

SKILL_NAMES = [
    "small_guns",
    "big_guns",
    "energy_weapons",
    "unarmed",
    "melee_weapons",
    "throwing",
    "first_aid",
    "doctor",
    "sneak",
    "lockpick",
    "steal",
    "traps",
    "science",
    "repair",
    "speech",
    "barter",
    "gambling",
    "outdoorsman",
]

TRAIT_NAMES = [
    "fast_metabolism",
    "bruiser",
    "small_frame",
    "one_hander",
    "finesse",
    "kamikaze",
    "heavy_handed",
    "fast_shot",
    "bloody_mess",
    "jinxed",
    "good_natured",
    "chem_reliant",
    "chem_resistant",
    "night_person",
    "skilled",
    "gifted",
]

PERK_NAMES = [
    "awareness",
    "bonus_hth_attacks",
    "bonus_hth_damage",
    "bonus_move",
    "bonus_ranged_damage",
    "bonus_rate_of_fire",
    "earlier_sequence",
    "faster_healing",
    "more_criticals",
    "night_vision",
    "presence",
    "rad_resistance",
    "toughness",
    "strong_back",
    "sharpshooter",
    "silent_running",
    "survivalist",
    "master_trader",
    "educated",
    "healer",
    "fortune_finder",
    "better_criticals",
    "empathy",
    "slayer",
    "sniper",
    "silent_death",
    "action_boy",
    "mental_block",
    "lifegiver",
    "dodger",
    "snakeater",
    "mr_fixit",
    "medic",
    "master_thief",
    "speaker",
    "heave_ho",
    "friendly_foe",
    "pickpocket",
    "ghost",
    "cult_of_personality",
    "scrounger",
    "explorer",
    "flower_child",
    "pathfinder",
    "animal_friend",
    "scout",
    "mysterious_stranger",
    "ranger",
    "quick_pockets",
    "smooth_talker",
    "swift_learner",
    "tag",
    "mutate",
    "nuka_cola_addiction",
    "buffout_addiction",
    "mentats_addiction",
    "psycho_addiction",
    "radaway_addiction",
    "weapon_long_range",
    "weapon_accurate",
    "weapon_penetrate",
    "weapon_knockback",
    "powered_armor",
    "combat_armor",
]

# Fallout 1 kill-count block in SAVE.DAT Function 7.  The engine source stores
# an array of kill counters; the exact user-facing labels are data/message driven,
# so the editor exposes stable indices instead of guessing localized names.
KILL_COUNT_NAMES = [f"kill_type_{i:02d}" for i in range(KILL_TYPE_COUNT)]
KILL_COUNT_DISPLAY_NAMES = [f"Kill type {i:02d}" for i in range(KILL_TYPE_COUNT)]

# Function 5 critter body-part damage bitfield. Names match the F12se UI idea
# of explicit limb/eye toggles, but values are still edited as one raw bitfield.
CRIPPLED_PART_FLAGS = {
    "eye": 0x01,
    "right_arm": 0x02,
    "left_arm": 0x04,
    "right_leg": 0x08,
    "left_leg": 0x10,
}

TRAIT_EFFECTS = {
    "fast_metabolism": "Healing rate +2; radiation and poison resistance are effectively removed by the engine trait adjustment.",
    "bruiser": "Strength +2; maximum action points -2.",
    "small_frame": "Agility +1; carry weight penalty based on Strength.",
    "one_hander": "Engine-side weapon accuracy effects; no direct saved stat change here.",
    "finesse": "Critical chance +10; engine-side damage trade-off is not written to SAVE.DAT by this editor.",
    "kamikaze": "Armor class base bonus is suppressed; sequence +5.",
    "heavy_handed": "Melee damage +4; better criticals penalty.",
    "fast_shot": "Engine-side attack mode/rate-of-fire effects; no direct saved stat change here.",
    "bloody_mess": "Presentation/endgame effect; no direct saved stat change here.",
    "jinxed": "Engine-side critical failure effect; no direct saved stat change here.",
    "good_natured": "Combat skills -10; First Aid, Doctor, Speech and Barter +15.",
    "chem_reliant": "Engine-side addiction duration/effects; no direct saved stat change here.",
    "chem_resistant": "Engine-side chem resistance/effects; no direct saved stat change here.",
    "night_person": "Perception and Intelligence are adjusted dynamically by time of day.",
    "skilled": "All skills +10; perk cadence side effect is engine-side.",
    "gifted": "All primary S.P.E.C.I.A.L. stats +1; all skills -10.",
}
