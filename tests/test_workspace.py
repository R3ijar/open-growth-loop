from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_growth_loop.workspace import init_workspace, validate_workspace


class WorkspaceTests(unittest.TestCase):
    def test_init_creates_default_data_files_without_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = init_workspace(root)
            inventory = root / "data" / "content_inventory.csv"
            inventory.write_text("custom\n", encoding="utf-8")

            second_result = init_workspace(root)
            inventory_text = inventory.read_text(encoding="utf-8")

        self.assertEqual(len(result.created), 4)
        self.assertEqual(len(second_result.created), 0)
        self.assertEqual(len(second_result.skipped), 4)
        self.assertEqual(inventory_text, "custom\n")

    def test_validate_accepts_initialized_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_workspace(root)

            result = validate_workspace(root)

        self.assertTrue(result.ok, result.errors)
        self.assertEqual(len(result.checked), 4)

    def test_validate_reports_private_event_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_workspace(root)
            (root / "data" / "events.csv").write_text(
                "date,asset,event,count,email\n"
                "2026-05-20,/docs/start,view,1,a@example.com\n",
                encoding="utf-8",
            )

            result = validate_workspace(root)

        self.assertFalse(result.ok)
        self.assertTrue(any("private-looking columns" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
