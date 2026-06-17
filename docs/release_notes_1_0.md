# Release notes - 1.0

`f1se` 1.0 is the stable safe-editor milestone.

## Stable surfaces

- Public command names from `f1se commands --json`.
- Top-level public JSON keys from `f1se json-contracts --json`.
- Read-only diagnostics for artifacts, map summaries, global labels, raw blocks and fixture status.
- Guided fixed-width save edits with preview/backup/write gates.

## Safety boundaries

The 1.0 release does not claim semantic map object editing, quest editing, global variable editing, item insertion/removal or artifact rebuilding.

## Release checks

Before tagging:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m f1se smoke --json
PYTHONPATH=src python3 -m f1se release-audit --strict --json
```
