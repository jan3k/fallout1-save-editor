from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from f1se.gui.model import SaveEditorSession
from f1se.project.features import FEATURES, F1SE_STATUSES, INTERFACES, RISK_LEVELS, feature_matrix_payload, filter_features

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "SLOT01"


class FeatureMatrixTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {"PYTHONPATH": str(ROOT / "src")}
        return subprocess.run([sys.executable, "-m", "f1se", *args], cwd=ROOT, env=env, capture_output=True, text=True)

    def test_feature_matrix_is_valid(self) -> None:
        self.assertGreater(len(FEATURES), 20)
        ids = [row.id for row in FEATURES]
        self.assertEqual(len(ids), len(set(ids)))
        for row in FEATURES:
            self.assertIn(row.f1se_status, F1SE_STATUSES)
            self.assertIn(row.risk_level, RISK_LEVELS)
            self.assertTrue(set(row.interface).issubset(INTERFACES))
            self.assertTrue(row.category)
            self.assertTrue(row.name)

    def test_required_categories_exist(self) -> None:
        categories = {row.category for row in FEATURES}
        for category in [
            "save metadata", "player stats", "SPECIAL", "derived stats", "skills", "tag skills", "traits", "perks", "kills", "inventory", "item metadata", "raw read/write", "artifacts", "map .SAV", "automap", "raw blocks", "global/script state", "quest state", "worldmap", "party", "map objects", "containers", "GUI safety workflow", "backups", "atomic write", "fixture matrix", "source alignment", "validation",
        ]:
            self.assertIn(category, categories)

    def test_feature_filters(self) -> None:
        inventory = filter_features(category="inventory")
        self.assertGreaterEqual(len(inventory), 2)
        self.assertTrue(all(row.category == "inventory" for row in inventory))
        readonly = filter_features(status="read-only")
        self.assertGreaterEqual(len(readonly), 1)
        self.assertTrue(all(row.f1se_status == "read-only" for row in readonly))

    def test_features_cli_json(self) -> None:
        cp = self.run_cli("features", "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertGreater(len(payload["features"]), 20)

    def test_features_cli_filters(self) -> None:
        cp = self.run_cli("features", "--category", "inventory", "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertTrue(payload["features"])
        self.assertTrue(all(row["category"] == "inventory" for row in payload["features"]))
        cp = self.run_cli("features", "--status", "read-only", "--json")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertTrue(payload["features"])
        self.assertTrue(all(row["f1se_status"] == "read-only" for row in payload["features"]))

    def test_feature_matrix_payload_and_gui_model(self) -> None:
        payload = feature_matrix_payload()
        self.assertIn("counts_by_status", payload)
        self.assertIn("counts_by_risk", payload)
        self.assertIn("recommended_next_milestones", payload)
        session_payload = SaveEditorSession(FIXTURE).feature_matrix_payload()
        self.assertEqual(payload["counts_by_status"], session_payload["counts_by_status"])
        self.assertGreater(len(session_payload["features"]), 20)

    def test_docs_exist(self) -> None:
        self.assertTrue((ROOT / "docs" / "f12se_parity.md").is_file())
        self.assertTrue((ROOT / "docs" / "roadmap.md").is_file())


if __name__ == "__main__":
    unittest.main()
