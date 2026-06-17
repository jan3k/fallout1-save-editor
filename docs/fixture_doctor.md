# Fixture doctor

`f1se fixture-doctor` performs read-only checks over the fixture corpus.

```bash
f1se fixture-doctor tests/fixtures --json
```

It checks manifest status, slot parseability, unexpected fixture files and per-slot verification issues.

The command does not modify fixtures.
