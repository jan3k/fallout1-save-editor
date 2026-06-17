# Risk levels

Risk levels describe write safety. They are independent from parser visibility: a field can be visible in the UI and still remain `ADVANCED`, `EXPERIMENTAL` or raw-preserved.

Read-only metadata, such as known item/proto names, inventory parser confidence, slot artifact fingerprints, raw block discovery and GUI diagnostic payloads, does not change a field or file's write safety.

## SAFE

Fixed-width fields with local byte edits and conservative validation:

- base S.P.E.C.I.A.L. values,
- S.P.E.C.I.A.L. bonus values,
- current HP/radiation/poison,
- saved skill points over base,
- tag skill ids,
- trait ids,
- PC skill points, level, XP, reputation, karma,
- kill counters,
- inventory quantity for existing items,
- known ammo/charges values for existing entries.

A `SAFE` edit must be covered by tests showing the changed byte range is local and fixed-width.

## ADVANCED

Fixed-width fields that can have engine-side consequences or derived-stat mismatch:

- derived stats,
- raw perk ranks,
- inventory ammo type,
- player facing/coordinates/map level,
- partial options fields,
- fields whose normal game workflow would trigger extra recalculation.

These fields can be edited, but users should treat them as lower-level save data rather than as fully emulated game actions. The GUI requires an additional acknowledgement before writing patches that include `ADVANCED` fields.

## EXPERIMENTAL

Operations that can alter structure length or object identity:

- adding/removing inventory items,
- changing PID/FID/type,
- changing object scripts/local vars,
- changing queue entries,
- semantic global/quest/script editing,
- semantic worldmap/party/map-object editing,
- `.SAV`/`AUTOMAP.SAV` rebuild or semantic write.

High-level `EXPERIMENTAL` operations are intentionally not implemented until there are enough real fixtures and source-aligned parser tests to protect round-trip behaviour.

## RAW

Unknown bytes. The tool can read them and can write them only through:

```bash
f1se raw-write SLOT SAVE.DAT:0xOFFSET:HEX --experimental --write
```

Raw writes bypass semantic field validators. They must remain explicit and must not be hidden behind friendly high-level APIs.

## Fixture rule

Every new writable field should be checked against at least one real save fixture. The no-change parse invariant is stronger than semantic coverage: unknown bytes must remain byte-identical even when the editor does not understand them.
