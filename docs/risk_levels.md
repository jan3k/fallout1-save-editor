# Risk levels

## SAFE

Fixed-width fields with local byte edits and conservative validation:

- base S.P.E.C.I.A.L. values,
- S.P.E.C.I.A.L. bonus values,
- current HP/radiation/poison,
- saved skill points over base,
- tag skill ids,
- trait ids,
- PC skill points, level, XP, reputation, karma,
- inventory quantity for existing items,
- known ammo/charges values for existing entries.

## ADVANCED

Fixed-width fields that can have engine-side consequences or derived-stat mismatch:

- derived stats,
- raw perk ranks,
- inventory ammo type,
- player facing/coordinates/map level,
- partial options fields,
- fields whose normal game workflow would trigger extra recalculation.

## EXPERIMENTAL

Operations that can alter structure length or object identity:

- adding/removing inventory items,
- changing PID/FID/type,
- changing object scripts/local vars,
- changing queue entries,
- semantic worldmap/party/map-object editing.

Not implemented as high-level operations in v0.1.

## RAW

Unknown bytes. The tool can read them and can write them only through:

```bash
f1se raw-write SLOT SAVE.DAT:0xOFFSET:HEX --experimental --write
```
