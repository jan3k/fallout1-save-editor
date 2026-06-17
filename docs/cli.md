# CLI contract

`f1se commands --json` exposes the public command index used by regression tests.

```bash
f1se commands
f1se commands --json
```

The index is not a new editor feature. It is a compatibility surface for the existing CLI so future wrapper consolidation can be tested safely.

The command list includes read-only diagnostics, fixture tooling, guided fixed-width patch workflows and explicit raw commands. Existing command behavior is delegated to the previous CLI implementation.
