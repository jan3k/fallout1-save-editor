# Release checklist

Use the audit command before cutting a stable build:

```bash
f1se release-audit --json
f1se release-audit --strict --json
```

Required checks before a stable release:

- CI is green.
- Public CLI index exists.
- Important JSON payload contracts are present.
- Risk surface is explicit.
- Byte-level commands remain explicit and gated.
- Fixture checks pass.

Normal audit mode allows warnings. Strict mode treats warnings as release-candidate blockers.

The audit command is read-only and does not inspect or modify user save files unless a caller separately runs slot-specific commands.
