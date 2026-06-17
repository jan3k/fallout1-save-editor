# Install

Development checkout:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
f1se commands --json
```

Smoke test:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m f1se smoke --json
PYTHONPATH=src python3 -m f1se release-audit --strict --json
```

The project has no required runtime dependency outside the Python standard library.
