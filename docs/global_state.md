# Global state discovery

`f1se globals-scan` is a read-only discovery command for raw `SAVE.DAT` regions that may contain global or script state data.

It is not a quest editor and it does not claim semantic truth about individual values.

## CLI

```bash
f1se globals-scan /path/to/SLOT
f1se globals-scan /path/to/SLOT --json
```

The command reports candidate regions with:

- source-order block index and name;
- offset range;
- i32 count;
- nonzero i32 count;
- min/max i32 value;
- confidence;
- notes.

## Confidence

Confidence is intentionally conservative:

- `medium` means a raw source-order block has enough integer-like data to be useful for further reverse-engineering;
- `low` means the block is low-signal or likely mixed with other raw state;
- `unknown` means there is not enough aligned data to inspect.

Confidence does not identify a quest, global variable, script, map state, or engine object.

## Safety boundary

`globals-scan` is read-only. It does not implement edits for global variables, quests, scripts, maps, worldmap, or party data.

Any future semantic write path must be backed by source alignment, fixtures, exact byte-diff tests and explicit risk classification.
