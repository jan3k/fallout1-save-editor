# Fixture matrix

`tests/fixtures/fixtures.json` is the parser-regression manifest for real Fallout 1 save slots.

The fixture matrix exists to prove that `f1se` can parse, validate and round-trip multiple real saves without rewriting unknown bytes. It is intentionally separate from semantic editor features: adding a fixture should not require implementing new writable fields.

## Directory layout

```text
测试/fixtures/
  fixtures.json
  SLOT01/
    SAVE.DAT
    AUTOMAP.SAV
    V13ENT.SAV
```

Use real save slots only. Do not invent synthetic binary save files unless the test is specifically checking rejection of malformed input.

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
    "expected_artifacts": ["AUTOMAP.SAV", "V13ENT.SAV"]
  }
}
```

Hex strings are accepted for offsets. Counts are decimal integers.

## Adding a fixture

1. Add a complete save slot directory under `tests/fixtures`.
2. Keep `SAVE.DAT` plus all slot artifacts that belong to the save, for example `.SAV` map files and `AUTOMAP.SAV`.
3. Run `f1se inspect tests/fixtures/<SLOT>` and record the stable parser anchors in `fixtures.json`.
4. Run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The fixture matrix checks:

- `SaveSlot.open()` succeeds;
- header values match the manifest;
- Function 5 and Function 6 anchors match the manifest;
- inventory count and kill-count count match the manifest;
- slot artifacts match the manifest;
- `verify()` returns no issues;
- no-change parse is byte-identical;
- all 27 source-order function blocks are monotonic and stay inside `SAVE.DAT`.

## Regression rule

If a parser change moves an expected offset, do not update `fixtures.json` blindly. First explain why the new anchor is more source-aligned or more correct than the previous one. Unknown bytes must remain byte-identical across no-change parses.
