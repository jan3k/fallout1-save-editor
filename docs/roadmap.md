# Roadmap

The roadmap keeps `f1se` conservative in writes while expanding coverage through source alignment and real fixtures.

## Milestones

- `v0.11.0` - F12se feature parity matrix and guided roadmap.
- `v0.12.0` - real fixture corpus expansion and guided import workflow.
- `v0.13.0` - safer existing-inventory UX and item quantity workflows.
- `v0.14.0` - read-only quest/global naming groundwork.
- `v0.15.0` - map object deep scan.
- `v1.0.0` - stable safe editor.

## Risk classes

- `SAFE write` - fixed-width local edits with validators and tests.
- `ADVANCED write` - fixed-width fields with possible engine-side effects.
- `READ_ONLY` - parser visibility without write.
- `DIAGNOSTIC` - heuristic or structural inspection only.
- `EXPERIMENTAL` - operations that may alter structure or identity.

## Current priority

Expand the real fixture corpus. The fixture import workflow makes this repeatable and reviewable.
