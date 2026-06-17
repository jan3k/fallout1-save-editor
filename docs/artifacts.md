# Slot artifacts

`f1se` treats non-`SAVE.DAT` files in a save slot as read-only artifacts. The first milestone for these files is classification and fingerprinting, not semantic editing.

## Artifact kinds

Current artifact kinds:

- `SAVE_DAT` - the main `SAVE.DAT` file; handled by the core parser.
- `AUTOMAP_SAV` - `AUTOMAP.SAV`; currently read-only/raw-fingerprint.
- `MAP_SAV` - map `.SAV` files such as `V13ENT.SAV`; currently read-only/raw-fingerprint.
- `UNKNOWN` - any other slot-local file.

## CLI

```bash
f1se artifacts /path/to/SLOT
f1se artifacts /path/to/SLOT --json
```

The command reports:

- file name;
- artifact kind;
- size;
- SHA-256;
- parser status;
- warnings.

## Parser status

`AUTOMAP.SAV` and map `.SAV` files currently use `raw-fingerprint`. This means the file is recognized and fingerprinted, but its internal structures are not interpreted as writable semantic data.

## Safety boundary

The artifact layer does not implement:

- map object editing;
- add/remove object;
- automap reveal/clear write;
- map variable write;
- `.SAV` rebuild;
- `AUTOMAP.SAV` rebuild.

These files remain byte-preserved slot artifacts. Artifact fingerprints are used by fixture regression tests to detect accidental slot changes.
