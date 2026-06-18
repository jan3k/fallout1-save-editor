# Fixture corpus expansion

Version 1.4 adds read-only planning for future fixture corpus growth.

## Coverage command

```bash
f1se fixture-coverage tests/fixtures --json
```

The payload includes:

- current fixture status;
- recommended fixture rows;
- missing recommended fixtures;
- current coverage categories;
- missing coverage categories;
- a prioritized expansion plan.

## Doctor findings

`fixture-doctor` now includes structured findings. Each finding has:

- `severity`: `error`, `warning`, or `info`;
- `code`: stable machine-readable category;
- `message`: human-readable detail;
- optional `slot`.

## Policy

Do not commit private real saves into the repository without review. Use the coverage plan to identify what kind of save is needed, then import curated test fixtures deliberately.
