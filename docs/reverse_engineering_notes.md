# Reverse engineering notes

## Source-of-truth priority

1. `alexbatalov/fallout1-ce` source code for handler order and constants.
2. Local fixture bytes.
3. `nousrnam/F12se` as community UX/reference editor inspiration, especially grouped pages for player, stats, skills, perks, kills, inventory, options and raw/hex workflows.
4. `aleitner/fse` as a small CLI reference.
5. Vault-Tec Labs/FalloutMods documentation as field map, with Fallout 1 vs Fallout 2 differences checked before using counts.

## Current uncertainties

- The pre-Function-5 region contains variable script/global/map data. v0.1 preserves it raw and exposes coarse function blocks only.
- Fallout 1 kill-count block in the uploaded fixture resolves to 15 counters before valid tag skills. The editor now exposes them as `kill_counts.kill_type_00..14`; user-facing localized labels are still intentionally not guessed.
- Combat block is inferred from the PC-stats anchor. It is preserved raw.
- Queue/event entries are not semantically parsed.
- `AUTOMAP.SAV` and map `.SAV` files are fingerprinted and backed up, but not semantically edited.
- Late blocks after options are split heuristically; bytes are preserved exactly.

## Fixture discrepancy

The task prompt contained an earlier report with base S.P.E.C.I.A.L. values `3/5/5/10/10/5/2`. The `SAVE.DAT` file uploaded with this run currently contains `10/10/10/10/10/10/10` at the same offsets. Tests and fixture report follow the uploaded bytes.

## Next semantic targets

- Full queue parser from `queue.cc`.
- Worldmap parser from `worldmap.cc`.
- Automap parser from `automap.cc` plus standalone `AUTOMAP.SAV`.
- Party parser from `party.cc`.
- Semantic perk application compatible with engine-side `perk_add_effect` logic.
- More complete trait/skill effective-value calculation, including dynamic Night Person time-of-day behaviour.
- PRO/DAT-backed item PID database instead of a small curated PID map.
