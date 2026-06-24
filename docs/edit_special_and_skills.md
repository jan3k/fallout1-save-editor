# Editing S.P.E.C.I.A.L. and skills

The editor exposes convenience wrappers for common character edits:

```bash
f1se special-set SLOT01 str 10 --game auto
f1se special-set SLOT01 strength 10 --game fallout1 --write
f1se special-set SLOT01 agility 9 --game fallout2 --write
```

```bash
f1se skill-set SLOT01 retoryka 120 --game auto
f1se skill-set SLOT01 speech 120 --game fallout1 --write
f1se skill-set SLOT01 retoryka 120 --game fallout2 --write
```

## Dry-run by default

Both commands default to dry-run. Add `--write` to modify `SAVE.DAT`.

Before a real modification the editor creates a `.f1se-backups/` backup directory inside the slot.

## S.P.E.C.I.A.L. aliases

Accepted examples:

- `str` / `strength`
- `per` / `perception`
- `end` / `endurance`
- `cha` / `charisma`
- `int` / `intelligence`
- `agi` / `agility`
- `luc` / `luck`

Default accepted range is `1..10`. `--allow-out-of-range` enables debug values in a wider internal range.

## Skill aliases

Skill fields use internal names from `skills.*`. For Speech/Retoryka you can use:

- `retoryka`
- `retoryki`
- `mowa`
- `speech`

Example:

```bash
f1se skill-set SLOT01 retoryka 120 --game auto --write
```

## Important note about skill values

The `skills.*` fields store saved points over the base formula, not necessarily the final displayed percentage after all engine modifiers.

This mirrors the existing field schema where `skills.speech` is described as saved points over base.
