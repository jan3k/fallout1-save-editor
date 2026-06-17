# Save diff

`f1se diff` compares two save slots without modifying either slot.

```bash
f1se diff tests/fixtures/SLOT01 tests/fixtures/SLOT01 --json
```

The payload includes field differences, artifact differences and function-block hash differences.

The command is intended for diagnostics and regression work, not for patch generation.
