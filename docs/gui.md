# GUI notes

`f1se gui` is a stdlib Tkinter/ttk interface over the same parser and writer used by the CLI. It does not implement independent binary save logic.

## Launch

```bash
./f1se gui /path/to/SLOT01
```

or after installation:

```bash
f1se gui /path/to/SLOT01
```

## Source/community-inspired layout

The layout borrows the F12se idea of grouped editor sections for savegame overview, player values, stats, skills, perks, kill counts, items, settings/options, raw/hex and validation. Only fields already registered by the Fallout 1 parser are writable.

## Tabs

- **Overview**: slot metadata, header fields, function-block offsets and parser status.
- **Player**: current HP, radiation, poison, crippled body parts, PC skill points, level, XP, reputation, karma, coordinates and facing.
- **S.P.E.C.I.A.L.**: base stats, bonus stats, derived stats and static effective preview based on always-on trait adjustments.
- **Skills**: 18 saved skill points-over-base plus four tag skill slots.
- **Traits**: two trait slots with enum names and effect notes from Fallout 1 source behaviour.
- **Inventory**: item list plus editable quantity/ammo/known fields.
- **Perks**: raw rank editor for Fallout 1 perk slots.
- **Kills**: Function 7 kill counters exposed as source-order indices.
- **Options**: partial `save_options` field registry.
- **Fields**: complete field registry with offsets, sizes, risk levels and writability.
- **Raw**: explicit raw read/write workflow with EXPERIMENTAL acknowledgement.
- **Validation**: `verify` output, warnings and byte diff previews.

## Write model

The GUI uses staged patches:

1. collect edited field values,
2. apply them to a cloned `SaveDat`,
3. show byte-range diffs,
4. on write, create a full slot backup,
5. atomically replace `SAVE.DAT`.

The GUI therefore keeps the same safety properties as CLI `set`/`patch`.

## Runtime dependency

Tkinter is part of the Python standard-library interface to Tcl/Tk, but Linux distributions may package the Tk runtime separately. On Debian/Ubuntu install `python3-tk` if `python3 -m tkinter` fails.
