from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_growth_loop.audit import build_repo_audit
from open_growth_loop.fix import FixOptions, apply_fix, fixable_check_ids, project_name


class FixTests(unittest.TestCase):
    def test_license_is_blocked_without_an_explicit_choice(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            check = _check_for(repo, "license")

            result = apply_fix(repo, check, FixOptions())

            self.assertEqual(result.status, "blocked")
            self.assertIn("--license", result.detail)
            self.assertFalse((repo / "LICENSE").exists())

    def test_license_mit_scaffold_passes_the_audit_afterwards(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            check = _check_for(repo, "license")

            result = apply_fix(repo, check, FixOptions(license_id="mit", holder="Example Person"))
            content = (repo / "LICENSE").read_text(encoding="utf-8")
            after = _check_for(repo, "license")

            self.assertEqual(result.status, "created")
            self.assertEqual(result.files, ["LICENSE"])
            self.assertIn("MIT License", content)
            self.assertIn("Example Person", content)
            self.assertNotIn("__YEAR__", content)
            self.assertEqual(after.status, "pass")

    def test_dry_run_plans_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            check = _check_for(repo, "security_policy")

            result = apply_fix(repo, check, FixOptions(dry_run=True))

            self.assertEqual(result.status, "planned")
            self.assertEqual(result.files, ["SECURITY.md"])
            self.assertFalse((repo / "SECURITY.md").exists())

    def test_passing_check_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "SECURITY.md").write_text("# Security\n", encoding="utf-8")
            check = _check_for(repo, "security_policy")

            result = apply_fix(repo, check, FixOptions())

            self.assertEqual(result.status, "skipped")

    def test_templates_substitute_the_project_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "pyproject.toml").write_text('[project]\nname = "sample-tool"\nversion = "1.0.0"\n', encoding="utf-8")
            check = _check_for(repo, "contributing")

            apply_fix(repo, check, FixOptions())
            content = (repo / "CONTRIBUTING.md").read_text(encoding="utf-8")

            self.assertIn("sample-tool", content)
            self.assertNotIn("__PROJECT__", content)

    def test_ci_fix_detects_a_python_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "pyproject.toml").write_text('[project]\nname = "sample-tool"\nversion = "1.0.0"\n', encoding="utf-8")
            check = _check_for(repo, "ci")

            result = apply_fix(repo, check, FixOptions())
            content = (repo / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

            self.assertEqual(result.status, "created")
            self.assertIn("python", result.detail)
            self.assertIn("setup-python", content)

    def test_ci_fix_is_blocked_for_unknown_ecosystems(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            check = _check_for(repo, "ci")

            result = apply_fix(repo, check, FixOptions())

            self.assertEqual(result.status, "blocked")
            self.assertFalse((repo / ".github" / "workflows" / "ci.yml").exists())

    def test_thin_readme_is_manual_not_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "README.md").write_text("# Tiny\n", encoding="utf-8")
            check = _check_for(repo, "readme")

            result = apply_fix(repo, check, FixOptions())

            self.assertEqual(result.status, "manual")
            self.assertEqual((repo / "README.md").read_text(encoding="utf-8"), "# Tiny\n")

    def test_missing_readme_is_scaffolded_with_todo_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            check = _check_for(repo, "readme")

            result = apply_fix(repo, check, FixOptions())
            content = (repo / "README.md").read_text(encoding="utf-8")

            self.assertEqual(result.status, "created")
            self.assertIn("TODO", content)

    def test_issue_templates_creates_both_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            check = _check_for(repo, "issue_templates")

            result = apply_fix(repo, check, FixOptions())

            self.assertEqual(result.status, "created")
            self.assertEqual(len(result.files), 2)
            self.assertEqual(_check_for(repo, "issue_templates").status, "pass")

    def test_unfixable_checks_are_manual(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            check = _check_for(repo, "quickstart")

            result = apply_fix(repo, check, FixOptions())

            self.assertEqual(result.status, "manual")
        self.assertNotIn("quickstart", fixable_check_ids())

    def test_project_name_prefers_package_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self.assertEqual(project_name(repo), repo.name)
            (repo / "package.json").write_text('{"name": "node-tool"}', encoding="utf-8")
            self.assertEqual(project_name(repo), "node-tool")
            (repo / "pyproject.toml").write_text('[project]\nname = "py-tool"\n', encoding="utf-8")
            self.assertEqual(project_name(repo), "py-tool")


def _check_for(repo: Path, check_id: str):
    audit = build_repo_audit(repo, generated_at="2026-06-03")
    return next(check for check in audit.checks if check.id == check_id)


if __name__ == "__main__":
    unittest.main()
