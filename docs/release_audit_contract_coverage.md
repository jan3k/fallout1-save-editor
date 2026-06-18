# Release audit contract coverage

Version 1.7 makes release audit consume the JSON contract metadata added in earlier releases.

`f1se release-audit --json` now reports `json.contract_coverage`.

The check verifies that selected public JSON surfaces have:

- a key contract;
- top-level field types;
- nested samples where required.

The coverage matrix is intentionally selective. It focuses on public automation surfaces used by GUI, CI and scripting.

The audit remains read-only.
