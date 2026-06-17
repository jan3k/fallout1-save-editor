# fallout1-save-editor / `f1se`

Round-trip-safe Fallout 1 `SAVE.DAT` parser/editor for Linux with CLI and a stdlib Tkinter/ttk GUI.

The editor patches fixed-width fields in-place and preserves unknown bytes exactly. It does **not** rebuild a save from semantic objects.

## Current scope

Implemented:

- full slot discovery for `SAVE.DAT`, `.SAV`, `AUTOMAP.SAV` fingerprints;
- typed read-only slot artifact classification for `AUTOMAP.SAV`, map `.SAV`, and unknown files;
- `SAVE.DAT` header parser;
- source-aligned registry for the 27 Fallout 1 load/save handlers;
- read-only raw block structural inspection;
- read-only global/script-state candidate discovery;
- read-only map `.SAV` candidate discovery;
- dynamic `Function 5` detection by `00 00 46 50` / `FP`;
- dynamic inventory item-size inference for Function 5;
- read-only item/proto metadata for known Fallout 1 PIDs;
- inventory confidence metadata for known-vs-heuristic item parsing;
- `Function 6` critter/player stats parser;
- Function 7 kill-count field registry and SAFE editing;
- SAFE editing for:
  - S.P.E.C.I.A.L. base values,
  - stat bonuses,
  - HP/radiation/poison,
  - crippled body-part bitfield,
  - skill points over base,
  - tag skills,
  - traits,
  - PC skill points, level, XP, reputation, karma,
  - inventory quantity and known ammo/charges fields;
- trait-effect metadata from Fallout 1 source logic;
- static effective S.P.E.C.I.A.L. preview: base + bonus + always-on trait adjustments;
- guided GUI safety model with read-only diagnostics, dirty-state summaries, and ADVANCED write acknowledgement;
- conservative built-in presets: `max-special`, `heal`, `clear-crippled`;
- raw perk-rank editing as `ADVANCED`;
- partial options field registry;
- raw read/write with explicit `--experimental` gate;
- backup before write;
- atomic write via temp file + fsync + rename;
- no-change round-trip tests;
- fixture matrix for multi-save parser regression;
- fixture snapshot CLI for generating manifest entries;
- fixture check CLI for validating fixture manifests;
- `f1se inventory` read-only inventory/proto view;
- `f1se artifacts` read-only slot artifact view;
- `f1se gui` Tkinter/ttk GUI over the same parser/writer.

Preserved raw, not fully semantic yet:

- global vars/scripts/maps before Function 5,
- combat block,
- queue/event state,
- automap state inside `SAVE.DAT`,
- late worldmap/Pip-Boy/movie/skill-use/party/interface substructure,
- `.SAV` map files and `AUTOMAP.SAV` beyond fingerprint/backup/raw preservation.

## Install / run from source

```bash
cd fallout1-save-editor
PYTHONPATH=src python3 -m f1se inspect tests/fixtures/SLOT01
```

Optional editable install:

```bash
python3 -m pip install -e .
f1se inspect /path/to/SLOT01
```

Python 3.12+ is recommended.

## Commands

```bash
f1se inspect /path/to/SLOT
f1se dump /path/to/SLOT --json
f1se fields /path/to/SLOT
f1se inventory /path/to/SLOT
f1se inventory /path/to/SLOT --json
f1se artifacts /path/to/SLOT
f1se artifacts /path/to/SLOT --json
f1se raw-blocks /path/to/SLOT --json
f1se globals-scan /path/to/SLOT --json
f1se map-scan /path/to/SLOT --json
f1se fixture-snapshot /path/to/SLOT --name SLOT02_AFTER_COMBAT --json
f1se fixture-check tests/fixtures --json
f1se get /path/to/SLOT player.base_strength
f1se set /path/to/SLOT player.base_strength 10 --dry-run
f1se set /path/to/SLOT player.base_strength 10 --write
f1se patch /path/to/SLOT patch.json --dry-run
f1se patch /path/to/SLOT patch.json --write
f1se preset /path/to/SLOT max-special --dry-run
f1se preset /path/to/SLOT heal --write
f1se preset /path/to/SLOT clear-crippled --write
f1se effective /path/to/SLOT --json
f1se backup /path/to/SLOT
f1se verify /path/to/SLOT
f1se gui /path/to/SLOT
f1se raw-read /path/to/SLOT SAVE.DAT:0x8B40:4
f1se raw-write /path/to/SLOT SAVE.DAT:0x8B40:0000000A --experimental --write
```

`--dry-run` is the default behaviour for mutating commands unless `--write` is present.

## GUI

Launch:

```bash
./f1se gui /path/to/SLOT01
# or, after editable install:
f1se gui /path/to/SLOT01
```

The GUI is intentionally a thin Tkinter/ttk layer over the existing parser/writer. It exposes guided previews, risk labels, dirty-state summaries and read-only diagnostic tabs for artifacts, raw blocks, global scan and map scan.

GUI writes still create a slot backup before atomically replacing `SAVE.DAT`. Patches that include `ADVANCED` fields require an additional acknowledgement. Raw writes require an explicit EXPERIMENTAL checkbox and confirmation.

See `docs/gui_workflow.md` for details.

## Tests

```bash
cd fallout1-save-editor
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Expected result: all tests pass with `OK`.

## Risk levels

- `SAFE`: fixed-width value, local edit, conservative validator.
- `ADVANCED`: fixed-width but likely has derived or engine-side effects.
- `EXPERIMENTAL`: structure length or object identity can change; currently mostly gated to raw operations.
- `RAW`: unknown bytes; read by default, write only via explicit raw workflow.

## Important fixture note

The included uploaded `SAVE.DAT` has all seven base S.P.E.C.I.A.L. fields already set to `10` at `0x8B40..0x8B58`. Older notes in the prompt described `3/5/5/10/10/5/2`; that does not match the bytes currently uploaded with this task.
