# Release candidate notes

Use these commands before tagging a stable release:

```bash
f1se commands --json
f1se json-contracts --json
f1se release-audit --strict --json
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

A release candidate can proceed only when CI passes and strict audit either passes or every warning is explicitly accepted in release notes.
