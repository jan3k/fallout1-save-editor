# Versioning

The package uses Python-compatible pre-1.0 version numbers.

Current policy:

- `0.x` releases may still refine public JSON details.
- Public top-level JSON keys are protected by `json-contracts` tests.
- CLI command names listed by `f1se commands --json` should remain stable unless a release note says otherwise.
- Patch-level formatting may vary while the project remains pre-1.0.

Before a stable release, run:

```bash
f1se release-audit --json
f1se release-audit --strict --json
```
