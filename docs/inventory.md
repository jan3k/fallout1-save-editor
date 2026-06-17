# Inventory metadata

`f1se` parses the player's Function 5 inventory without rebuilding the save file. Existing item quantities and known ammo/charge fields can still be edited through fixed-width field patches, but item identity and list structure remain out of scope.

## Read-only item/proto metadata

Known Fallout 1 item ids are described in `src/f1se/schema/items.py` as `ItemProtoMeta` records:

- `pid`
- display `name`
- `type_name`
- serialized inventory `save_size`
- `source`
- `notes`

This metadata is used for display and safer item-size inference. It does not make changing PID, FID, type, scripts, or inventory list length safe.

## Known vs heuristic parsing

`ParsedInventoryItem` exposes:

- `known_pid`
- `size_source`
- `confidence`
- `item_meta`

Known PIDs use the curated item metadata and have `confidence = high`. Unknown PIDs use the existing conservative size probing path and are marked as heuristic with lower confidence.

## CLI

```bash
f1se inventory /path/to/SLOT
f1se inventory /path/to/SLOT --json
```

The JSON output includes offsets, quantity, PID, known/unknown status, item type, display name, serialized size, ammo/charge fields, raw fields and warnings.

## Safety boundary

These remain outside the high-level editor scope:

- add item;
- remove item;
- change PID;
- change FID;
- change item type;
- rebuild inventory;
- object script/local-var editing.

Those operations can alter object identity or serialized structure length and remain `EXPERIMENTAL`/raw-only until backed by more real fixtures and source-aligned parser coverage.
