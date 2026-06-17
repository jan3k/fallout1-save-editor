# State discovery

This document covers the read-only `globals-scan` command and the read-only label layer.

```bash
f1se globals-scan /path/to/SLOT --json
f1se global-labels --json
```

The output is diagnostic only and does not modify save files. Labels describe broad candidate regions with confidence and source notes; they are not individual variable names.
