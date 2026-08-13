"""Opt-in, read-only GitHub evidence for maintainer decisions."""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

Runner = Callable[[list[str]], str]


@dataclass(frozen=True)
class GitHubItem:
    number: str
    title: str
    url: str
    updated_at: str
    labels: list[str]


@dataclass(frozen=True)
class GitHubSnapshot:
    available: bool
    repo: str
    error: str
    default_branch: str
    open_issues: int
    open_pull_requests: int
    failing_default_branch_runs: int
    latest_release: str
    latest_release_at: str
    oldest_issue: GitHubItem | None
    actionable_issue: GitHubItem | None
    oldest_pull_request: GitHubItem | None
    failing_run: GitHubItem | None


def read_github_snapshot(repo: str, limit: int = 50, runner: Runner | None = None) -> GitHubSnapshot:
    """Read public maintainer signals with ``gh`` without mutating GitHub."""

    _validate_repo(repo)
    if limit < 1:
        raise ValueError("limit must be at least 1")
    run = runner or run_gh
    try:
        repo_payload = _gh_object(run, ["repo", "view", repo, "--json", "defaultBranchRef"])
        default_branch = str((repo_payload.get("defaultBranchRef") or {}).get("name") or "main")
        issues = _gh_list(
            run,
            [
                "issue",
                "list",
                "--repo",
                repo,
                "--state",
                "open",
                "--limit",
                str(limit),
                "--json",
                "number,title,labels,createdAt,updatedAt,url",
            ],
        )
        pull_requests = _gh_list(
            run,
            [
                "pr",
                "list",
                "--repo",
                repo,
                "--state",
                "open",
                "--limit",
                str(limit),
                "--json",
                "number,title,isDraft,statusCheckRollup,reviewDecision,createdAt,updatedAt,url",
            ],
        )
        runs = _gh_list(
            run,
            [
                "run",
                "list",
                "--repo",
                repo,
                "--branch",
                default_branch,
                "--limit",
                str(limit),
                "--json",
                "databaseId,workflowName,status,conclusion,headBranch,createdAt,url",
            ],
        )
        releases = _gh_list(
            run,
            [
                "release",
                "list",
                "--repo",
                repo,
                "--limit",
                "1",
                "--json",
                "tagName,publishedAt,createdAt,isDraft,isPrerelease,name",
            ],
        )
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        return unavailable_github_snapshot(repo, str(exc))

    issue_items = sorted((_issue_item(item) for item in issues), key=lambda item: item.updated_at)
    pr_items = sorted((_pr_item(item) for item in pull_requests if not bool(item.get("isDraft"))), key=lambda item: item.updated_at)
    failing_runs = [_run_item(item) for item in runs if _is_failure(item.get("conclusion"))]
    actionable = next((item for item in issue_items if _actionable_labels(item.labels)), None)
    latest_release = releases[0] if releases else {}
    return GitHubSnapshot(
        available=True,
        repo=repo,
        error="",
        default_branch=default_branch,
        open_issues=len(issues),
        open_pull_requests=len(pull_requests),
        failing_default_branch_runs=len(failing_runs),
        latest_release=str(latest_release.get("tagName") or ""),
        latest_release_at=str(latest_release.get("publishedAt") or latest_release.get("createdAt") or ""),
        oldest_issue=issue_items[0] if issue_items else None,
        actionable_issue=actionable,
        oldest_pull_request=pr_items[0] if pr_items else None,
        failing_run=failing_runs[0] if failing_runs else None,
    )


def unavailable_github_snapshot(repo: str, error: str) -> GitHubSnapshot:
    return GitHubSnapshot(False, repo, error, "", 0, 0, 0, "", "", None, None, None, None)


def run_gh(args: list[str]) -> str:
    gh = shutil.which("gh") or (str(Path("C:/Program Files/GitHub CLI/gh.exe")) if Path("C:/Program Files/GitHub CLI/gh.exe").exists() else "")
    if not gh:
        raise RuntimeError("GitHub CLI was not found; install gh and authenticate before using --github")
    completed = subprocess.run([gh, *args], capture_output=True, check=False, text=True, timeout=30)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(f"gh {' '.join(args[:3])} failed: {detail}")
    return completed.stdout


def _validate_repo(repo: str) -> None:
    parts = repo.split("/")
    if len(parts) != 2 or not all(part.strip() for part in parts):
        raise ValueError("repo must use owner/name format, for example R3ijar/open-growth-loop")


def _gh_list(run: Runner, args: list[str]) -> list[dict[str, object]]:
    payload = json.loads(run(args) or "[]")
    if not isinstance(payload, list):
        raise RuntimeError(f"gh {' '.join(args[:3])} returned a non-list JSON payload")
    return [item for item in payload if isinstance(item, dict)]


def _gh_object(run: Runner, args: list[str]) -> dict[str, object]:
    payload = json.loads(run(args) or "{}")
    if not isinstance(payload, dict):
        raise RuntimeError(f"gh {' '.join(args[:3])} returned a non-object JSON payload")
    return payload


def _issue_item(item: dict[str, object]) -> GitHubItem:
    return GitHubItem(
        str(item.get("number") or ""),
        str(item.get("title") or ""),
        str(item.get("url") or ""),
        str(item.get("createdAt") or item.get("updatedAt") or ""),
        _label_names(item.get("labels")),
    )


def _pr_item(item: dict[str, object]) -> GitHubItem:
    return GitHubItem(
        str(item.get("number") or ""),
        str(item.get("title") or ""),
        str(item.get("url") or ""),
        str(item.get("createdAt") or item.get("updatedAt") or ""),
        [],
    )


def _run_item(item: dict[str, object]) -> GitHubItem:
    return GitHubItem(
        str(item.get("databaseId") or ""),
        str(item.get("workflowName") or "GitHub Actions run"),
        str(item.get("url") or ""),
        str(item.get("createdAt") or ""),
        [str(item.get("conclusion") or "failure").lower()],
    )


def _label_names(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    labels: list[str] = []
    for item in value:
        name = item.get("name", "") if isinstance(item, dict) else item
        if str(name).strip():
            labels.append(str(name).strip())
    return labels


def _actionable_labels(labels: list[str]) -> bool:
    normalized = {label.lower().replace("-", "_").replace(" ", "_") for label in labels}
    return bool(normalized & {"bug", "repro", "reproduction", "reproducible", "minimal_repro"})


def _is_failure(value: object) -> bool:
    return str(value or "").strip().lower() in {"failure", "failed", "timed_out", "cancelled", "action_required", "startup_failure"}
