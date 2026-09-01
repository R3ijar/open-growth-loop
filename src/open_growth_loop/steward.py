"""Local maintainer briefing built from repository and git evidence."""

from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from .audit import AuditAction, RepoAudit, build_repo_audit
from .config import AuditProfile
from .github_evidence import GitHubItem, GitHubSnapshot
from .io_utils import today_iso, write_json_report, write_text_report
from .reporting import collapsible_section, key_value_table, status_label


@dataclass(frozen=True)
class GitSnapshot:
    available: bool
    branch: str
    clean: bool | None
    changed_paths: int
    latest_tag: str
    commits_since_tag: int | None
    commits_90d: int | None
    active_authors_90d: int | None


@dataclass(frozen=True)
class StewardAction:
    kind: str
    title: str
    reason: str
    confidence: str
    evidence: list[str]
    steps: list[str]


@dataclass(frozen=True)
class StewardBrief:
    generated_at: str
    repo: str
    project_name: str
    status: str
    audit: RepoAudit
    git: GitSnapshot
    github: GitHubSnapshot | None
    action: StewardAction


def build_steward_brief(
    repo: Path,
    generated_at: str | None = None,
    github: GitHubSnapshot | None = None,
    audit_profile: AuditProfile | None = None,
) -> StewardBrief:
    generated_at = generated_at or today_iso()
    audit = build_repo_audit(repo, generated_at=generated_at, audit_profile=audit_profile)
    git = _read_git_snapshot(repo)
    action = _select_action(audit, git, github)
    remote_warn = bool(github and (not github.available or github.failing_default_branch_runs))
    status = (
        "fail"
        if audit.score["fail"]
        else ("warn" if audit.score["warn"] or audit.score["qualified"] or audit.score["profile_skipped"] or git.clean is False or remote_warn else "pass")
    )
    return StewardBrief(generated_at, str(repo), repo.name or str(repo), status, audit, git, github, action)


def render_steward_markdown(brief: StewardBrief) -> str:
    git = brief.git
    action = brief.action
    clean = "not available" if git.clean is None else ("yes" if git.clean else "no")
    lines = [
        "# Maintainer Brief",
        "",
        (
            "A local evidence packet plus an opt-in, read-only GitHub snapshot. It selects one reviewable maintenance action without mutating remote state."
            if brief.github
            else "A local evidence packet that selects one reviewable maintenance action. It does not fetch remote issues, pull requests, CI logs, or adoption metrics."
        ),
        "",
        "## Decision",
        "",
        *key_value_table(
            [
                ("Repository", brief.project_name),
                ("Generated at", brief.generated_at),
                ("Status", status_label(brief.status)),
                ("Next action", action.title),
                ("Why now", action.reason),
                ("Confidence", action.confidence),
            ]
        ),
        "",
        "## Local Evidence",
        "",
        *key_value_table(
            [
                ("Audit score", f"{brief.audit.score['percent']}% ({brief.audit.score['pass']} of {brief.audit.score['total']} checks pass)"),
                ("Audit warnings", brief.audit.score["warn"]),
                ("Audit failures", brief.audit.score["fail"]),
                ("Git available", "yes" if git.available else "no"),
                ("Branch", git.branch or "not available"),
                ("Working tree clean", clean),
                ("Changed paths", git.changed_paths),
                ("Latest tag", git.latest_tag or "none"),
                ("Commits since tag", git.commits_since_tag if git.commits_since_tag is not None else "not available"),
                ("Commits in 90 days", git.commits_90d if git.commits_90d is not None else "not available"),
                ("Active authors in 90 days", git.active_authors_90d if git.active_authors_90d is not None else "not available"),
            ]
        ),
        "",
        "Evidence used for this decision:",
        "",
        *(f"- {item}" for item in action.evidence),
        "",
        *_github_markdown(brief.github),
        "## One Next Action",
        "",
        *(f"- [ ] {step}" for step in action.steps),
        "",
        "## Safety Boundary",
        "",
        "- Review the evidence before changing files.",
        "- Do not push, publish, comment, label, merge, or close remote work without explicit approval.",
        "- Do not invent users, downloads, security impact, or ecosystem-importance claims.",
        (
            "- GitHub evidence was fetched read-only through gh; verify details in GitHub before acting."
            if brief.github and brief.github.available
            else "- Verify remote issue, pull-request, CI, and release state separately when those signals matter."
        ),
        "",
        *collapsible_section("Agent handoff prompt", ["```text", *render_steward_prompt(brief).splitlines(), "```"]),
        "",
    ]
    return "\n".join(lines)


def render_steward_prompt(brief: StewardBrief) -> str:
    evidence = "\n".join(f"- {item}" for item in brief.action.evidence)
    steps = "\n".join(f"- {step}" for step in brief.action.steps)
    return f"""Help maintain {brief.project_name} by completing one evidence-backed action.

Action: {brief.action.title}
Reason: {brief.action.reason}
Confidence: {brief.action.confidence}

Local evidence:
{evidence}

Steps:
{steps}

Constraints:
- Inspect the relevant files and remote state before acting.
- Keep the change focused and reviewable.
- Do not invent adoption or impact claims.
- Run the repository's relevant checks.
- Do not push, publish, merge, close, label, or comment without explicit approval.
"""


def write_steward_reports(brief: StewardBrief, out_dir: Path) -> tuple[Path, Path, Path, Path]:
    md_path, md_history = write_text_report(out_dir / "latest-steward.md", render_steward_markdown(brief))
    json_path, json_history = write_json_report(out_dir / "latest-steward.json", asdict(brief))
    return md_path, md_history, json_path, json_history


def _select_action(audit: RepoAudit, git: GitSnapshot, github: GitHubSnapshot | None = None) -> StewardAction:
    if github and github.available and github.failing_run:
        run = github.failing_run
        return StewardAction(
            "github_ci",
            f"Investigate failing {github.default_branch} CI: {run.title}",
            "A failing default-branch workflow can block releases and reduce contributor confidence.",
            "high",
            [f"GitHub reports {github.failing_default_branch_runs} failing default-branch run(s).", _item_evidence(run)],
            ["Open the failing workflow log.", "Reproduce the smallest failing command locally.", "Patch the cause and run the relevant checks.", "Ask for approval before pushing."],
        )
    if audit.recommended_action is not None:
        return _audit_action(audit.recommended_action)
    if git.available and git.clean is False:
        return StewardAction(
            "working_tree",
            "Review and verify the current uncommitted work",
            f"The local working tree has {git.changed_paths} changed path(s), so starting more work would increase maintenance risk.",
            "medium",
            [f"git status reports {git.changed_paths} changed path(s).", "All repository-hygiene checks currently pass."],
            ["Inspect the complete diff.", "Identify and preserve unrelated or user-owned changes.", "Run the relevant tests and lint checks.", "Summarize the reviewable maintenance slice; do not commit or push without approval."],
        )
    if github and github.available and github.oldest_pull_request:
        pull_request = github.oldest_pull_request
        return StewardAction(
            "github_pull_request",
            f"Review pull request #{pull_request.number}: {pull_request.title}",
            "An open, non-draft pull request is direct contributor demand and should be reviewed before speculative backlog work.",
            "high",
            [_item_evidence(pull_request), f"GitHub reports {github.open_pull_requests} open pull request(s)."],
            ["Read the pull request summary and changed files.", "Verify its test and CI evidence.", "Choose a clear review outcome.", "Ask for approval before commenting, merging, or closing."],
        )
    if github and github.available and github.actionable_issue:
        issue = github.actionable_issue
        return StewardAction(
            "github_issue",
            f"Triage reproducible issue #{issue.number}: {issue.title}",
            "A bug-labeled public issue is stronger maintainer demand than a speculative feature.",
            "medium",
            [_item_evidence(issue), f"Labels: {', '.join(issue.labels) or 'none'}."],
            ["Confirm the reproduction and affected version.", "Identify the smallest safe fix or missing evidence.", "Run the relevant regression checks.", "Ask for approval before commenting, labeling, or closing."],
        )
    if git.commits_since_tag is not None and git.commits_since_tag >= 10:
        return StewardAction(
            "release",
            "Prepare a release from the accumulated changes",
            f"There are {git.commits_since_tag} commits since {git.latest_tag or 'the last release'}, while repository-hygiene checks pass.",
            "medium",
            [f"Latest tag: {git.latest_tag or 'none'}.", f"Commits since tag: {git.commits_since_tag}."],
            ["Review user-visible changes since the latest tag.", "Update the changelog and version metadata.", "Run the full release checks.", "Ask for approval before tagging or publishing."],
        )
    if github and github.available and github.oldest_issue:
        issue = github.oldest_issue
        return StewardAction(
            "github_issue_review",
            f"Review issue #{issue.number}: {issue.title}",
            "Local signals are healthy, so the oldest current issue is the best available source of maintainer demand.",
            "medium",
            [_item_evidence(issue), f"GitHub reports {github.open_issues} open issue(s)."],
            ["Read the issue and linked evidence.", "Decide whether it is actionable, needs information, or is out of scope.", "Record the smallest next step.", "Ask for approval before changing remote state."],
        )
    if github and github.available:
        return StewardAction(
            "wait_for_signal",
            "Keep the repository healthy and wait for stronger demand",
            "The local audit is healthy and the read-only GitHub snapshot found no open issue, pull request, or failing default-branch workflow.",
            "high",
            ["All counted repository-hygiene checks pass.", "The current GitHub snapshot found no actionable maintainer queue."],
            ["Avoid adding speculative scope.", "Recheck after new maintainer or contributor evidence arrives.", "Use the time for outreach or documentation validation rather than invented feature work."],
        )
    return StewardAction(
        "remote_review",
        "Review the live issue and pull-request queue before changing code",
        "Local repository signals look healthy, so the next action should come from real maintainer demand rather than another speculative feature.",
        "medium",
        ["All counted repository-hygiene checks pass.", "Remote issues, pull requests, CI runs, and adoption signals were not fetched."],
        ["Read the oldest open issue and pull request with current remote data.", "Identify one blocked user or contributor outcome.", "Record the evidence and choose the smallest action that unblocks it.", "Ask for approval before mutating remote state."],
    )


def _github_markdown(github: GitHubSnapshot | None) -> list[str]:
    if github is None:
        return []
    lines = ["## Read-only GitHub Evidence", ""]
    if not github.available:
        lines.extend([f"GitHub evidence for `{github.repo}` was unavailable: {github.error}", ""])
        return lines
    lines.extend(
        [
            *key_value_table(
                [
                    ("Repository", github.repo),
                    ("Default branch", github.default_branch),
                    ("Open issues", github.open_issues),
                    ("Open pull requests", github.open_pull_requests),
                    ("Currently failing default-branch workflows", github.failing_default_branch_runs),
                    ("Latest release", github.latest_release or "none"),
                    ("Latest release date", github.latest_release_at or "not available"),
                ]
            ),
            "",
        ]
    )
    return lines


def _item_evidence(item: GitHubItem) -> str:
    suffix = f" ({item.url})" if item.url else ""
    return f"#{item.number} {item.title}{suffix}."


def _audit_action(action: AuditAction) -> StewardAction:
    return StewardAction(
        "repository_gap",
        action.title,
        action.reason,
        action.confidence,
        [f"Repository audit selected the '{action.check_id}' gap as the highest-priority non-pass check."],
        list(action.next_steps),
    )


def _read_git_snapshot(repo: Path) -> GitSnapshot:
    if _git(repo, "rev-parse", "--is-inside-work-tree") != "true":
        return GitSnapshot(False, "", None, 0, "", None, None, None)
    # Ignore this tool's own report directory so a second run does not
    # recommend reviewing files that Open Growth Loop just generated.
    status = _git(repo, "status", "--porcelain", "--", ".", ":(top,exclude)outbox", allow_empty=True)
    changed_paths = len([line for line in (status or "").splitlines() if line.strip()])
    latest_tag = _git(repo, "describe", "--tags", "--abbrev=0") or ""
    commits_since_tag = _git_int(repo, "rev-list", "--count", f"{latest_tag}..HEAD") if latest_tag else _git_int(repo, "rev-list", "--count", "HEAD")
    authors = _git(repo, "log", "--since=90.days", "--format=%aN", allow_empty=True) or ""
    active_authors = len({author.strip() for author in authors.splitlines() if author.strip()})
    return GitSnapshot(
        True,
        _git(repo, "branch", "--show-current") or "",
        changed_paths == 0,
        changed_paths,
        latest_tag,
        commits_since_tag,
        _git_int(repo, "rev-list", "--count", "--since=90.days", "HEAD"),
        active_authors,
    )


def _git_int(repo: Path, *args: str) -> int | None:
    value = _git(repo, *args)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _git(repo: Path, *args: str, allow_empty: bool = False) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value if value or allow_empty else None
