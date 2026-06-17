# Fixture report

Fixture path: `tests/fixtures/SLOT01`

## Files

```text
SAVE.DAT     size=38155 / 0x950B  sha256=d728d1d4f7c36fa1bed4218e996724e7b21c8ff3ca18da3b03c3ecd1811845a8
AUTOMAP.SAV  size=2218  / 0x08AA  sha256=c3481b91ec65146656008af69261c3f4ec6afb53872eda87181d82d1dd0084d3
V13ENT.SAV   size=177224 / 0x2B448 sha256=c6cac9d286f1fa54b64e61f070e86068d4d74b76b542cfed551637a83f2604bf
```

## Header

```text
signature: FALLOUT SAVE FILE
version: 1.02R
player_name: yay
current_map_file: V13ENT.sav
map_id: 35
elevation: 0
saved_date: 2026-06-17
```

## Function anchors

```text
Function 5 / player object + inventory: 0x88CC
Function 6 / player critter stats:       0x8B38
Function 6 length:                       0x178
Function 7 start:                        0x8CB0
```

## Function 5 fields

```text
signature:             0x88CC = 00 00 46 50
coordinates:           0x88D0 = 19090
facing:                0x88E8 = 2
FID:                   0x88EC = 0x0100000B
map_level:             0x88F4 = 0
inventory_count:       0x8914 = 5
crippled_body_parts:   0x8930 = 0
current_hp:            0x8940 = 28
radiation:             0x8944 = 0
poison:                0x8948 = 0
item_list_start:       0x894C
camera_position:       0x8B34
```

## Inventory

| Index | Offset | Size | Quantity | PID | Type | Object |
| ---: | ---: | ---: | ---: | ---: | --- | --- |
| 0 | `0x894C` | `0x64` | 1 | 4 | weapon | Knife |
| 1 | `0x89B0` | `0x64` | 1 | 8 | weapon | 10mm Pistol |
| 2 | `0x8A14` | `0x60` | 3 | 29 | ammo | 10mm JHP |
| 3 | `0x8A74` | `0x5C` | 6 | 40 | drug | Stimpak |
| 4 | `0x8AD0` | `0x64` | 2 | 79 | weapon | Flare |

## Function 6 / player stats

The current uploaded fixture has already-maxed base S.P.E.C.I.A.L. values:

| Field | Offset | Value |
| --- | ---: | ---: |
| base_strength | `0x8B40` | 10 |
| base_perception | `0x8B44` | 10 |
| base_endurance | `0x8B48` | 10 |
| base_charisma | `0x8B4C` | 10 |
| base_intelligence | `0x8B50` | 10 |
| base_agility | `0x8B54` | 10 |
| base_luck | `0x8B58` | 10 |
| base_hitpoints | `0x8B5C` | 28 |
| base_action_points | `0x8B60` | 7 |
| base_armor_class | `0x8B64` | 5 |
| base_melee_damage | `0x8B6C` | 1 |
| base_carry_weight | `0x8B70` | 100 |
| base_sequence | `0x8B74` | 10 |
| base_healing_rate | `0x8B78` | 1 |
| base_critical_chance | `0x8B7C` | 2 |
| radiation_resistance | `0x8BBC` | 10 |
| poison_resistance | `0x8BC0` | 25 |
| starting_age | `0x8BC4` | 25 |
| gender | `0x8BC8` | 0 |
| skills array start | `0x8C58` | 18 × 0 |
| proto_id | `0x8CA0` | 0 |
| description_line | `0x8CAC` | 0 |

## Other detected anchors

```text
kill_counts_start: 0x8CB0, detected 15 Fallout 1 counters
tag_skills_start: 0x8CEC, values: [14, 6, -1, 0]
perks_start:      0x8CFC, count: 64
pc_stats_start:   0x8E0C, values: [0, 21, 264797, 3, 1106]
traits_start:     0x8FA8, values: [8, 9]
options_start:    0x8FB4
```
