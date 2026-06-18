# Fallout 1 derived-stats report

`derived-stats` is a read-only consistency report for Fallout 1 saves.

```bash
f1se derived-stats SLOT01
f1se derived-stats SLOT01 --json
f1se derived-stats SLOT01 --game auto --json
```

## Purpose

The command compares saved secondary stat fields against conservative formula targets computed from current base S.P.E.C.I.A.L. values.

This is useful after manual edits because some fixed-width fields can become internally inconsistent. The command reports differences without changing the save.

## Formula scope

The report currently checks stable formulaic fields covered by the existing semantic SPECIAL recalculation model:

- `player.base_hitpoints`
- `player.base_action_points`
- `player.base_armor_class`
- `player.base_melee_damage`
- `player.base_carry_weight`
- `player.base_sequence`
- `player.base_healing_rate`
- `player.base_critical_chance`
- `player.radiation_resistance`
- `player.poison_resistance`

The command intentionally does not recompute armor, equipment, temporary effects, many perk effects, or non-local trait effects.

## JSON contract

The public JSON contract id is `derived_stats`.

Top-level fields:

- `game_kind`
- `slot_path`
- `read_only`
- `identity`
- `source_special`
- `formula_scope`
- `derived_stats`
- `mismatches`
- `summary`
- `warnings`

## Safety

This command is read-only. It does not invoke `set`, `patch`, `preset`, semantic recalculation, or raw-write.
