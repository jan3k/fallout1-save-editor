# Inventory quantity workflow

`f1se inventory-editable` shows editable fixed-width player inventory fields.

```bash
f1se inventory-editable tests/fixtures/SLOT01 --json
f1se inventory-set-quantity tests/fixtures/SLOT01 --index 3 --quantity 20 --dry-run
```

The supported action is changing quantity for an existing inventory row through `inventory.<index>.quantity`.

Rules:

- quantity range: `1..999999`;
- `0` is refused;
- dry-run is default;
- write mode uses the existing patch model, backup and atomic `SAVE.DAT` replacement;
- map/container data is not part of this workflow.
