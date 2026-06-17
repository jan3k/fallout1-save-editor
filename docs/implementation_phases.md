# Implementation phases

This document records the final pre-v1 implementation phases.

## v0.21 Strict audit cleanup

Analysis: strict audit must become a real gate. JSON contract coverage is expanded and audit warnings are expected to be explainable.

## v0.22 CLI consolidation phase 1

Analysis: command discovery is kept explicit through `commands --json`; new commands are routed through a thin wrapper to avoid breaking older handlers.

## v0.23 CLI consolidation phase 2

Analysis: slot diagnostics remain delegated where stable, while new production-facing diagnostic commands are added through the final wrapper.

## v0.24 JSON schema hardening

Analysis: contracts remain shallow but include more public payloads to protect automation without freezing every nested heuristic field.

## v0.25 Fixture corpus hardening

Analysis: `fixture-doctor` adds corpus validation without writing fixture files.

## v0.26 Backup workflow

Analysis: backup listing and preview are read paths; selected backup copy-back requires an explicit write flag and first creates a safety backup.

## v0.27 Save diff

Analysis: slot comparison is read-only and reports semantic field, artifact and block-hash differences.

## v0.28 GUI/model diagnostic parity

Analysis: model payloads from earlier phases remain the integration point for future GUI views.

## v0.29 Release packaging

Analysis: install and smoke documentation describe the supported release checks without adding runtime dependencies.

## v1.0 Stable safe editor

Analysis: version is bumped to 1.0 and release notes describe the stable safe-editor boundary.
