# Fallout 1 character summary

`character-summary` is a read-only aggregate command for quick inspection of a Fallout 1 save slot.

```bash
f1se character-summary SLOT01
f1se character-summary SLOT01 --json
f1se character-summary SLOT01 --game auto --json
```

## Purpose

The command avoids forcing users to inspect dozens of raw field names when they only need the current state of the player character.

It does not mutate `SAVE.DAT`.

## JSON payload

The public JSON contract id is `character_summary`.

Top-level fields:

- `game_kind`
- `slot_path`
- `read_only`
- `identity`
- `progression`
- `status_effects`
- `special`
- `skills`
- `traits`
- `trait_effect_notes`
- `active_perks`
- `nonzero_kill_counts`
- `inventory_summary`
- `warnings`

## Included data

`identity` includes player name, save name, game version, current map, map id, elevation, save date and SAVE.DAT SHA-256.

`progression` includes level, XP, unspent skill points, reputation and karma.

`status_effects` includes current HP, max HP, poison, radiation and crippled-body-part flags.

`special` includes base, bonus, trait adjustment and effective static preview for each S.P.E.C.I.A.L. stat.

`skills` includes saved points-over-base and tag-skill markers.

`inventory_summary` includes parsed item count, known/unknown PID counts, total quantity and the largest item stacks.

## Safety

This command is read-only. It uses the existing Fallout 1 parser and field registry and does not introduce a new write path.
