from __future__ import annotations

import unittest
from pathlib import Path

from f1se.format.slot import SaveSlot
from f1se.gui.model import SaveEditorSession
from f1se.project.inventory_workflow import build_inventory_quantity_patch, inventory_workflow_payload

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "SLOT01"


class InventoryWorkflowTests(unittest.TestCase):
    def test_payload_contains_existing_items_and_fields(self) -> None:
        slot = SaveSlot.open(FIXTURE)
        payload = inventory_workflow_payload(slot)
        self.assertEqual(payload["inventory_count"], 5)
        items = {item["index"]: item for item in payload["items"]}
        stimpak = items[3]
        self.assertEqual(stimpak["pid"], 40)
        self.assertEqual(stimpak["quantity"], 6)
        self.assertTrue(stimpak["known_pid"])
        field_names = [field["field_name"] for field in stimpak["editable_fields"]]
        self.assertIn("inventory.3.quantity", field_names)
        for op in ["add_item", "remove_item", "change_pid", "change_fid", "change_type"]:
            self.assertIn(op, stimpak["blocked_operations"])

    def test_quantity_patch_plan(self) -> None:
        slot = SaveSlot.open(FIXTURE)
        plan = build_inventory_quantity_patch(slot, 3, 20)
        self.assertEqual(plan.patch, {"inventory.3.quantity": 20})
        self.assertEqual(plan.risks, ["SAFE"])
        self.assertFalse(plan.requires_advanced_confirmation)

    def test_quantity_validation(self) -> None:
        slot = SaveSlot.open(FIXTURE)
        with self.assertRaises(ValueError):
            build_inventory_quantity_patch(slot, 3, 0)
        with self.assertRaises(ValueError):
            build_inventory_quantity_patch(slot, 3, -1)
        with self.assertRaises(IndexError):
            build_inventory_quantity_patch(slot, 99, 1)

    def test_gui_model_payloads(self) -> None:
        session = SaveEditorSession(FIXTURE)
        payload = session.inventory_workflow_payload()
        self.assertEqual(payload["inventory_count"], 5)
        plan = session.inventory_quantity_plan(3, 20)
        self.assertEqual(plan["patch"], {"inventory.3.quantity": 20})


if __name__ == "__main__":
    unittest.main()
