# Compatibility contract

This document describes the compatibility surface intended for automation and GUI clients.

Stable surfaces before v1.0:

- command names from `f1se commands --json`;
- top-level JSON keys listed by `f1se json-contracts --json`;
- read-only diagnostic payloads remaining read-only;
- explicit gated byte-level command behavior.

Not yet frozen before v1.0:

- nested diagnostic object shape;
- warning wording;
- heuristic confidence values;
- ordering of non-semantic candidates.

Use `release-audit --strict` in release pipelines when warnings should block a release candidate.
