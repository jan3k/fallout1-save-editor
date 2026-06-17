# v1 readiness

A v1-ready build must satisfy:

- full test suite passes;
- `f1se smoke --json` returns `ok: true`;
- `f1se release-audit --strict --json` has no failing checks, or every warning is documented in release notes;
- public command names are listed by `f1se commands --json`;
- public top-level JSON contracts are listed by `f1se json-contracts --json`;
- fixture corpus is checked with `fixture-doctor`;
- compatibility and safety model documents are present.

This document intentionally does not expand high-level edit scope.
