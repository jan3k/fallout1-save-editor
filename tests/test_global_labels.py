from __future__ import annotations

import unittest
from pathlib import Path

from f1se.format.save_dat import SaveDat
from f1se.gui.model import SaveEditorSession
from f1se.project.features import FEATURES
from f1se.project.global_labels import GLOBAL_LABELS, VALID_CONFIDENCES, global_labels, global_labels_payload

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "SLOT01"
SAVE = FIXTURE / "SAVE.DAT"


class GlobalLabelTests(unittest.TestCase):
    def test_label_matrix_is_valid(self) -> None:
        self.assertGreaterEqual(len(GLOBAL_LABELS), 3)
        ids = [label.id for label in GLOBAL_LABELS]
        self.assertEqual(len(ids), len(set(ids)))
        for label in GLOBAL_LABELS:
            self.assertIn(label.confidence, VALID_CONFIDENCES)
            self.assertGreaterEqual(label.block_index, 0)
            self.assertTrue(label.label)
            self.assertTrue(label.source)

    def test_block_filter_and_payload(self) -> None:
        labels = global_labels(2)
        self.assertTrue(labels)
        self.assertTrue(all(label.block_index == 2 for label in labels))
        payload = global_labels_payload(2)
        self.assertEqual(payload["block_index"], 2)
        self.assertTrue(payload["read_only"])
        self.assertTrue(payload["labels"])

    def test_gui_model_payload_and_scan_labels(self) -> None:
        session = SaveEditorSession(FIXTURE)
        payload = session.global_labels_payload()
        self.assertTrue(payload["labels"])
        scan = session.globals_scan_payload()
        by_index = {row["block_index"]: row for row in scan["candidates"]}
        self.assertIn(2, by_index)
        self.assertIn("labels", by_index[2])
        self.assertTrue(by_index[2]["labels"])

    def test_save_dat_unchanged_and_feature_matrix(self) -> None:
        before = SAVE.read_bytes()
        session = SaveEditorSession(FIXTURE)
        session.global_labels_payload()
        session.globals_scan_payload()
        self.assertEqual(SAVE.read_bytes(), before)
        self.assertEqual(SaveDat.from_path(SAVE).verify(), [])
        ids = {row.id for row in FEATURES}
        self.assertIn("global.labels", ids)


if __name__ == "__main__":
    unittest.main()
