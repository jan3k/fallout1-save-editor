# Map summary

`f1se map-summary` is a read-only diagnostic command for map `.SAV` artifacts.

```bash
f1se map-summary tests/fixtures/SLOT01 --json
f1se map-summary tests/fixtures/SLOT01 --file V13ENT.SAV --json
```

The command summarizes known PID-like candidates already found by the map scan layer. It groups repeated PIDs and nearby regions to make map artifacts easier to inspect.

The output is not a semantic map parser and does not modify `SAVE.DAT`, `.SAV`, or `AUTOMAP.SAV`.
