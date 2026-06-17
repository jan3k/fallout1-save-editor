# Slot artifacts

`f1se` treats non-`SAVE.DAT` files in a save slot as read-only artifacts. The first milestone for these files is classification and fingerprinting, not semantic editing.

## Artifact kinds

Current artifact kinds:

- `SAVE_DAT` - the main `SAVE.DAT` file; handled by the core parser.
- `AUTOMAP_SAV` - `AUTOMAP.SAV`; currently read-only/raw-fingerprint.
- `MAP_SAV` - map `.SAV` files such as `V13ENT.SAV`; currently read-only/raw-fingerprint plus optional heuristic read-only scan.
- `UNKNOWN` - any other slot-local file.

## CLI

```bash
f1se artifacts /path/to/SLOT
f1se artifacts /path/to/SLOT --json
f1se map-scan /path/to/SLOT --json
```

The artifact command reports file name, kind, size, SHA-256, parser status, and warnings. `map-scan` adds heuristic candidate discovery for map `.SAV` files without enabling writes.

## Parser status

`AUTOMAP.SAV` and map `.SAV` files currently use `raw-fingerprint`. Map scan output uses `heuristic-read-only` for candidate discovery. This means the file is recognized and inspected, but its internal structures are not interpreted as writable semantic data.

## Safety boundary

The artifact layer does not implement:

- map object editing;
- add/remove object;
- automap reveal/clear write;
- map variable write;
- `.SAV` rebuild;
- `AUTOMAP.SAV` rebuild.

These files remain byte-preserved slot artifacts. Artifact fingerprints are used by fixture regression tests to detect accidental slot changes.
