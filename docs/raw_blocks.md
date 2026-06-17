# Raw block inspection

`f1se raw-blocks` is a read-only diagnostic command for preserved raw `SAVE.DAT` function blocks.

It does not assign quest names, global variable names, script meanings, or engine semantics. It only reports structural properties that are useful for regression testing and later reverse-engineering.

## CLI

```bash
f1se raw-blocks /path/to/SLOT
f1se raw-blocks /path/to/SLOT --json
```

The output includes:

- function block index and name;
- start/end offsets;
- byte size;
- SHA-256 of the block payload;
- parser status;
- zero ratio;
- i32 count;
- plausible i32 count;
- entropy hint;
- warnings.

## Entropy hints

Hints are deliberately coarse:

- `empty`;
- `mostly-zero`;
- `dense-i32-table`;
- `dense-binary`;
- `mixed-raw`.

They are not semantic labels. A block that looks like an integer table is not automatically a quest/global table.

## Fixture regression

`fixtures.json` can optionally include `expected_raw_blocks` to lock stable raw block boundaries. This protects parser anchor logic without requiring a full semantic parser.

## Safety boundary

Raw block inspection does not add write access. Raw writes remain available only through the explicit `raw-write --experimental --write` workflow.
