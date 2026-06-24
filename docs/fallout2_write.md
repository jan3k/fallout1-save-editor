# Fallout 2 semantic set

Fallout 2 support now includes a limited semantic `set` path for existing fixed-width integer fields.

## List accepted fields

```bash
f1se fallout2-writable-fields SLOT01
f1se fallout2-writable-fields SLOT01 --json
f1se fallout2-writable-fields SLOT01 --allow-advanced --json
```

## Dry-run first

`set` defaults to dry-run. It prints the planned byte diff and does not modify `SAVE.DAT`.

```bash
f1se set SLOT01 player.current_hp 45 --game fallout2
f1se set SLOT01 player.current_hp 45 --game fallout2 --json
```

## Real save modification

Use `--write` to actually update the save. A `.f1se-backups/` slot backup is created first.

```bash
f1se set SLOT01 player.current_hp 45 --game fallout2 --write
```

## Accepted safe field groups

- `player.current_hp`
- `player.radiation`
- `player.poison`
- `player.crippled_body_parts`
- `player.base_*`
- `skills.*`
- `kill_counts.*`
- `tag_skills.*`
- `traits.*`
- `pc.skill_points`
- `pc.level`
- `pc.experience`

## Advanced fields

Some fields require `--allow-advanced`, for example raw perk ranks and bonus/derived stat fields.

```bash
f1se set SLOT01 perks.awareness 1 --game fallout2 --allow-advanced --write
```

## Still blocked

The semantic path does not support object graph edits such as item identity/PID edits, item creation, item deletion, arbitrary raw offsets, or batch patching.

Use the writable-field catalog to see the current accepted subset.
