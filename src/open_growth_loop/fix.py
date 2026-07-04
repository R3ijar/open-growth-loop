"""Deterministic fixes for audit findings.

Where an audit gap is mechanical (a missing community file, changelog,
license, or starter CI workflow), the fix command scaffolds it from a
bundled template with clear TODO markers. Existing files are never
overwritten. Gaps that need real judgment (README content, quickstart,
docs) stay manual and are handed off as a Codex-ready prompt instead.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from importlib import resources
from pathlib import Path

from .audit import AuditCheck

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib  # type: ignore[no-redef]


LICENSE_CHOICES = ["mit", "apache-2.0"]

# Ecosystem marker file -> CI template, checked in order.
CI_ECOSYSTEMS = [
    ("pyproject.toml", "ci-python.yml", "python"),
    ("setup.py", "ci-python.yml", "python"),
    ("package.json", "ci-node.yml", "node"),
    ("Cargo.toml", "ci-rust.yml", "rust"),
    ("go.mod", "ci-go.yml", "go"),
]


@dataclass(frozen=True)
class FixOptions:
    license_id: str = ""
    holder: str = ""
    dry_run: bool = False


@dataclass(frozen=True)
class FixResult:
    check_id: str
    status: str  # created | planned | skipped | manual | blocked
    detail: str
    files: list[str]


def fixable_check_ids() -> list[str]:
    return list(_FIXERS)


def apply_fix(repo: Path, check: AuditCheck, options: FixOptions) -> FixResult:
    if check.status == "pass":
        return FixResult(check.id, "skipped", f"{check.name} already passes; nothing to scaffold.", [])
    if check.status == "skip":
        return FixResult(check.id, "skipped", check.detail, [])
    fixer = _FIXERS.get(check.id)
    if fixer is None:
        return FixResult(
            check.id,
            "manual",
            f"{check.name} needs project knowledge and cannot be scaffolded mechanically. Use the generated prompt.",
            [],
        )
    return fixer(repo, check, options)


def _fix_license(repo: Path, check: AuditCheck, options: FixOptions) -> FixResult:
    if options.license_id not in LICENSE_CHOICES:
        return FixResult(
            check.id,
            "blocked",
            "Choosing a license is a deliberate decision. Rerun with --license mit or --license apache-2.0 (and optionally --holder \"Your Name\").",
            [],
        )
    content = _render(f"LICENSE-{options.license_id}.txt", repo, holder=options.holder)
    return _write_files(repo, {"LICENSE": content}, check, options)


def _fix_readme(repo: Path, check: AuditCheck, options: FixOptions) -> FixResult:
    if check.status == "warn":
        return FixResult(
            check.id,
            "manual",
            "A README already exists but is thin. Expand it rather than replacing it; use the generated prompt.",
            [],
        )
    return _write_files(repo, {"README.md": _render("README.md", repo)}, check, options)


def _fix_changelog(repo: Path, check: AuditCheck, options: FixOptions) -> FixResult:
    return _write_files(repo, {"CHANGELOG.md": _render("CHANGELOG.md", repo)}, check, options)


def _fix_contributing(repo: Path, check: AuditCheck, options: FixOptions) -> FixResult:
    return _write_files(repo, {"CONTRIBUTING.md": _render("CONTRIBUTING.md", repo)}, check, options)


def _fix_code_of_conduct(repo: Path, check: AuditCheck, options: FixOptions) -> FixResult:
    return _write_files(repo, {"CODE_OF_CONDUCT.md": _render("CODE_OF_CONDUCT.md", repo)}, check, options)


def _fix_security_policy(repo: Path, check: AuditCheck, options: FixOptions) -> FixResult:
    return _write_files(repo, {"SECURITY.md": _render("SECURITY.md", repo)}, check, options)


def _fix_issue_templates(repo: Path, check: AuditCheck, options: FixOptions) -> FixResult:
    return _write_files(
        repo,
        {
            ".github/ISSUE_TEMPLATE/bug_report.md": _render("ISSUE_TEMPLATE-bug_report.md", repo),
            ".github/ISSUE_TEMPLATE/feature_request.md": _render("ISSUE_TEMPLATE-feature_request.md", repo),
        },
        check,
        options,
    )


def _fix_pr_template(repo: Path, check: AuditCheck, options: FixOptions) -> FixResult:
    return _write_files(repo, {".github/pull_request_template.md": _render("pull_request_template.md", repo)}, check, options)


def _fix_ci(repo: Path, check: AuditCheck, options: FixOptions) -> FixResult:
    for marker, template, ecosystem in CI_ECOSYSTEMS:
        if (repo / marker).is_file():
            result = _write_files(repo, {".github/workflows/ci.yml": _render(template, repo)}, check, options)
            if result.status in {"created", "planned"}:
                detail = f"{result.detail} Detected a {ecosystem} project from {marker}; review the TODO markers before relying on it."
                return FixResult(result.check_id, result.status, detail, result.files)
            return result
    return FixResult(
        check.id,
        "blocked",
        "Could not detect a Python, Node, Rust, or Go project, so no CI template applies. Add a workflow manually or use the generated prompt.",
        [],
    )


_FIXERS = {
    "license": _fix_license,
    "readme": _fix_readme,
    "changelog": _fix_changelog,
    "contributing": _fix_contributing,
    "code_of_conduct": _fix_code_of_conduct,
    "security_policy": _fix_security_policy,
    "issue_templates": _fix_issue_templates,
    "pr_template": _fix_pr_template,
    "ci": _fix_ci,
}


def _write_files(repo: Path, files: dict[str, str], check: AuditCheck, options: FixOptions) -> FixResult:
    existing = [rel for rel in files if (repo / rel).exists()]
    to_create = {rel: content for rel, content in files.items() if rel not in existing}
    if not to_create:
        return FixResult(check.id, "skipped", f"Nothing to do; already present: {', '.join(existing)}.", [])

    if not options.dry_run:
        for rel, content in to_create.items():
            target = repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

    created = sorted(to_create)
    verb = "Would scaffold" if options.dry_run else "Scaffolded"
    detail = f"{verb} {', '.join(created)}."
    if existing:
        detail += f" Left existing file(s) untouched: {', '.join(sorted(existing))}."
    detail += " Review the generated file(s) and fill in any TODO markers before committing."
    return FixResult(check.id, "planned" if options.dry_run else "created", detail, created)


def _render(template_name: str, repo: Path, holder: str = "") -> str:
    text = _template(template_name)
    project = project_name(repo)
    return (
        text.replace("__PROJECT__", project)
        .replace("__YEAR__", str(date.today().year))
        .replace("__HOLDER__", holder or f"{project} contributors")
    )


def _template(name: str) -> str:
    return (resources.files("open_growth_loop") / "templates" / name).read_text(encoding="utf-8")


def project_name(repo: Path) -> str:
    pyproject = repo / "pyproject.toml"
    if pyproject.is_file():
        try:
            name = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("project", {}).get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()
        except (OSError, ValueError):
            pass
    package_json = repo / "package.json"
    if package_json.is_file():
        try:
            payload = json.loads(package_json.read_text(encoding="utf-8"))
            name = payload.get("name") if isinstance(payload, dict) else None
            if isinstance(name, str) and name.strip():
                return name.strip()
        except (OSError, ValueError):
            pass
    cargo = repo / "Cargo.toml"
    if cargo.is_file():
        try:
            name = tomllib.loads(cargo.read_text(encoding="utf-8")).get("package", {}).get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()
        except (OSError, ValueError):
            pass
    return repo.name or str(repo)
