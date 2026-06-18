# Fallout 2 reference repositories

This document records the repositories consulted for the Fallout 2 read-only foundation. It is intentionally an implementation-audit document, not copied source code.

## Scope

The target project remains MIT. Fallout 2 support starts as detection and read-only parsing only. No GPL code was imported.

## `freesalu/fallout-2-editor`

- **License:** MIT.
- **Language/runtime:** Python 2.7.
- **Supported Fallout 2 surfaces:** header metadata, player status fields, base SPECIAL, skills, perks, and a small CLI around stats/skills/perks.
- **Detection/layout strategy:** find the Function 5 marker `00 00 46 50`, walk the player inventory, infer Function 6, then derive later stat/perk blocks from known sizes.
- **Representative offsets used as behavioral reference:**
  - header player name at `0x1D`;
  - save name at `0x3D`;
  - Function 5 current HP at `0x74`, radiation at `0x78`, poison at `0x7C`;
  - Function 6 base SPECIAL at `0x08..0x20`;
  - skills at Function 6 `0x0120`;
  - perks in the post-tag-skill/perk block.
- **Write behavior:** writes are applied directly to the mapped file when values are changed.
- **Limitations:** old runtime, narrow field coverage, known parsing failures on some late-game saves, no robust item editing workflow.
- **Use in this project:** behavioral reference only. No source was copied.

## `efossvold/fallout2-save-editor`

- **License:** GPL-3.0.
- **Language/runtime:** Wails application with TypeScript frontend and Go bridge.
- **Supported Fallout 2 surfaces:** attributes, skills, perks, traits, tag skills, HP, poison, radiation, injuries, miscellaneous derived stats, reputation and kill counts.
- **Detection/layout strategy:** Function 5 marker scan, inventory walk to Function 6, fixed Function 7/8/9 sizes, Function 13 PC stats, Function 15 traits, and preference scanning for later anchors.
- **Representative section assumptions:**
  - Function 6 size `0x178`;
  - Function 7 kill counters size `0x4C`;
  - Function 8 tag skills size `0x10`;
  - Function 9 perks size `0x02C8`;
  - Function 13 PC stats size `0x14`;
  - Function 15 traits size `0x08`.
- **Write behavior:** UI edits are saved back through the application bridge.
- **Limitations:** project documentation warns that saving creates no backup and the application is not extensively tested.
- **License risk:** GPL-3.0 is not copied into this MIT project. It is used only as a behavioral and format reference.

## `ali-raheem/fallout-se`

- **License:** MIT OR Apache-2.0.
- **Language/runtime:** Rust workspace with separate core/CLI/GUI/TUI/web crates.
- **Supported Fallout 2 surfaces:** auto-detection, JSON/debug views, selected field edits, inventory quantity edits, layout/section inspection, and save comparison.
- **Architectural value:** clean split between common code, Fallout 1 modules, Fallout 2 modules, layout code and frontends.
- **Important safety precedent:** does not treat new inventory-object creation as a trivial operation; object-graph editing remains constrained.
- **Use in this project:** architectural inspiration and test-surface inspiration. No source was copied.

## Licensing policy applied

- GPL-3.0 code from `efossvold/fallout2-save-editor` is not copied.
- MIT / Apache sources are used as references only unless a future change explicitly records attribution and compatibility in `docs/third_party_notes.md`.
- All Fallout 2 implementation in this branch is original Python code built around the existing f1se parser architecture.
