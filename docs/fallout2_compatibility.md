# Fallout 2 compatibility

Fallout 2 support is intentionally introduced as a read-only compatibility layer.

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
| `artifacts` | supported | partial |
| `map-summary` | supported | not_supported |
| `set` | supported | not_supported |
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
f1se gui SLOT01
```

## GUI behavior

The Tkinter GUI can open Fallout 2 saves through `app_v11` in read-only mode. It shows:

- overview;
- player fields;
- S.P.E.C.I.A.L.;
- skills;
- traits;
- inventory;
- perks;
- kill counters;
- field schema with confidence;
- warnings;
- compatibility matrix.

Fallout 2 write controls are disabled. Raw read remains available for diagnostics, but raw write is blocked.

## Write policy

Fallout 2 writes are disabled in this phase. The compatibility matrix must not report `supported` for Fallout 2 `set`, `patch`, `preset` or semantic inventory writes until curated fixtures prove the exact offsets and invariants.
