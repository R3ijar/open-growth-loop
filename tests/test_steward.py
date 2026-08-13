from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_audit import _write_healthy_repo

from open_growth_loop.steward import GitSnapshot, build_steward_brief, render_steward_markdown, write_steward_reports


class StewardTests(unittest.TestCase):
    def test_repository_gap_wins_before_git_work(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_healthy_repo(root)
            (root / "CHANGELOG.md").unlink()
            git = GitSnapshot(True, "main", False, 2, "v1.0.0", 3, 5, 1)
            with patch("open_growth_loop.steward._read_git_snapshot", return_value=git):
                brief = build_steward_brief(root, generated_at="2026-08-12")
        self.assertEqual(brief.action.kind, "repository_gap")
        self.assertIn("CHANGELOG", brief.action.title)

    def test_dirty_tree_wins_when_audit_is_healthy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_healthy_repo(root)
            git = GitSnapshot(True, "main", False, 4, "v1.0.0", 2, 6, 2)
            with patch("open_growth_loop.steward._read_git_snapshot", return_value=git):
                brief = build_steward_brief(root, generated_at="2026-08-12")
        self.assertEqual(brief.action.kind, "working_tree")
        self.assertIn("4 changed path", brief.action.reason)
        self.assertEqual(brief.action.confidence, "medium")
        self.assertTrue(any("preserve" in step for step in brief.action.steps))

    def test_healthy_repo_defers_to_remote_demand(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_healthy_repo(root)
            git = GitSnapshot(True, "main", True, 0, "v1.0.0", 2, 6, 2)
            with patch("open_growth_loop.steward._read_git_snapshot", return_value=git):
                brief = build_steward_brief(root, generated_at="2026-08-12")
                markdown = render_steward_markdown(brief)
        self.assertEqual(brief.action.kind, "remote_review")
        self.assertIn("Safety Boundary", markdown)
        self.assertIn("does not fetch", markdown.lower())

    def test_write_reports_creates_markdown_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_healthy_repo(root)
            git = GitSnapshot(False, "", None, 0, "", None, None, None)
            with patch("open_growth_loop.steward._read_git_snapshot", return_value=git):
                brief = build_steward_brief(root, generated_at="2026-08-12")
                md_path, _, json_path, _ = write_steward_reports(brief, root / "outbox" / "steward")
            self.assertTrue(md_path.exists())
            self.assertTrue(json_path.exists())


if __name__ == "__main__":
    unittest.main()
