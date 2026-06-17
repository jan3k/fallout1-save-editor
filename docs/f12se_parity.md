# F12se parity matrix

F12se is used as a scope and UX reference. `f1se` keeps stricter safety gates: source alignment, fixture regression, byte-identical no-change round trips and explicit risk classes.

## Current comparison

Run:

```bash
f1se features --json
```

The matrix shows category, f1se status, F12se note, risk level, interface coverage, source alignment and fixture coverage.

## Stronger in f1se

- explicit SAFE/ADVANCED/RAW/READ_ONLY/DIAGNOSTIC labels;
- fixture corpus and fixture import workflow;
- source-aligned handler registry;
- read-only diagnostics before risky writes;
- guided GUI safety workflow.

## Still behind by design

- semantic quest/global writes;
- item identity changes;
- map object/container writes;
- party/worldmap writes;
- `.SAV` and `AUTOMAP.SAV` rebuilds.

These gaps are deliberate until fixture coverage and source alignment are strong enough.
