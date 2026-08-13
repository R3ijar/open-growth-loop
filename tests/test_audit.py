from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_growth_loop.audit import (
    build_repo_audit,
    render_audit_markdown,
    render_audit_prompt,
    write_audit_reports,
)

HEALTHY_README = """# Example Project

A small command-line tool that does one thing well: it reads a local file,
summarizes what it found, and writes the result next to the input so that
nothing ever leaves the machine it runs on.

## Install

```bash
pip install example-project
```

## Usage

```bash
example-project --input notes.txt
```

The command prints a short summary and writes `notes.summary.txt` in the
same directory.

## Documentation

See the docs/ directory for the full guide, configuration reference, and
troubleshooting notes.
"""


class AuditTests(unittest.TestCase):
    def test_empty_repo_fails_essentials_and_recommends_license_first(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            audit = build_repo_audit(Path(temp_dir), generated_at="2026-06-03")

        self.assertFalse(audit.ok)
        by_id = {check.id: check for check in audit.checks}
        self.assertEqual(by_id["readme"].status, "fail")
        self.assertEqual(by_id["license"].status, "fail")
        self.assertEqual(by_id["release_tags"].status, "skip")
        self.assertIsNotNone(audit.recommended_action)
        self.assertEqual(audit.recommended_action.check_id, "license")
        self.assertEqual(audit.recommended_action.confidence, "high")

    def test_healthy_repo_passes_all_counted_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_healthy_repo(root)

            audit = build_repo_audit(root, generated_at="2026-06-03")

        self.assertTrue(audit.ok)
        self.assertEqual(audit.score["fail"], 0)
        self.assertEqual(audit.score["warn"], 0)
        self.assertEqual(audit.score["percent"], 100)
        self.assertEqual(audit.score["skipped"], 1)
        self.assertIsNone(audit.recommended_action)

    def test_thin_readme_warns_and_becomes_recommendation_after_license(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_healthy_repo(root)
            (root / "README.md").write_text("# Tiny\n", encoding="utf-8")

            audit = build_repo_audit(root, generated_at="2026-06-03")

        self.assertTrue(audit.ok)
        by_id = {check.id: check for check in audit.checks}
        self.assertEqual(by_id["readme"].status, "warn")
        self.assertIsNotNone(audit.recommended_action)
        self.assertEqual(audit.recommended_action.check_id, "readme")
        self.assertEqual(audit.recommended_action.confidence, "medium")

    def test_dual_license_filenames_are_recognized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_healthy_repo(root)
            (root / "LICENSE").unlink()
            (root / "LICENSE-APACHE").write_text("Apache License 2.0\n", encoding="utf-8")
            (root / "LICENSE-MIT").write_text("MIT License\n", encoding="utf-8")
            audit = build_repo_audit(root, generated_at="2026-08-12")
        by_id = {check.id: check for check in audit.checks}
        self.assertEqual(by_id["license"].status, "pass")

    def test_markdown_report_includes_scorecard_and_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_healthy_repo(root)
            (root / "CHANGELOG.md").unlink()

            audit = build_repo_audit(root, generated_at="2026-06-03")
            markdown = render_audit_markdown(audit)
            prompt = render_audit_prompt(audit)

        self.assertIn("## Scorecard", markdown)
        self.assertIn("## Recommended Next Action", markdown)
        self.assertIn("Codex-ready prompt", markdown)
        self.assertIn("one focused, reviewable change", prompt)
        self.assertIn("CHANGELOG", prompt)

    def test_all_healthy_report_points_to_data_loop(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_healthy_repo(root)

            audit = build_repo_audit(root, generated_at="2026-06-03")
            markdown = render_audit_markdown(audit)

        self.assertIn("ogl init", markdown)
        self.assertEqual(render_audit_prompt(audit), "")

    def test_write_audit_reports_writes_latest_and_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_healthy_repo(root)
            audit = build_repo_audit(root, generated_at="2026-06-03")

            md_path, md_history, json_path, json_history = write_audit_reports(audit, root / "outbox" / "audit")

            self.assertTrue(md_path.exists())
            self.assertTrue(json_path.exists())

        self.assertEqual(md_path.name, "latest-audit.md")
        self.assertTrue(md_history.name.endswith("-audit.md"))
        self.assertEqual(json_path.name, "latest-audit.json")
        self.assertTrue(json_history.name.endswith("-audit.json"))


def _write_healthy_repo(root: Path) -> None:
    (root / "README.md").write_text(HEALTHY_README, encoding="utf-8")
    (root / "LICENSE").write_text("Apache License 2.0\n", encoding="utf-8")
    (root / "CONTRIBUTING.md").write_text("# Contributing\n", encoding="utf-8")
    (root / "CODE_OF_CONDUCT.md").write_text("# Code of Conduct\n", encoding="utf-8")
    (root / "SECURITY.md").write_text("# Security\n", encoding="utf-8")
    (root / "CHANGELOG.md").write_text("# Changelog\n\n## Unreleased\n\n- Note.\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
    (root / "examples").mkdir()
    (root / "examples" / "basic.md").write_text("# Basic\n", encoding="utf-8")
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI\n", encoding="utf-8")
    templates = root / ".github" / "ISSUE_TEMPLATE"
    templates.mkdir()
    (templates / "bug_report.md").write_text("Bug\n", encoding="utf-8")
    (root / ".github" / "pull_request_template.md").write_text("PR\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
