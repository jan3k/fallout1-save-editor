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
| `artifacts` | supported | not_supported |
| `map-summary` | supported | not_supported |
| `set` | supported | not_supported |
| `patch` | supported | not_supported |
| `preset` | supported | not_supported |
| `raw-read` | supported | partial |
| `raw-write` | unsafe | unsafe |
| `gui` | supported | partial |

## Fallout 2 command examples

```bash
f1se detect SLOT01 --json
f1se detect SLOT01/SAVE.DAT --json
f1se dump SLOT01 --game auto --json
f1se fields SLOT01 --game fallout2 --json
f1se get SLOT01 pc.level --game fallout2
f1se inventory SLOT01 --game fallout2 --json
```

## Write policy

Fallout 2 writes are disabled in this phase. The compatibility matrix must not report `supported` for Fallout 2 `set`, `patch`, `preset` or semantic inventory writes until curated fixtures prove the exact offsets and invariants.
