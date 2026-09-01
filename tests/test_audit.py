from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from open_growth_loop.audit import (
    build_repo_audit,
    render_audit_markdown,
    render_audit_prompt,
    write_audit_reports,
)
from open_growth_loop.config import load_config

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

    def test_readme_vulnerability_reporting_instructions_satisfy_security_check(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_healthy_repo(root)
            (root / "SECURITY.md").unlink()
            readme = (root / "README.md").read_text(encoding="utf-8")
            (root / "README.md").write_text(
                readme
                + "\n## Vulnerability reporting\n\n"
                + "For reporting a security vulnerability, contact the maintainer through the private disclosure channel.\n",
                encoding="utf-8",
            )

            audit = build_repo_audit(root, generated_at="2026-08-12")

        by_id = {check.id: check for check in audit.checks}
        self.assertEqual(by_id["security_policy"].status, "pass")
        self.assertIn("README", by_id["security_policy"].detail)

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

    def test_example_profile_qualifies_install_without_claiming_a_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_healthy_repo(root)
            readme = (root / "README.md").read_text(encoding="utf-8")
            readme = readme.replace("## Install\n\n```bash\npip install example-project\n```\n\n", "")
            (root / "README.md").write_text(readme, encoding="utf-8")
            (root / "open-growth-loop.toml").write_text(
                "[audit_profile]\n"
                'purpose = "example"\n'
                "\n[audit_profile.checks.install]\n"
                'disposition = "qualify"\n'
                'reason = "This repository is editable packaging-tutorial material; its install command is taught in the surrounding tutorial."\n',
                encoding="utf-8",
            )
            profile = load_config(root).audit_profile

            audit = build_repo_audit(root, generated_at="2026-09-01", audit_profile=profile)
            markdown = render_audit_markdown(audit)
            _, _, json_path, _ = write_audit_reports(audit, root / "outbox" / "audit")
            json_payload = json.loads(json_path.read_text(encoding="utf-8"))

        by_id = {check.id: check for check in audit.checks}
        self.assertEqual(by_id["install"].status, "qualified")
        self.assertIn("repository profile qualified", by_id["install"].detail.lower())
        self.assertEqual(audit.score["qualified"], 1)
        self.assertEqual(audit.score["pass"], 12)
        self.assertEqual(audit.score["total"], 13)
        self.assertEqual(audit.score["percent"], 92)
        self.assertIsNone(audit.recommended_action)
        self.assertIn("## Repository Context", markdown)
        self.assertIn("not independently verified", markdown)
        self.assertIn("QUALIFIED", markdown)
        self.assertEqual(json_payload["profile"]["purpose"], "example")
        json_checks = {check["id"]: check for check in json_payload["checks"]}
        self.assertEqual(json_checks["install"]["status"], "qualified")

    def test_profile_skip_remains_in_score_and_default_behavior_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_healthy_repo(root)
            readme = (root / "README.md").read_text(encoding="utf-8")
            readme = readme.replace("## Install\n\n```bash\npip install example-project\n```\n\n", "")
            (root / "README.md").write_text(readme, encoding="utf-8")

            default_audit = build_repo_audit(root, generated_at="2026-09-01")
            (root / "open-growth-loop.toml").write_text(
                "[audit_profile]\n"
                'purpose = "template"\n'
                "\n[audit_profile.checks.install]\n"
                'disposition = "skip"\n'
                'reason = "Generated projects own their install instructions; this repository only supplies source templates."\n',
                encoding="utf-8",
            )
            profile = load_config(root).audit_profile
            profiled_audit = build_repo_audit(root, generated_at="2026-09-01", audit_profile=profile)

        default_by_id = {check.id: check for check in default_audit.checks}
        profiled_by_id = {check.id: check for check in profiled_audit.checks}
        self.assertEqual(default_by_id["install"].status, "warn")
        self.assertEqual(default_audit.recommended_action.check_id, "install")
        self.assertEqual(profiled_by_id["install"].status, "profile_skip")
        self.assertEqual(profiled_audit.score["profile_skipped"], 1)
        self.assertEqual(profiled_audit.score["percent"], 92)
        self.assertIsNone(profiled_audit.recommended_action)

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
