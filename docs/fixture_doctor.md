# Fixture doctor

`f1se fixture-doctor` performs read-only checks over the fixture corpus.

```bash
f1se fixture-doctor tests/fixtures --json
```

It checks manifest status, slot parseability, unexpected fixture files and per-slot verification issues.

The payload includes legacy `issues` and `warnings` arrays plus structured `findings` with severity, code, message and optional slot name.

The command does not modify fixtures.
