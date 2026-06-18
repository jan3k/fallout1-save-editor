# Third-party notes

This project remains MIT. This document records third-party repositories consulted for the Fallout 2 read-only foundation.

## Consulted repositories

| Repository | License | Use in this project |
|---|---|---|
| `freesalu/fallout-2-editor` | MIT | Behavioral reference for Fallout 2 Function 5/6/9 offsets and legacy editor limitations. No source copied. |
| `efossvold/fallout2-save-editor` | GPL-3.0 | Behavioral/layout reference only. No source copied or translated. |
| `ali-raheem/fallout-se` | MIT OR Apache-2.0 | Architecture and test-surface inspiration for multi-game support. No source copied. |

## GPL handling

`efossvold/fallout2-save-editor` is GPL-3.0. Its code must not be copied into this MIT repository unless the project explicitly changes its licensing posture. The current implementation uses original Python code and records only format-level observations in documentation.

## Direct code imports

No direct third-party code fragments were imported in the Fallout 2 read-only foundation.

If future changes directly move code, data tables or generated assets from any third-party source, the PR must document:

1. exact source path and commit;
2. license compatibility;
3. attribution text;
4. whether the copied material is code, data or documentation;
5. why a clean-room implementation was not used.
