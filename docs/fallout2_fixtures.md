# Fallout 2 fixtures

Fallout 2 fixtures are not committed by default. Real saves must be imported only after explicit review of origin, license, privacy and reproducibility.

## Categories

The fixture tooling now recognizes the following Fallout 2 categories:

- `fallout2.baseline`
- `fallout2.inventory`
- `fallout2.perks`
- `fallout2.status_effects`
- `fallout2.late_game`
- `fallout2.negative`

The existing Fallout 1 baseline category remains represented by `baseline` and `fallout1.baseline` in coverage output.

## Synthetic fixtures

Unit tests use `f1se.format.fallout2.synthetic.build_minimal_fallout2_save()`. This byte stream is artificial and contains only enough structure to validate:

- common header parsing;
- Fallout 2 detection;
- Function 5 marker handling;
- Function 6 stat offsets;
- Function 7/8/9/13/15 read-only skeletons;
- JSON contracts.

Synthetic data is not evidence that write support is safe.

## Real fixture import policy

Before adding a real Fallout 2 fixture:

1. document the game version and distribution if known;
2. strip or accept player-identifying data only after review;
3. confirm the save is legally shareable;
4. add a manifest entry describing expected fields and warnings;
5. run `fixture-doctor`, `fixture-coverage` and `release-audit`;
6. do not enable Fallout 2 writes from that fixture alone.

## Negative fixtures

Negative fixtures should be temporary, synthetic mutations of curated saves or synthetic headers. They should exercise corrupt headers, missing Function 5 markers, broken inventory walks and impossible stat ranges.
