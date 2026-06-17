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

Each key in `fixtures.json` is a slot directory under `tests/fixtures`:

```json
{
  "SLOT01": {
    "description": "Uploaded baseline save used for parser regression",
    "save_dat_size": 38155,
    "version": "1.02R",
    "player_name": "yay",
    "current_map_file": "V13ENT.sav",
    "function5_start": "0x88CC",
    "function6_start": "0x8B38",
    "inventory_count": 5,
    "kill_count_count": 15,
    "expected_artifacts": ["AUTOMAP.SAV", "V13ENT.SAV"],
    "expected_artifact_kinds": {
      "AUTOMAP.SAV": "AUTOMAP_SAV",
      "V13ENT.SAV": "MAP_SAV"
    }
  }
}
```

Hex strings are accepted for offsets. Counts are decimal integers.

Optional `expected_inventory` rows can assert existing inventory offsets, PIDs, sizes and quantities when the fixture is intended to protect inventory parser behaviour.

## Generating a manifest entry

Use `fixture-snapshot` to generate a JSON object for a real slot:

```bash
PYTHONPATH=src python3 -m f1se fixture-snapshot tests/fixtures/SLOT01 --name SLOT01 --json
```

Optional fields:

```bash
PYTHONPATH=src python3 -m f1se fixture-snapshot tests/fixtures/SLOT01 \
  --name SLOT01 \
  --description "Uploaded baseline save used for parser regression" \
  --include-sha256 \
  --include-warnings \
  --json
```

The command does not modify `fixtures.json`; copy the generated entry manually after reviewing it.

## Checking a fixture corpus

Use `fixture-check` to validate `fixtures.json` against real slot directories:

```bash
PYTHONPATH=src python3 -m f1se fixture-check tests/fixtures
PYTHONPATH=src python3 -m f1se fixture-check tests/fixtures --json
```

The command checks slot existence, `SAVE.DAT`, source anchors, header values, artifact names, artifact kinds, optional inventory rows and `SaveDat.verify()`.

## Adding a fixture

1. Add a complete real save slot directory under `tests/fixtures`.
2. Keep `SAVE.DAT` plus all slot artifacts that belong to the save, for example `.SAV` map files and `AUTOMAP.SAV`.
3. Run `f1se fixture-snapshot tests/fixtures/<SLOT> --name <SLOT> --json`.
4. Copy the generated manifest entry into `tests/fixtures/fixtures.json`.
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
- optional expected inventory rows match parser output;
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
