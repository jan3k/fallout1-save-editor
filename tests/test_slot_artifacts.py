from __future__ import annotations

import unittest
from pathlib import Path

from f1se.format.slot import ARTIFACT_AUTOMAP_SAV, ARTIFACT_MAP_SAV, SaveSlot, classify_artifact

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "SLOT01"


class SlotArtifactsTests(unittest.TestCase):
    def test_artifacts_are_classified_and_fingerprinted(self) -> None:
        slot = SaveSlot.open(FIXTURE)
        artifacts = {artifact.name: artifact for artifact in slot.artifacts}
        self.assertEqual(set(artifacts), {"AUTOMAP.SAV", "V13ENT.SAV"})
        self.assertEqual(artifacts["AUTOMAP.SAV"].kind, ARTIFACT_AUTOMAP_SAV)
        self.assertEqual(artifacts["V13ENT.SAV"].kind, ARTIFACT_MAP_SAV)
        self.assertGreater(artifacts["AUTOMAP.SAV"].size, 0)
        self.assertGreater(artifacts["V13ENT.SAV"].size, 0)
        self.assertEqual(len(artifacts["AUTOMAP.SAV"].sha256), 64)
        self.assertEqual(artifacts["AUTOMAP.SAV"].parser_status, "raw-fingerprint")
        self.assertEqual(artifacts["V13ENT.SAV"].parser_status, "raw-fingerprint")

    def test_artifact_to_dict_keeps_legacy_fields(self) -> None:
        artifact = SaveSlot.open(FIXTURE).artifacts[0]
        doc = artifact.to_dict()
        self.assertIn("name", doc)
        self.assertIn("size", doc)
        self.assertIn("size_hex", doc)
        self.assertIn("sha256", doc)
        self.assertIn("kind", doc)
        self.assertIn("parser_status", doc)
        self.assertIn("warnings", doc)

    def test_classify_artifact(self) -> None:
        self.assertEqual(classify_artifact("SAVE.DAT"), "SAVE_DAT")
        self.assertEqual(classify_artifact("AUTOMAP.SAV"), "AUTOMAP_SAV")
        self.assertEqual(classify_artifact("V13ENT.SAV"), "MAP_SAV")
        self.assertEqual(classify_artifact("README.txt"), "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
