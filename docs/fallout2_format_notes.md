# Fallout 2 SAVE.DAT format notes

These notes describe the currently implemented read-only Fallout 2 assumptions.

## Detection anchors

The current detector uses a confidence-ranked probe:

1. parse the common `FALLOUT SAVE FILE` header;
2. search for the Function 5 marker `00 00 46 50`;
3. walk the existing inventory object list to locate Function 6;
4. validate the fixed-width Function 6 critter stats block;
5. check whether a Fallout 2-sized Function 7 block is followed by plausible Function 8 tag skills;
6. check for plausible Function 13 PC stats after Function 9 perks.

A score below the minimum threshold returns `UNKNOWN`.

## Implemented read-only sections

| Section | Size / location | Confidence | Notes |
|---|---:|---|---|
| Header | `0x0000..0x7563` | high | Shared Fallout 1/2 header parser. |
| Function 5 player object | FP marker to Function 6 | high/medium | Inventory walk still needs more real Fallout 2 fixtures. |
| Function 6 critter stats | `0x178` | high | Base SPECIAL, derived base stats, bonus SPECIAL and skills. |
| Function 7 kill counts | `0x4C` | medium | 19 counters, labels exposed as stable indices when unknown. |
| Function 8 tag skills | `0x10` | medium | Four skill ids. |
| Function 9 perks | `0x02C8` | medium | 178 raw perk ranks; semantic side effects are not modeled. |
| Function 13 PC stats | `0x14` | medium/low | Skill points, level and XP are exposed; later offsets remain conservative. |
| Function 15 traits | `0x08` | medium | Two trait ids. |

## Implemented read-only field groups

- `player.base_<special>` from Function 6 `0x08..0x20`.
- `player.current_hp` from Function 5 `0x74`.
- `player.radiation` from Function 5 `0x78`.
- `player.poison` from Function 5 `0x7C`.
- `player.base_hitpoints` from Function 6 `0x24`.
- `skills.<skill>` from Function 6 `0x0120`.
- `pc.skill_points`, `pc.level`, `pc.experience` from Function 13 `0x00`, `0x04`, `0x08`.
- `traits.0`, `traits.1` from Function 15.
- `perks.*` as raw ranks from Function 9.
- `kill_counts.*` as stable indexed counters from Function 7.
- `inventory.N.quantity` and `inventory.N.pid` for existing inventory objects only.

## Explicit non-goals in this phase

- no Fallout 2 writes;
- no quest/global/world-state editing;
- no map object editing;
- no new inventory object creation;
- no arbitrary section rewrite;
- no guarantee that every real Fallout 2 variant or modded save maps cleanly yet.
