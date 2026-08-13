from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from .io_utils import write_json_report, write_text_report
from .reporting import key_value_table, markdown_table, status_label


@dataclass(frozen=True)
class ReportIndexItem:
    name: str
    path: str
    description: str
    exists: bool
    updated_at: str


@dataclass(frozen=True)
class ReportIndex:
    workspace: str
    outbox: str
    reports: list[ReportIndexItem]

    @property
    def available_count(self) -> int:
        return sum(1 for report in self.reports if report.exists)

    @property
    def missing_count(self) -> int:
        return len(self.reports) - self.available_count

    @property
    def ready_for_review(self) -> bool:
        return self.missing_count == 0

    @property
    def missing_reports(self) -> list[str]:
        return [report.name for report in self.reports if not report.exists]


REPORTS = [
    ("Maintainer Brief", "steward/latest-steward.md", "One action selected from repository hygiene and local Git maintenance signals."),
    ("Repo Audit", "audit/latest-audit.md", "Zero-config repository hygiene check with one recommended next action."),
    ("Doctor", "doctor/latest-doctor.md", "One-shot readiness check across validation, freshness, privacy, planning, and release review."),
    ("Plan", "plans/latest-plan.md", "The selected daily maintainer action and decision trace."),
    ("Candidates", "candidates/latest-candidates.md", "All ranked actions considered by the conservative engine."),
    ("Freshness", "freshness/latest-freshness.md", "Whether local CSV inputs are recent enough to trust."),
    ("Query Backlog", "query-backlog.md", "Search Console-style opportunities ranked for review."),
    ("Issue Draft", "issues/latest-issue-draft.md", "A public-reviewable GitHub issue draft from the latest plan."),
    ("Prompt", "prompts/latest-prompt.md", "A focused Codex-ready prompt for the selected action."),
    ("Release Brief", "release-brief/latest-release-brief.md", "Release-readiness checks and public claim guardrails."),
    ("Weekly Review", "weekly-review.md", "Current operating state across inventory and experiments."),
    ("Experiment Review", "experiment-review.md", "Conservative outcome review for shipped experiments."),
    ("Privacy Scan", "privacy-scan.md", "Private-data leakage scan before sharing outputs."),
]


def build_report_index(workspace: Path) -> ReportIndex:
    outbox = workspace / "outbox"
    reports = [_report_item(outbox, name, rel_path, description) for name, rel_path, description in REPORTS]
    return ReportIndex(workspace=workspace.name or ".", outbox="outbox", reports=reports)


def render_report_index(index: ReportIndex) -> str:
    lines = [
        "# Open Growth Loop Report Index",
        "",
        "A local front page for the generated maintainer reports in this workspace.",
        "",
        "## Summary",
        "",
        *key_value_table(
            [
                ("Workspace", index.workspace),
                ("Reports available", index.available_count),
                ("Reports missing", index.missing_count),
                ("Review ready", "yes" if index.ready_for_review else "not yet"),
                ("Next missing report", index.missing_reports[0] if index.missing_reports else "none"),
            ]
        ),
        "",
        "## Report Map",
        "",
        *markdown_table(
            ["Report", "Status", "Updated", "Link", "What to review"],
            [
                (
                    item.name,
                    status_label(item.exists),
                    item.updated_at or "not generated",
                    _link(item),
                    item.description,
                )
                for item in index.reports
            ],
        ),
        "",
        "## Recommended Reading Order",
        "",
        "1. Start with `Maintainer Brief` for the local repository decision boundary.",
        "2. Use `Freshness` to confirm optional data-loop inputs are trustworthy enough.",
        "3. Read `Candidates` to see what the data loop considered.",
        "4. Use `Plan`, `Issue Draft`, and `Prompt` for one focused change.",
        "5. Check `Release Brief` before public release notes, applications, or broad claims.",
        "6. Return later to `Weekly Review`, `Experiment Review`, and `Outcome` commands to close the loop.",
        "",
    ]
    return "\n".join(lines)


def write_report_index(index: ReportIndex, out_dir: Path) -> tuple[Path, Path]:
    return write_text_report(out_dir / "index.md", render_report_index(index))


def write_report_index_json(index: ReportIndex, out_dir: Path) -> tuple[Path, Path]:
    return write_json_report(out_dir / "index.json", report_index_payload(index))


def report_index_payload(index: ReportIndex) -> dict[str, object]:
    return {
        "workspace": index.workspace,
        "outbox": index.outbox,
        "summary": {
            "available_count": index.available_count,
            "missing_count": index.missing_count,
            "ready_for_review": index.ready_for_review,
            "missing_reports": index.missing_reports,
        },
        "reports": [asdict(report) for report in index.reports],
    }


def _report_item(outbox: Path, name: str, rel_path: str, description: str) -> ReportIndexItem:
    path = outbox / rel_path
    updated_at = ""
    if path.exists():
        updated_at = datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
    return ReportIndexItem(
        name=name,
        path=rel_path.replace("\\", "/"),
        description=description,
        exists=path.exists(),
        updated_at=updated_at,
    )


def _link(item: ReportIndexItem) -> str:
    if not item.exists:
        return item.path
    return f"[{item.path}]({item.path})"
