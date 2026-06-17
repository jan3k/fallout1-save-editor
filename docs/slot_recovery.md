# Slot recovery

`f1se backups SLOT --json` lists available slot backups.

`f1se restore-preview SLOT --backup NAME --json` previews files from a selected backup.

`f1se restore SLOT --backup NAME --write --json` copies a selected backup back into the slot after first creating a safety backup of the current slot.

The write command is explicit and should be tested on copied slots first.
