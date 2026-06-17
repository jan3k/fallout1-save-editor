from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "SLOT01"


class ArtifactsCliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {"PYTHONPATH": str(ROOT / "src")}
        return subprocess.run(
            [sys.executable, "-m", "f1se", *args],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_artifacts_json_command(self) -> None:
        cp = self.run_cli("artifacts", str(FIXTURE), "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        artifacts = {artifact["name"]: artifact for artifact in payload["artifacts"]}
        self.assertEqual(set(artifacts), {"AUTOMAP.SAV", "V13ENT.SAV"})
        self.assertEqual(artifacts["AUTOMAP.SAV"]["kind"], "AUTOMAP_SAV")
        self.assertEqual(artifacts["V13ENT.SAV"]["kind"], "MAP_SAV")
        self.assertEqual(artifacts["AUTOMAP.SAV"]["parser_status"], "raw-fingerprint")
        self.assertEqual(len(artifacts["AUTOMAP.SAV"]["sha256"]), 64)

    def test_artifacts_text_command(self) -> None:
        cp = self.run_cli("artifacts", str(FIXTURE))
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("AUTOMAP.SAV", cp.stdout)
        self.assertIn("AUTOMAP_SAV", cp.stdout)
        self.assertIn("V13ENT.SAV", cp.stdout)
        self.assertIn("MAP_SAV", cp.stdout)


if __name__ == "__main__":
    unittest.main()
