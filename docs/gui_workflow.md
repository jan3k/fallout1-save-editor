# GUI workflow

The GUI is a thin Tkinter layer over the same parser and writer used by the CLI.
It does not implement a second save format model.

## Guided editing

The normal workflow is:

1. Open a save slot.
2. Stage field changes in the editable tabs.
3. Use `Preview diff`.
4. Review offsets, old bytes, new bytes and risk labels.
5. Write changes only after confirmation.

Every normal write creates a slot backup before atomically replacing `SAVE.DAT`.

## Risk labels

Editable fields expose their risk level:

- `SAFE`
- `ADVANCED`
- `RAW`
- `EXPERIMENTAL`

Read-only diagnostic views use parser status labels such as:

- `read-only`
- `raw-fingerprint`
- `heuristic-read-only`

`ADVANCED` patches require additional acknowledgement because the engine may have side effects that are not fully emulated by the editor.

## Dirty state

The GUI model can summarize whether staged values differ from the current loaded `SAVE.DAT`, how many fields changed, and whether the staged patch is SAFE-only or includes ADVANCED fields.

`Reset Changes` restores form values from the currently loaded save and does not write files.

## Read-only diagnostics

The GUI exposes read-only diagnostic tabs for:

- slot artifacts;
- raw block inspection;
- global-state candidate scan;
- map scan.

These views are for inspection only and do not enable map, quest, global, worldmap, party, or container writes.

## RAW workflow

Raw writes stay separate from field editing and still require the explicit experimental acknowledgement.
