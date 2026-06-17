# Fixture matrix

`tests/fixtures/fixtures.json` is the parser-regression manifest for real Fallout 1 save slots.

The fixture matrix exists to prove that `f1se` can parse, validate and round-trip multiple real saves without rewriting unknown bytes. It is intentionally separate from semantic editor features: adding a fixture should not require implementing new writable fields.

## Directory layout

```text
tests/fixtures/
  fixtures.json
  SLOT01/
    SAVE.DAT
    AUTOMAP.SAV
    V13ENT.SAV
```

Use real save slots only. Do not invent synthetic binary save files unless the test is specifically checking rejection of malformed input.

## Guided commands

```bash
f1se fixture-plan --json
f1se fixture-status tests/fixtures --json
f1se fixture-import /path/to/SLOT --fixture-root tests/fixtures --name SLOT02_AFTER_COMBAT --dry-run
f1se fixture-import /path/to/SLOT --fixture-root tests/fixtures --name SLOT02_AFTER_COMBAT --write
f1se fixture-check tests/fixtures --json
```

`fixture-import` copies only relevant slot files: `SAVE.DAT`, `AUTOMAP.SAV` and map `.SAV` artifacts. It skips `.f1se-backups`, `*.bak` and `*.tmp`.

## Naming convention

Prefer descriptive, stable names:

```text
SLOT01_BASELINE
SLOT02_AFTER_COMBAT
SLOT03_BIG_INVENTORY
SLOT04_WITH_PERKS
SLOT05_POISON_RAD_CRIPPLED
SLOT06_WORLD_MAP_TRAVEL
SLOT07_MAP_TRANSITION
SLOT08_WITH_COMPANION
SLOT09_LATE_GAME
```

The existing `SLOT01` fixture keeps its historical name for compatibility.

## Manifest format

Each key in `fixtures.json` is a slot directory under `tests/fixtures` and records stable parser anchors, artifact names/kinds and optional inventory/raw/map assertions.

Hex strings are accepted for offsets. Counts are decimal integers.

Optional `expected_inventory` rows can assert existing inventory offsets, PIDs, sizes and quantities when the fixture is intended to protect inventory parser behaviour.

Optional `expected_raw_blocks` entries can assert raw block boundaries. Optional `expected_map_artifacts` entries can assert map artifact kind/status/size.

## Adding a fixture

1. Pick or create a real Fallout 1 save with the desired coverage.
2. Run `f1se fixture-import ... --dry-run`.
3. Review generated files and manifest entry.
4. Run `f1se fixture-import ... --write`.
5. Run `f1se fixture-check tests/fixtures --json`.
6. Run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The fixture matrix checks:

- `SaveSlot.open()` succeeds;
- header values match the manifest;
- Function 5 and Function 6 anchors match the manifest;
- inventory count and kill-count count match the manifest;
- slot artifacts match the manifest;
- artifact kinds match the manifest;
- optional raw/map/inventory expectations match parser output;
- `verify()` returns no issues;
- no-change parse is byte-identical;
- all 27 source-order function blocks are monotonic and stay inside `SAVE.DAT`.

## Recommended fixture corpus

The target corpus should eventually cover:

```text
tests/fixtures/
  SLOT01_BASELINE/
  SLOT02_AFTER_COMBAT/
  SLOT03_BIG_INVENTORY/
  SLOT04_WITH_PERKS/
  SLOT05_POISON_RAD_CRIPPLED/
  SLOT06_WORLD_MAP_TRAVEL/
  SLOT07_MAP_TRANSITION/
  SLOT08_WITH_COMPANION/
  SLOT09_LATE_GAME/
  SLOT10_CORRUPTION_NEGATIVE/
```

`SLOT10_CORRUPTION_NEGATIVE` should not be a fake normal save. Prefer negative tests that mutate a real fixture in memory or in a temporary directory.

## Regression rule

If a parser change moves an expected offset, do not update `fixtures.json` blindly. First explain why the new anchor is more source-aligned or more correct than the previous one. Unknown bytes must remain byte-identical across no-change parses.
