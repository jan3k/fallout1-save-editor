# Roadmap

The roadmap keeps `f1se` more conservative than traditional save editors while moving toward broader feature coverage.

## Milestones

- `v0.11.0` - F12se feature parity matrix and guided roadmap.
- `v0.12.0` - real fixture corpus expansion and guided import workflow.
- `v0.13.0` - safer inventory UX for existing-item operations.
- `v0.14.0` - read-only quest/global naming groundwork.
- `v0.15.0` - map object deep scan.
- `v1.0.0` - stable safe editor.

## Risk classes

- `SAFE write` - fixed-width local edits with validators and tests.
- `ADVANCED write` - fixed-width fields with possible engine-side effects.
- `READ_ONLY` - parser visibility without write.
- `DIAGNOSTIC` - heuristic or structural inspection only.
- `EXPERIMENTAL` - operations that may alter structure or identity.
- `OUT_OF_SCOPE` - intentionally not planned until source and fixtures justify it.

## Fixture corpus workflow

`fixture-plan`, `fixture-status` and `fixture-import` make real save expansion repeatable. More real saves are required before adding high-risk editor features.

## Next priority

The next practical milestone is safer UX for existing player-inventory workflows, still limited to already-supported fixed-width fields.
