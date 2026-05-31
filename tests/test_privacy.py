from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_growth_loop.privacy import render_privacy_scan_markdown, scan_privacy


class PrivacyScanTests(unittest.TestCase):
    def test_privacy_scan_accepts_clean_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "data").mkdir()
            (root / "data" / "events.csv").write_text("date,asset,event,count\n", encoding="utf-8")

            result = scan_privacy(root)

        self.assertTrue(result.ok)
        self.assertEqual(result.findings, [])

    def test_privacy_scan_flags_private_csv_headers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "data").mkdir()
            (root / "data" / "events.csv").write_text("date,asset,event,count,email\n", encoding="utf-8")

            result = scan_privacy(root)

        self.assertFalse(result.ok)
        self.assertEqual(result.findings[0].kind, "private_csv_header")

    def test_privacy_scan_flags_secret_like_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "notes.md").write_text("api_key = abcdefghijklmnop\n", encoding="utf-8")

            result = scan_privacy(root)
            markdown = render_privacy_scan_markdown(result)

        self.assertFalse(result.ok)
        self.assertIn("secret_assignment", markdown)

    def test_privacy_scan_excludes_tests_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "tests").mkdir()
            (root / "tests" / "fixture.csv").write_text("date,asset,event,count,email\n", encoding="utf-8")

            result = scan_privacy(root)
            result_with_tests = scan_privacy(root, include_tests=True)

        self.assertTrue(result.ok)
        self.assertFalse(result_with_tests.ok)


if __name__ == "__main__":
    unittest.main()
