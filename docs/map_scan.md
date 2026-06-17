# Map scan

`f1se map-scan` is a read-only diagnostic command for map `.SAV` artifacts.

It looks for object-like candidates using conservative heuristics. A candidate is not proof of a real object, container, or inventory entry.

```bash
f1se map-scan /path/to/SLOT
f1se map-scan /path/to/SLOT --json
f1se map-scan /path/to/SLOT --file V13ENT.SAV --json
```

The command reports map file name, size, SHA-256, parser status, candidate count, candidate offsets, PID/FID hints, confidence, reasons, and warnings.

## Safety boundary

`map-scan` does not modify `SAVE.DAT`, `.SAV`, or `AUTOMAP.SAV`. It does not add, remove, move, or edit map objects, containers, or items.
