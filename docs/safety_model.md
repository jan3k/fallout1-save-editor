# Safety model

`f1se` separates visibility from edit permission.

## Safe edits

Safe edits are fixed-width local fields with validators and tests.

## Advanced edits

Advanced edits are fixed-width fields that can have engine-side consequences. GUI workflows require extra acknowledgement for these fields.

## Diagnostics

Diagnostics expose structure, labels, candidates and summaries. Diagnostic visibility does not create edit permission.

## Explicit byte workflow

Byte-level operations remain explicit and gated. They are not hidden behind friendly semantic commands.

## Release rule

A new high-level edit should require source alignment, fixture coverage, validators, dry-run behavior, backup behavior and tests.
