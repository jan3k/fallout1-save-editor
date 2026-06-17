# F12se parity matrix

F12se is a scope and UX reference for Fallout save editing. `f1se` deliberately uses a stricter safety model: source-aligned fields, fixture regression, clear risk labels and no semantic writes until the binary layout is proven.

## Positioning

`f1se` aims to be more advanced by exposing diagnostics, source alignment and byte-level confidence, while staying simpler for the user through guided SAFE/ADVANCED/RAW labels.

## Current matrix

Run:

```bash
f1se features --json
```

The feature matrix classifies each capability by:

- category;
- f1se status;
- F12se status note;
- risk level;
- CLI/GUI/MODEL/DOCS coverage;
- source alignment;
- fixture coverage.

## Where f1se is already stronger

- conservative write gates;
- byte-identical no-change round trips;
- fixture matrix;
- explicit source-aligned save handler registry;
- diagnostics for raw blocks, artifacts, map scan and global-state candidates;
- guided GUI safety workflow.

## Where f1se is intentionally behind

- quest/global semantic writes;
- add/remove inventory items;
- PID/FID/type mutation;
- map object writes;
- party/worldmap writes;
- `.SAV` and `AUTOMAP.SAV` rebuilds.

These gaps are deliberate until the implementation is source-aligned and fixture-covered.
