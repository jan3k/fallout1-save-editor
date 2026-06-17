# fallout1-save-editor / `f1se`

Round-trip-safe Fallout 1 `SAVE.DAT` parser/editor for Linux with CLI and a stdlib Tkinter/ttk GUI.

The editor patches fixed-width fields in-place and preserves unknown bytes exactly. It does **not** rebuild a save from semantic objects.

## Current scope

Implemented:

- `SAVE.DAT` header and source-aligned 27 handler block registry;
- SAFE fixed-width editing for player stats, S.P.E.C.I.A.L., skills, traits, kills, PC stats and existing inventory quantities/ammo fields;
- guided quantity workflow for existing inventory rows;
- ADVANCED fixed-width editing for derived stats, raw perk ranks and selected lower-level fields;
- read-only inventory metadata, artifact fingerprints, raw block inspection, global-state candidate scan and map `.SAV` scan;
- CLI and guided Tkinter/ttk GUI with preview diff, backup, atomic write, raw-write experimental gate and ADVANCED acknowledgement;
- fixture matrix, fixture-check and no-change byte-identical round-trip tests;
- F12se-oriented feature matrix and roadmap.

Preserved raw, not fully semantic yet:

- global/script state;
- quest state;
- map objects and containers;
- worldmap and party;
- `.SAV` map files and `AUTOMAP.SAV` rebuilds.

## Commands

```bash
f1se inspect /path/to/SLOT
f1se dump /path/to/SLOT --json
f1se fields /path/to/SLOT
f1se inventory /path/to/SLOT --json
f1se inventory-editable /path/to/SLOT --json
f1se inventory-set-quantity /path/to/SLOT --index 3 --quantity 20 --dry-run
f1se inventory-set-quantity /path/to/SLOT --index 3 --quantity 20 --write
f1se artifacts /path/to/SLOT --json
f1se raw-blocks /path/to/SLOT --json
f1se globals-scan /path/to/SLOT --json
f1se map-scan /path/to/SLOT --json
f1se features --json
f1se features --category inventory --json
f1se features --status read-only --json
f1se fixture-snapshot /path/to/SLOT --name SLOT02_AFTER_COMBAT --json
f1se fixture-check tests/fixtures --json
f1se set /path/to/SLOT player.base_strength 10 --dry-run
f1se set /path/to/SLOT player.base_strength 10 --write
f1se patch /path/to/SLOT patch.json --dry-run
f1se patch /path/to/SLOT patch.json --write
f1se gui /path/to/SLOT
f1se raw-read /path/to/SLOT SAVE.DAT:0x8B40:4
f1se raw-write /path/to/SLOT SAVE.DAT:0x8B40:0000000A --experimental --write
```

`--dry-run` is the default behaviour for mutating commands unless `--write` is present.

## Project positioning vs F12se

F12se is treated as a useful UX and scope reference. `f1se` is intentionally more conservative in write operations:

- it separates `SAFE`, `ADVANCED`, `RAW`, `READ_ONLY`, `DIAGNOSTIC` and `EXPERIMENTAL` capabilities;
- it requires fixture coverage and source alignment before adding risky writes;
- it keeps unknown bytes byte-identical on no-change parses;
- it exposes diagnostic context instead of pretending every discovered value is semantically safe.

A missing write feature does not mean lack of ambition. It means the feature is not yet safe enough to expose as a friendly high-level editor action.

See:

- `docs/f12se_parity.md`
- `docs/roadmap.md`
- `docs/risk_levels.md`
- `docs/source_alignment.md`
- `docs/gui_workflow.md`
- `docs/inventory_workflow.md`

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Expected result: all tests pass with `OK`.

## Important fixture note

The included uploaded `SAVE.DAT` has all seven base S.P.E.C.I.A.L. fields already set to `10` at `0x8B40..0x8B58`. Older notes in the prompt described `3/5/5/10/10/5/2`; that does not match the bytes currently uploaded with this task.
