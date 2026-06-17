# JSON payload contracts

`f1se json-contracts --json` lists stable top-level keys for public JSON payloads.

```bash
f1se json-contracts --json
```

Contracts currently cover:

- `features --json`
- `commands --json`
- `inventory-editable SLOT --json`
- `map-summary SLOT --json`
- `global-labels --json`
- `globals-scan SLOT --json`
- `fixture-status FIXTURES --json`

The contracts are intentionally shallow. They define required top-level keys so future refactors can avoid breaking public automation.
