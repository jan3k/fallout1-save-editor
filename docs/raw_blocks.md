# Block inspection

`f1se raw-blocks` is a read-only diagnostic command for preserved `SAVE.DAT` function blocks.

It reports offsets, size, hash, parser status, zero ratio, aligned integer counts, a coarse hint, and warnings.

```bash
f1se raw-blocks /path/to/SLOT
f1se raw-blocks /path/to/SLOT --json
```

The command does not edit save files.
