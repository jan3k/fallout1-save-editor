from __future__ import annotations

from typing import Any

from f1se.project.cli_index import commands_payload
from f1se.project.json_contracts import contracts_payload
from f1se.project.release_audit import run_release_audit


def smoke_payload() -> dict[str, Any]:
    commands = commands_payload()
    contracts = contracts_payload()
    audit = run_release_audit()
    checks = [
        {"id": "commands", "ok": commands.get("count", 0) > 0},
        {"id": "contracts", "ok": contracts.get("count", 0) > 0},
        {"id": "audit", "ok": audit.get("status") in {"OK", "WARN"}},
    ]
    return {"ok": all(row["ok"] for row in checks), "checks": checks, "commands_count": commands.get("count", 0), "contracts_count": contracts.get("count", 0), "audit_status": audit.get("status"), "read_only": True}
