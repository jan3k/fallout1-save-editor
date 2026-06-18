# Fallout 1 progression summary

`progression` is a read-only command that summarizes level progression and perk cadence for a Fallout 1 save slot.

```bash
f1se progression SLOT01
f1se progression SLOT01 --json
f1se progression SLOT01 --game auto --json
```

## Purpose

The command answers the common progression questions without requiring manual `get` calls:

- current level;
- current XP;
- XP threshold for the current level;
- next level and XP required;
- unspent skill points;
- karma and reputation;
- selected traits;
- next perk level and XP threshold.

## Fallout 1 XP formula

The command uses the Fallout 1 cumulative XP threshold formula:

```text
threshold(level) = ((level - 1) * level / 2) * 1000
```

Examples:

| Level | XP threshold |
|---:|---:|
| 1 | 0 |
| 2 | 1000 |
| 3 | 3000 |
| 4 | 6000 |
| 21 | 210000 |

## Perk cadence

Default perk cadence is every 3 levels. If the selected traits include `skilled`, the command reports a 4-level interval.

The command is diagnostic only. It does not add perks, change XP, or rewrite the save.

## JSON contract

The public JSON contract id is `progression`.

Top-level fields:

- `game_kind`
- `slot_path`
- `read_only`
- `identity`
- `level`
- `experience`
- `skill_points`
- `karma`
- `reputation`
- `traits`
- `perk_cadence`
- `warnings`
