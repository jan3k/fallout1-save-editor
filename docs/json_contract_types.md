# JSON contract types

Version 1.5 adds shallow top-level type hints to the JSON contract catalog.

```bash
f1se json-contracts --json
```

Each contract row includes `field_types` beside required and optional keys.

The checker validates public top-level fields only. It does not freeze nested diagnostic details.

Supported type names: `str`, `int`, `bool`, `list`, `dict`, `number`.
