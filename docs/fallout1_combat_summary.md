# Fallout 1 combat summary

`combat-summary` is a read-only command for inspecting combat-relevant player state in a Fallout 1 save slot.

```bash
f1se combat-summary SLOT01
f1se combat-summary SLOT01 --json
f1se combat-summary SLOT01 --game auto --json
```

## Purpose

The command groups the combat fields that are otherwise scattered across the field registry.

It is useful after status edits or SPECIAL edits because it quickly shows the effective saved combat state.

## Included data

The payload includes:

- base S.P.E.C.I.A.L.;
- current/max/missing HP;
- action points;
- armor class;
- melee damage;
- carry weight;
- sequence;
- healing rate;
- critical chance;
- radiation and poison resistance;
- radiation and poison status values;
- crippled body-part flags;
- source field offsets and risks;
- parser warnings.

## JSON contract

The public JSON contract id is `combat_summary`.

Top-level fields:

- `game_kind`
- `slot_path`
- `read_only`
- `identity`
- `special`
- `hp`
- `action_points`
- `armor_class`
- `melee_damage`
- `carry_weight`
- `sequence`
- `healing_rate`
- `critical_chance`
- `resistances`
- `status_effects`
- `fields`
- `summary`
- `warnings`

## Safety

This command is read-only. It does not call patching, presets, or semantic recalculation.
