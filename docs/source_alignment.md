# Source alignment notes

## Fallout 1 engine references

The editor follows `alexbatalov/fallout1-ce` as the primary source for handler order and constants. `loadsave.cc` defines the `FALLOUT SAVE FILE` signature, 27 save/load handlers, and the save handler order used to label blocks.

`fallout1-re` is treated as the closer historical reverse-engineering reference. Its project goal is source restoration close to the original binary, so it is useful for checking naming and behaviour, while `fallout1-ce` remains more convenient for portable code references.

## Source-order registry

`src/f1se/format/function_registry.py` records the 27 Fallout 1 save/load handlers as metadata. Parser code uses this registry to label `FunctionBlock` ranges with source handler names, load handler names and a conservative writable policy.

The registry is not a serializer. It must not be used to rebuild `SAVE.DAT` from semantic objects. Unknown or partially understood ranges remain raw and must stay byte-identical on no-change round trips.

## Item metadata

`src/f1se/schema/items.py` contains read-only item metadata used by the parser and CLI. It is display and inference data only, not a serializer.

## Constants used in the editor

- `PRIMARY_STAT_MIN = 1`
- `PRIMARY_STAT_MAX = 10`
- `PRIMARY_STAT_COUNT = 7`
- `SAVEABLE_STAT_COUNT = 35`
- `PC_LEVEL_MAX = 21`
- `SKILL_COUNT = 18`
- `NUM_TAGGED_SKILLS = 4`
- `PC_TRAIT_MAX = 2`
- `TRAIT_COUNT = 16`
- `PERK_COUNT = 64`
- detected Fallout 1 kill counters in the fixture: `15`

## Trait handling

The source trait system stores two selected trait ids, where an empty slot is `-1`. The editor validates those ids and blocks duplicates. Runtime effects such as Gifted, Bruiser, Small Frame, Fast Metabolism, Good Natured and Skilled are shown as notes/static previews but are not blindly written into base stats.

## Fixture alignment

`tests/fixtures/fixtures.json` is the regression manifest for source-aligned parser anchors. At minimum each real fixture records Function 5 start, Function 6 start, inventory count, kill-count count, slot artifacts and stable header values.

When a parser change moves an anchor, the fixture manifest should only be updated with a short explanation in the change summary. Blindly updating expected offsets hides parser regressions.

## F12se-inspired UX decisions

F12se groups editing around save metadata, globals/quests, map/SAV files, world map, inventory/items, stats, skills/perks, kills, player status and raw/hex operations. `f1se` mirrors the useful grouping while keeping Fallout 1 source-derived field validation and round-trip byte preservation.

## Python 3 / Context7-aligned GUI choice

The GUI uses `tkinter` and `tkinter.ttk` from Python 3. The Tk import is lazy and happens only inside the GUI entrypoint, so parser/CLI tests still run on headless hosts. The rest of the code uses `argparse`, `dataclasses`, `pathlib` and explicit type annotations rather than framework-specific runtime magic.
