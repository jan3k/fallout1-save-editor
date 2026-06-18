# Nested JSON contracts

Version 1.6 adds shallow nested contract samples for selected public JSON payloads.

The nested checker is intentionally limited. It validates representative nested objects and summaries without freezing every heuristic field.

Current nested paths include:

- `commands.commands[]`
- `release_audit.checks[]`
- `fixture_doctor.findings[]`
- `fixture_coverage.expansion_plan[]`
- `fixture_coverage.summary`
- `save_diff.summary`

Use:

```python
from f1se.project.json_contracts import validate_nested_payload_types

issues = validate_nested_payload_types(payload, "commands")
```

The catalog exposed by `f1se json-contracts --json` includes `nested_field_types` next to top-level `field_types`.
