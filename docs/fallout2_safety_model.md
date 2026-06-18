# Fallout 2 safety model

Fallout 2 support is read-only by default and, in the current branch, read-only in full.

## Hard rules

- No Fallout 2 write support is implemented in this foundation phase.
- No `set`, `patch`, `preset`, semantic inventory mutation or GUI write path is enabled for Fallout 2.
- Existing Fallout 1 write behavior is preserved and continues to use the existing dry-run/backup model.
- Fallout 2 fields expose `writable: false` regardless of confidence.
- Fallout 2 inventory exposes existing objects only.
- New PID/object creation is forbidden.
- World-state, quest-state, map-object and arbitrary-section rewrites are forbidden.

## Confidence model

Fallout 2 fields carry confidence metadata:

- `high`: fixed-width field backed by common SAVE.DAT structure and local parser sanity checks;
- `medium`: known public/referenced layout but still requires curated real-save fixture coverage;
- `low`: exposed for diagnostics only; label or semantic meaning needs real fixture confirmation.

Confidence does not imply writability.

## Risk model

- `SAFE`: read-only field with plausible direct semantic meaning.
- `ADVANCED`: read-only field whose interpretation may have hidden engine or derived-state effects.
- `RAW`: read-only structural value that must not be mutated through a semantic command.

## Future write gate

Fallout 2 writes may only be considered after:

1. curated real fixtures exist for the affected field group;
2. JSON contracts cover the command payload;
3. release audit checks the write operation and fixture coverage;
4. CLI defaults to dry-run;
5. `--write` is required;
6. backup creation remains mandatory;
7. GUI write controls remain disabled until a separate review.

Initial write candidates, after proof, are limited to fixed-width fields such as base SPECIAL, skill points, current HP and XP. Perks, traits and inventory require extra review because they can have non-local engine effects.
