# Release checklist

Use the audit command before cutting a stable build:

```bash
f1se release-audit --json
```

Required checks before a stable release:

- CI is green.
- Public CLI index exists.
- Important JSON payload contracts are present.
- Risk surface is explicit.
- Raw writes remain explicit and gated.
- Fixture checks pass.

The audit command is read-only and does not inspect or modify user save files unless a caller separately runs slot-specific commands.
