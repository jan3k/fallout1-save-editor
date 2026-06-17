# Global labels

`f1se global-labels` exposes read-only diagnostic labels for candidate global/script-state regions.

```bash
f1se global-labels --json
f1se global-labels --block 2 --json
f1se globals-scan tests/fixtures/SLOT01 --json
```

Labels describe broad source-order regions, not individual variables. Each label carries confidence and source notes.

Current labels are intentionally coarse:

- Function 2: primary script-state region;
- Function 4: secondary script-state region;
- Function 20: world or late-state region.

The label layer does not edit save files. It only adds context to scan output.
