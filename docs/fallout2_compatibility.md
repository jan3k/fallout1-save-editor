# Fallout 2 compatibility

Fallout 2 support includes read-only inspection plus a limited semantic `set` path for an accepted subset of existing integer fields.

Run:

```bash
f1se compatibility --json
```

## Current status

| Capability | Fallout 1 | Fallout 2 |
|---|---|---|
| `detect` | supported | supported |
| `dump` | supported | read_only |
| `fields` | supported | read_only |
| `get` | supported | read_only |
| `inventory` | supported | read_only |
| `fallout2-writable-fields` | not_supported | read_only |
| `artifacts` | supported | partial |
| `map-summary` | supported | not_supported |
| `set` | supported | partial |
| `patch` | supported | not_supported |
| `preset` | supported | not_supported |
| `raw-read` | supported | partial |
| `raw-write` | unsafe | unsafe |
| `gui` | supported | read_only |

## Fallout 2 command examples

```bash
f1se detect SLOT01 --json
f1se detect SLOT01/SAVE.DAT --json
f1se dump SLOT01 --game auto --json
f1se fields SLOT01 --game fallout2 --json
f1se get SLOT01 pc.level --game fallout2
f1se inventory SLOT01 --game fallout2 --json
f1se fallout2-writable-fields SLOT01 --json
f1se set SLOT01 player.current_hp 45 --game fallout2
f1se set SLOT01 player.current_hp 45 --game fallout2 --write
f1se gui SLOT01
```

## GUI behavior

The Tkinter GUI can open Fallout 2 saves through `app_v11` in read-only mode. It shows overview, player fields, S.P.E.C.I.A.L., skills, traits, inventory, perks, kill counters, field schema, warnings and compatibility state.

GUI editing for Fallout 2 remains disabled.

## Set policy

Fallout 2 `set` is intentionally limited:

- dry-run is the default;
- `--write` is required to modify `SAVE.DAT`;
- a `.f1se-backups/` slot backup is created before a real modification;
- only accepted semantic integer fields are supported;
- batch patching, presets, item creation, item deletion and arbitrary raw offsets remain unsupported.

Use `f1se fallout2-writable-fields SLOT01 --json` to inspect the currently accepted field subset.
