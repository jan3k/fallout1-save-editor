# Model API

The GUI-facing model exposes non-Tk payload helpers so diagnostics can be tested without X11 and reused by future GUI views.

Current diagnostic helpers include:

- `map_summary_payload()`
- `cli_commands_payload()`
- `backup_catalog_payload()`
- `restore_preview_payload(backup_name)`
- `slot_diff_payload(other_slot_path)`
- `smoke_payload()`
- `fixture_doctor_payload(fixture_root)`

These helpers expose existing project-layer logic without duplicating binary parsing in Tk code. Recovery preview and catalog helpers are read-only; actual restore remains a separate explicit write workflow in the CLI.
