# SAVE.DAT format notes implemented in v0.1

## Endianness

All parsed numeric fields are big-endian. Most semantic fields are signed 32-bit integers.

## Header

The parser validates `FALLOUT SAVE FILE` and reads fixed header metadata from the first `0x7563` bytes:

- version,
- player name,
- save name,
- real save date,
- game date/time,
- current map file,
- map id/elevation,
- thumbnail range.

## Function order

The engine has 27 save/load handlers. v0.1 creates 27 function-block records in source order and preserves raw bytes for every block.

Semantic support is implemented for these blocks:

- Function 5: player object + inventory,
- Function 6: critter/player stats,
- Function 7: kill-count block boundary detection,
- Function 8: tag skills,
- Function 10: perk raw ranks,
- Function 13: PC stats,
- Function 16: traits,
- Function 18: partial options.

The remaining blocks are preserved raw with warnings where block splitting is heuristic.

## Function 5

Located dynamically by the `00 00 46 50` / `FP` marker. The parser does not assume a global absolute offset.

Inventory starts at Function 5 relative offset `0x80` and uses dynamic item sizes. Known Fallout 1 fixture PIDs are mapped to type and size; unknown PIDs are handled by a bounded heuristic that must lead to a valid Function 6 candidate.

## Function 6

Function 6 is fixed at `0x178` bytes once the start is known. v0.1 parses:

- base stats,
- derived stats,
- bonus stats,
- 18 saved skill points-over-base,
- proto/message/description tail fields.

## Write model

The writer mutates only selected field bytes in a bytearray clone. It never serializes the save from scratch. Unknown bytes remain untouched unless `raw-write` is explicitly used.
