"""Zero-config repository audit.

Unlike the CSV-driven planner, the audit reads only files that every
repository already has (README, LICENSE, community files, CI workflows,
changelog, docs and examples directories) plus optional local git tag
history. It never touches the network, so it stays inside the same
privacy boundary as the rest of the tool.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import AuditProfile
from .io_utils import today_iso, write_json_report, write_text_report
from .reporting import (
    collapsible_section,
    key_value_table,
    markdown_table,
    status_label,
)


@dataclass(frozen=True)
class AuditCheck:
    id: str
    category: str
    name: str
    status: str
    detail: str
    recommendation: str


@dataclass(frozen=True)
class AuditAction:
    check_id: str
    title: str
    reason: str
    confidence: str
    next_steps: list[str]


@dataclass(frozen=True)
class RepoAudit:
    ok: bool
    generated_at: str
    repo: str
    project_name: str
    score: dict[str, int]
    checks: list[AuditCheck]
    recommended_action: AuditAction | None
    warnings: list[str]
    profile: AuditProfile | None = None


README_NAMES = ["README.md", "README.rst", "README.txt", "README"]
LICENSE_PREFIXES = ("LICENSE", "LICENCE", "COPYING")
CHANGELOG_NAMES = ["CHANGELOG.md", "CHANGELOG.rst", "CHANGELOG.txt", "CHANGELOG", "CHANGES.md", "CHANGES", "HISTORY.md", "NEWS.md", "RELEASES.md"]
COMMUNITY_DIRS = ["", ".github", "docs"]
CI_PATHS = [
    ".gitlab-ci.yml",
    ".circleci/config.yml",
    "azure-pipelines.yml",
    "Jenkinsfile",
    ".travis.yml",
]
THIN_README_CHARS = 400
NO_TAG_COMMIT_WARNING = 20
COMMITS_SINCE_TAG_WARNING = 30

INSTALL_PATTERN = re.compile(
    r"\b(pip3? install|pipx (install|run)|uv (pip install|tool install)|npm (install|i)\b|yarn add|pnpm add"
    r"|cargo (install|add)|go (install|get)|gem install|composer require|brew install"
    r"|apt(-get)? install|docker (pull|run)|dotnet add|nuget install)\b",
    re.IGNORECASE,
)
INSTALL_HEADING_PATTERN = re.compile(r"^#{1,6}\s*.*\b(install|installation|setup)\b", re.IGNORECASE | re.MULTILINE)
QUICKSTART_HEADING_PATTERN = re.compile(
    r"^#{1,6}\s*.*\b(usage|quick\s?start|getting started|example|examples|tutorial|how to use|demo)\b",
    re.IGNORECASE | re.MULTILINE,
)
DOCS_LINK_PATTERN = re.compile(r"readthedocs|docs\.rs|hexdocs|pkg\.go\.dev|/docs/|\bdocumentation\b", re.IGNORECASE)
SECURITY_GUIDANCE_PATTERN = re.compile(
    r"(^#{1,6}\s*.*\b(vulnerability|security)\s+(reporting|disclosure)\b|\breport(?:ing)?\s+(?:a\s+)?security\s+vulnerabilit(?:y|ies)\b)",
    re.IGNORECASE | re.MULTILINE,
)

# Ordered by how much a gap hurts a new visitor; the first non-pass check
# becomes the single recommended action.
RECOMMENDATION_ORDER = [
    "license",
    "readme",
    "install",
    "quickstart",
    "ci",
    "changelog",
    "release_tags",
    "security_policy",
    "contributing",
    "docs",
    "examples",
    "issue_templates",
    "pr_template",
    "code_of_conduct",
]

NEXT_STEPS: dict[str, list[str]] = {
    "license": [
        "Choose a license that matches how you want the project reused (for example MIT or Apache-2.0).",
        "Add the license text as a top-level LICENSE file.",
        "Reference the license at the end of the README.",
    ],
    "readme": [
        "Write a README that states in one sentence what the project does and who it is for.",
        "Add an install command and one copy-pasteable usage example.",
        "Link to docs, examples, and contribution guidance if they exist.",
    ],
    "install": [
        "Add an Install section to the README with the exact command a new user runs.",
        "Verify the command works from a clean environment.",
    ],
    "quickstart": [
        "Add a Quickstart or Usage section with one copy-pasteable example.",
        "Show the expected output so a new user can confirm it worked.",
    ],
    "ci": [
        "Add a CI workflow that installs the project and runs its tests on push and pull request.",
        "Add the CI status badge to the README once it passes.",
    ],
    "changelog": [
        "Add a CHANGELOG.md with an Unreleased section and notes for the latest release.",
        "Update it as part of every release, not after.",
    ],
    "release_tags": [
        "Review the unreleased commits and group them into user-visible changes.",
        "Update the changelog, tag a release, and publish release notes.",
    ],
    "security_policy": [
        "Add a SECURITY.md explaining how to report a vulnerability privately.",
        "State which versions receive fixes.",
    ],
    "contributing": [
        "Add a CONTRIBUTING.md covering setup, tests, and how to propose a change.",
        "Link it from the README so contributors find it.",
    ],
    "docs": [
        "Create a docs/ directory or documentation site for anything the README cannot hold.",
        "Link the documentation from the README.",
    ],
    "examples": [
        "Add an examples/ directory with at least one small, runnable example.",
        "Reference the examples from the README.",
    ],
    "issue_templates": [
        "Add .github/ISSUE_TEMPLATE forms for bug reports and feature requests.",
        "Ask for reproduction steps and environment details in the bug template.",
    ],
    "pr_template": [
        "Add .github/pull_request_template.md asking what changed, why, and how it was tested.",
    ],
    "code_of_conduct": [
        "Add a CODE_OF_CONDUCT.md (the Contributor Covenant is a common default).",
    ],
}


def build_repo_audit(repo: Path, generated_at: str | None = None, audit_profile: AuditProfile | None = None) -> RepoAudit:
    generated_at = generated_at or today_iso()
    readme_text = _readme_text(repo)

    checks = [
        _readme_check(repo, readme_text),
        _license_check(repo),
        _install_check(readme_text),
        _quickstart_check(readme_text),
        _docs_check(repo, readme_text),
        _examples_check(repo, readme_text),
        _community_file_check(repo, "contributing", "community", "Contributing guide", "CONTRIBUTING.md"),
        _community_file_check(repo, "code_of_conduct", "community", "Code of conduct", "CODE_OF_CONDUCT.md"),
        _security_policy_check(repo, readme_text),
        _issue_templates_check(repo),
        _pr_template_check(repo),
        _changelog_check(repo),
        _ci_check(repo),
        _release_tags_check(repo),
    ]
    checks = _apply_profile(checks, audit_profile)

    counted = [check for check in checks if check.status != "skip"]
    passed = sum(1 for check in counted if check.status == "pass")
    score = {
        "pass": passed,
        "warn": sum(1 for check in counted if check.status == "warn"),
        "fail": sum(1 for check in counted if check.status == "fail"),
        "qualified": sum(1 for check in counted if check.status == "qualified"),
        "profile_skipped": sum(1 for check in counted if check.status == "profile_skip"),
        "skipped": len(checks) - len(counted),
        "total": len(counted),
        "percent": round(100 * passed / len(counted)) if counted else 0,
    }

    return RepoAudit(
        ok=not any(check.status == "fail" for check in checks),
        generated_at=generated_at,
        repo=str(repo),
        project_name=repo.name or str(repo),
        score=score,
        checks=checks,
        recommended_action=_recommended_action(checks),
        warnings=[f"{check.name}: {check.detail}" for check in checks if check.status in {"warn", "fail", "qualified", "profile_skip"}],
        profile=audit_profile,
    )


def render_audit_markdown(audit: RepoAudit) -> str:
    lines = [
        "# Repository Audit",
        "",
        (
            "A local maintainer-readiness check using repository files plus explicit repository-owned context from `open-growth-loop.toml`."
            if audit.profile
            else "A zero-config maintainer-readiness check. It reads only files the repository already has; no analytics exports are required."
        ),
        "",
        *_profile_markdown(audit.profile),
        "## Scorecard",
        "",
        *key_value_table(
            [
                ("Repository", audit.project_name),
                ("Generated at", audit.generated_at),
                (
                    "Overall status",
                    status_label(
                        "fail"
                        if audit.score["fail"]
                        else ("warn" if audit.score["warn"] or audit.score["qualified"] or audit.score["profile_skipped"] else "pass")
                    ),
                ),
                ("Score", f"{audit.score['percent']}% ({audit.score['pass']} of {audit.score['total']} checks pass)"),
                ("Warnings", audit.score["warn"]),
                ("Failures", audit.score["fail"]),
                ("Qualified", audit.score["qualified"]),
                ("Profile-skipped", audit.score["profile_skipped"]),
                ("Skipped", audit.score["skipped"]),
            ]
        ),
        "",
        "## Checks",
        "",
        *markdown_table(
            ["Check", "Category", "Status", "Detail"],
            [(check.name, check.category, status_label(check.status), check.detail) for check in audit.checks],
        ),
        "",
        "## Recommended Next Action",
        "",
    ]
    action = audit.recommended_action
    if action is None:
        lines.extend(
            [
                "All audited surfaces look healthy. The next signal-driven step is the data loop:",
                "",
                "1. Run `ogl init` to create the local data files.",
                "2. Drop in a Search Console export and aggregate event counts.",
                "3. Run `ogl plan` for one conservative, evidence-backed action.",
            ]
        )
    else:
        lines.extend(
            key_value_table(
                [
                    ("Action", action.title),
                    ("Why now", action.reason),
                    ("Confidence", action.confidence),
                ]
            )
        )
        lines.extend(["", "Steps:", ""])
        lines.extend(f"- [ ] {step}" for step in action.next_steps)
        lines.extend(["", *collapsible_section("Codex-ready prompt for this action", ["```text", *render_audit_prompt(audit).splitlines(), "```"])])
    lines.extend(
        [
            "",
            "## Going Deeper",
            "",
            "The audit covers repository hygiene. To plan work from real usage signals, add local CSV exports and run the full loop: `ogl init`, `ogl validate`, `ogl plan`.",
            "",
        ]
    )
    return "\n".join(lines)


def render_audit_prompt(audit: RepoAudit, action: AuditAction | None = None) -> str:
    action = action or audit.recommended_action
    if action is None:
        return ""
    steps = "\n".join(f"- {step}" for step in action.next_steps)
    return f"""You are helping maintain an open-source project.

Work from this single repository-audit action:

Repository: {audit.project_name}
Action: {action.title}
Why now: {action.reason}
Confidence: {action.confidence}

Constraints:
- Make one focused, reviewable change.
- Do not invent analytics or adoption claims.
- Match the project's existing tone and conventions.
- Add or update tests/docs when the change affects maintainer workflows.

Steps:
{steps}
"""


def write_audit_reports(audit: RepoAudit, out_dir: Path) -> tuple[Path, Path, Path, Path]:
    md_path, md_history = write_text_report(out_dir / "latest-audit.md", render_audit_markdown(audit))
    json_path, json_history = write_json_report(out_dir / "latest-audit.json", asdict(audit))
    return md_path, md_history, json_path, json_history


def action_from_check(check: AuditCheck) -> AuditAction:
    return AuditAction(
        check_id=check.id,
        title=check.recommendation or check.name,
        reason=check.detail,
        confidence="high" if check.status == "fail" else "medium",
        next_steps=list(NEXT_STEPS.get(check.id, [])),
    )


def _recommended_action(checks: list[AuditCheck]) -> AuditAction | None:
    by_id = {check.id: check for check in checks}
    for check_id in RECOMMENDATION_ORDER:
        check = by_id.get(check_id)
        if check is None or check.status in {"pass", "skip", "qualified", "profile_skip"}:
            continue
        return action_from_check(check)
    return None


def _apply_profile(checks: list[AuditCheck], profile: AuditProfile | None) -> list[AuditCheck]:
    if profile is None:
        return checks

    output: list[AuditCheck] = []
    for check in checks:
        disposition = profile.checks.get(check.id)
        if disposition is None or check.status != "warn":
            output.append(check)
            continue

        if disposition.disposition == "skip":
            output.append(
                AuditCheck(
                    id=check.id,
                    category=check.category,
                    name=check.name,
                    status="profile_skip",
                    detail=f"{check.detail} Repository profile skipped this check: {disposition.reason}",
                    recommendation="",
                )
            )
            continue

        output.append(
            AuditCheck(
                id=check.id,
                category=check.category,
                name=check.name,
                status="qualified",
                detail=f"{check.detail} Repository profile qualified this check: {disposition.reason}",
                recommendation=check.recommendation,
            )
        )
    return output


def _profile_markdown(profile: AuditProfile | None) -> list[str]:
    if profile is None:
        return []
    return [
        "## Repository Context",
        "",
        *key_value_table(
            [
                ("Declared purpose", profile.purpose),
                ("Profile source", "repository-owned `open-growth-loop.toml`"),
                ("Declared dispositions", len(profile.checks)),
            ]
        ),
        "",
        "This context is supplied by the repository owner and is not independently verified. Profile-qualified and profile-skipped checks remain in the score denominator and never count as passes; checks skipped because evidence is unavailable are reported separately.",
        "",
    ]


def _readme_text(repo: Path) -> str:
    for name in README_NAMES:
        path = repo / name
        if path.is_file():
            try:
                return path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                return ""
    return ""


def _readme_check(repo: Path, readme_text: str) -> AuditCheck:
    if not any((repo / name).is_file() for name in README_NAMES):
        return AuditCheck("readme", "essentials", "README", "fail", "No README file was found.", "Add a README that explains what the project does and how to use it.")
    if len(readme_text.strip()) < THIN_README_CHARS:
        return AuditCheck(
            "readme",
            "essentials",
            "README",
            "warn",
            f"README is under {THIN_README_CHARS} characters; a visitor cannot judge the project from it.",
            "Expand the README with a one-line pitch, install command, and usage example.",
        )
    return AuditCheck("readme", "essentials", "README", "pass", "README is present with enough content to evaluate the project.", "")


def _license_check(repo: Path) -> AuditCheck:
    if any(path.is_file() and (path.name.upper().startswith(LICENSE_PREFIXES) or path.name.upper() == "UNLICENSE") for path in repo.iterdir()):
        return AuditCheck("license", "essentials", "License", "pass", "A license file is present.", "")
    return AuditCheck(
        "license",
        "essentials",
        "License",
        "fail",
        "No license file was found; without one, others cannot legally reuse the project.",
        "Add a LICENSE file so the project is actually open source.",
    )


def _install_check(readme_text: str) -> AuditCheck:
    if INSTALL_PATTERN.search(readme_text) or INSTALL_HEADING_PATTERN.search(readme_text):
        return AuditCheck("install", "onboarding", "Install instructions", "pass", "README shows how to install the project.", "")
    return AuditCheck(
        "install",
        "onboarding",
        "Install instructions",
        "warn",
        "README has no recognizable install command or Install section.",
        "Add an Install section with the exact command a new user runs.",
    )


def _quickstart_check(readme_text: str) -> AuditCheck:
    code_blocks = readme_text.count("```") // 2
    if code_blocks >= 1 and QUICKSTART_HEADING_PATTERN.search(readme_text):
        return AuditCheck("quickstart", "onboarding", "Quickstart", "pass", "README has a usage section with at least one code example.", "")
    return AuditCheck(
        "quickstart",
        "onboarding",
        "Quickstart",
        "warn",
        "README has no usage section with a copy-pasteable example.",
        "Add a Quickstart section with one runnable example and its expected output.",
    )


def _docs_check(repo: Path, readme_text: str) -> AuditCheck:
    for name in ("docs", "doc"):
        directory = repo / name
        if directory.is_dir() and any(directory.iterdir()):
            return AuditCheck("docs", "onboarding", "Documentation", "pass", f"A {name}/ directory is present.", "")
    if DOCS_LINK_PATTERN.search(readme_text):
        return AuditCheck("docs", "onboarding", "Documentation", "pass", "README links to documentation.", "")
    return AuditCheck(
        "docs",
        "onboarding",
        "Documentation",
        "warn",
        "No docs/ directory or documentation link was found.",
        "Add a docs/ directory or link a documentation site from the README.",
    )


def _examples_check(repo: Path, readme_text: str) -> AuditCheck:
    for name in ("examples", "example"):
        directory = repo / name
        if directory.is_dir() and any(directory.iterdir()):
            return AuditCheck("examples", "onboarding", "Examples", "pass", f"An {name}/ directory is present.", "")
    if QUICKSTART_HEADING_PATTERN.search(readme_text) and readme_text.count("```") // 2 >= 2:
        return AuditCheck("examples", "onboarding", "Examples", "pass", "README contains multiple worked examples.", "")
    return AuditCheck(
        "examples",
        "onboarding",
        "Examples",
        "warn",
        "No examples/ directory or worked README examples were found.",
        "Add at least one small, runnable example.",
    )


def _community_file_check(repo: Path, check_id: str, category: str, name: str, filename: str) -> AuditCheck:
    for directory in COMMUNITY_DIRS:
        path = repo / directory / filename if directory else repo / filename
        if path.is_file():
            return AuditCheck(check_id, category, name, "pass", f"{filename} is present.", "")
    return AuditCheck(
        check_id,
        category,
        name,
        "warn",
        f"No {filename} was found in the repository root, .github/, or docs/.",
        f"Add a {filename}.",
    )


def _security_policy_check(repo: Path, readme_text: str) -> AuditCheck:
    for directory in COMMUNITY_DIRS:
        path = repo / directory / "SECURITY.md" if directory else repo / "SECURITY.md"
        if path.is_file():
            return AuditCheck("security_policy", "community", "Security policy", "pass", "SECURITY.md is present.", "")
    if SECURITY_GUIDANCE_PATTERN.search(readme_text):
        return AuditCheck(
            "security_policy",
            "community",
            "Security policy",
            "pass",
            "README contains explicit vulnerability-reporting guidance.",
            "",
        )
    return AuditCheck(
        "security_policy",
        "community",
        "Security policy",
        "warn",
        "No SECURITY.md or README vulnerability-reporting guidance was found.",
        "Add a SECURITY.md.",
    )


def _issue_templates_check(repo: Path) -> AuditCheck:
    template_dir = repo / ".github" / "ISSUE_TEMPLATE"
    if template_dir.is_dir() and any(template_dir.iterdir()):
        return AuditCheck("issue_templates", "community", "Issue templates", "pass", "Issue templates are present.", "")
    return AuditCheck(
        "issue_templates",
        "community",
        "Issue templates",
        "warn",
        "No .github/ISSUE_TEMPLATE directory was found.",
        "Add bug-report and feature-request issue templates.",
    )


def _pr_template_check(repo: Path) -> AuditCheck:
    candidates = [
        repo / ".github" / "pull_request_template.md",
        repo / ".github" / "PULL_REQUEST_TEMPLATE.md",
        repo / "pull_request_template.md",
        repo / "PULL_REQUEST_TEMPLATE.md",
    ]
    if any(path.is_file() for path in candidates):
        return AuditCheck("pr_template", "community", "Pull request template", "pass", "A pull request template is present.", "")
    return AuditCheck(
        "pr_template",
        "community",
        "Pull request template",
        "warn",
        "No pull request template was found.",
        "Add a pull request template asking what changed, why, and how it was tested.",
    )


def _changelog_check(repo: Path) -> AuditCheck:
    if any((repo / name).is_file() for name in CHANGELOG_NAMES):
        return AuditCheck("changelog", "release", "Changelog", "pass", "A changelog file is present.", "")
    return AuditCheck(
        "changelog",
        "release",
        "Changelog",
        "warn",
        "No changelog file was found; users cannot see what changed between releases.",
        "Add a CHANGELOG.md and keep it updated with every release.",
    )


def _ci_check(repo: Path) -> AuditCheck:
    workflows = repo / ".github" / "workflows"
    if workflows.is_dir() and any(path.suffix in {".yml", ".yaml"} for path in workflows.iterdir() if path.is_file()):
        return AuditCheck("ci", "automation", "Continuous integration", "pass", "GitHub Actions workflows are present.", "")
    if any((repo / path).exists() for path in CI_PATHS):
        return AuditCheck("ci", "automation", "Continuous integration", "pass", "A CI configuration is present.", "")
    return AuditCheck(
        "ci",
        "automation",
        "Continuous integration",
        "warn",
        "No CI configuration was found; contributors cannot see whether tests pass.",
        "Add a CI workflow that installs the project and runs its tests.",
    )


def _release_tags_check(repo: Path) -> AuditCheck:
    if not (repo / ".git").exists():
        return AuditCheck("release_tags", "release", "Release tags", "skip", "Not a git repository; tag history was not checked.", "")

    latest_tag = _git(repo, "describe", "--tags", "--abbrev=0")
    if latest_tag is None:
        commits = _git_int(repo, "rev-list", "--count", "HEAD")
        if commits is None:
            return AuditCheck("release_tags", "release", "Release tags", "skip", "Git history could not be read; tag history was not checked.", "")
        if commits >= NO_TAG_COMMIT_WARNING:
            return AuditCheck(
                "release_tags",
                "release",
                "Release tags",
                "warn",
                f"No tagged release yet after {commits} commits.",
                "Tag a first release so users can pin a known-good version.",
            )
        return AuditCheck("release_tags", "release", "Release tags", "pass", f"Early history ({commits} commit(s)); no tagged release expected yet.", "")

    commits_since = _git_int(repo, "rev-list", "--count", f"{latest_tag}..HEAD")
    if commits_since is not None and commits_since >= COMMITS_SINCE_TAG_WARNING:
        return AuditCheck(
            "release_tags",
            "release",
            "Release tags",
            "warn",
            f"{commits_since} commits since {latest_tag}; unreleased work is piling up.",
            "Update the changelog and tag a release.",
        )
    return AuditCheck("release_tags", "release", "Release tags", "pass", f"Latest tag is {latest_tag}.", "")


def _git_int(repo: Path, *args: str) -> int | None:
    value = _git(repo, *args)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _git(repo: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None
