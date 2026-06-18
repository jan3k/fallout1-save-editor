# Recovery hardening

Version 1.2 strengthens the slot backup and recovery workflow.

## Backup manifest

`f1se backup SLOT --json` now creates a checksum manifest inside the backup directory.

```bash
f1se backup /path/to/SLOT --json
f1se backups /path/to/SLOT --json
```

## Preview before write

`restore-preview` reports files, source checksums, destination checksums and a small diff summary.

```bash
f1se restore-preview /path/to/SLOT --backup BACKUP_NAME --json
```

## Restore behavior

`restore` still requires explicit `--write` and creates a safety backup before copying files from the selected backup.
