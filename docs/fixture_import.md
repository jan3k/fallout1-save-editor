# Fixture import workflow

`f1se fixture-import` copies a real Fallout 1 save slot into the fixture corpus and writes a compatible `fixtures.json` manifest entry.

## Plan recommended fixtures

```bash
f1se fixture-plan
f1se fixture-plan --json
```

The plan lists baseline, combat, inventory, perks, status-effect, travel, transition, companion, late-game and negative fixtures.

## Check current corpus

```bash
f1se fixture-status tests/fixtures
f1se fixture-status tests/fixtures --json
```

The status command reports manifest count, present fixtures, missing recommended fixtures, coverage categories and a simple coverage score.

## Import a real save

Always start with dry-run:

```bash
f1se fixture-import /path/to/SLOT --fixture-root tests/fixtures --name SLOT02_AFTER_COMBAT --dry-run
```

Then write after reviewing the plan:

```bash
f1se fixture-import /path/to/SLOT --fixture-root tests/fixtures --name SLOT02_AFTER_COMBAT --write
```

Use `--force` only when intentionally replacing an existing fixture.

## Imported files

The import keeps:

- `SAVE.DAT`;
- `AUTOMAP.SAV`;
- map `.SAV` files.

It skips backup/cache files such as `.f1se-backups`, `*.bak` and `*.tmp`.

## Why this matters

Real fixtures are the safety net for future editor features. More real saves mean safer parser changes, stronger round-trip guarantees and clearer boundaries between SAFE, ADVANCED, READ_ONLY and EXPERIMENTAL functionality.
