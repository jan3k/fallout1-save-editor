# CLI router

`f1se` keeps historical command wrappers for compatibility, but final production-facing commands are now routed through `f1se.cli_router`.

The router provides:

- explicit command handler table;
- fallback to the previous CLI chain;
- regression coverage for router-level commands;
- no change to legacy command behavior.

Current router-owned commands include:

- `smoke`
- `fixture-doctor`
- `diff`
- `backups`
- `restore-preview`
- `restore`

The goal is incremental cleanup, not a risky full rewrite of every historical CLI wrapper.
