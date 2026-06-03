from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .candidates import build_candidates
from .config import GrowthConfig
from .freshness import build_freshness_report
from .io_utils import first_existing, write_json_report, write_text_report
from .planner import build_daily_plan, default_data_paths, default_memory_path
from .privacy import scan_privacy
from .release_brief import build_release_brief
from .reporting import compact_join, key_value_table, markdown_table, status_label
from .workspace import validate_workspace


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class DoctorReport:
    ok: bool
    workspace: str
    checks: list[DoctorCheck]
    next_steps: list[str]


def build_doctor_report(workspace: Path, config: GrowthConfig, include_tests: bool = False) -> DoctorReport:
    inventory, search_rows, events = default_data_paths(workspace)
    data_dir = workspace / "data"
    experiments = first_existing([data_dir / "experiments.csv", data_dir / "experiments.example.csv"])
    memory = default_memory_path(workspace)

    validation = validate_workspace(workspace, config)
    freshness = build_freshness_report(
        {
            "content_inventory": inventory,
            "search_rows": search_rows,
            "events": events,
            "experiments": experiments,
        },
        config.schema_aliases,
        warn_after_days=config.thresholds.freshness_warn_days,
    )
    privacy = scan_privacy(workspace, include_tests=include_tests)

    checks = [
        DoctorCheck(
            "Workspace validation",
            "pass" if validation.ok else "fail",
            "All required CSV schemas validate." if validation.ok else compact_join(validation.errors),
        ),
        DoctorCheck(
            "Data freshness",
            "pass" if freshness.ok else "warn",
            "Inputs are fresh enough for planning." if freshness.ok else compact_join(freshness.warnings),
        ),
        DoctorCheck(
            "Privacy scan",
            "pass" if privacy.ok else "fail",
            "No private-looking data was found." if privacy.ok else f"{len(privacy.findings)} finding(s) need review.",
        ),
    ]

    try:
        candidates = build_candidates(
            inventory,
            search_rows,
            events,
            minimum_impressions=config.thresholds.minimum_impressions,
            minimum_views=config.thresholds.minimum_views,
            weak_cta_rate=config.thresholds.weak_cta_rate,
            memory_path=memory,
            aliases=config.schema_aliases,
        )
        checks.append(
            DoctorCheck(
                "Candidate engine",
                "pass" if candidates else "warn",
                f"{len(candidates)} ranked candidate(s) available." if candidates else "No ranked candidates were available.",
            )
        )
    except Exception as exc:  # pragma: no cover - defensive CLI report
        checks.append(DoctorCheck("Candidate engine", "fail", str(exc)))

    try:
        plan = build_daily_plan(
            inventory,
            search_rows,
            events,
            minimum_impressions=config.thresholds.minimum_impressions,
            minimum_views=config.thresholds.minimum_views,
            weak_cta_rate=config.thresholds.weak_cta_rate,
            memory_path=memory,
            aliases=config.schema_aliases,
            freshness_warn_days=config.thresholds.freshness_warn_days,
        )
        actionable = plan.action_type != "wait_for_data"
        checks.append(
            DoctorCheck(
                "Daily plan",
                "pass" if actionable else "warn",
                f"{plan.action_type} for {plan.asset}." if actionable else plan.reason,
            )
        )
    except Exception as exc:  # pragma: no cover - defensive CLI report
        checks.append(DoctorCheck("Daily plan", "fail", str(exc)))

    try:
        release = build_release_brief(workspace, config, include_tests=include_tests)
        checks.append(
            DoctorCheck(
                "Release readiness",
                "pass" if release.ready else "warn",
                "Release brief is ready with manual review." if release.ready else compact_join(release.warnings),
            )
        )
    except Exception as exc:  # pragma: no cover - defensive CLI report
        checks.append(DoctorCheck("Release readiness", "warn", str(exc)))

    next_steps = _next_steps(checks)
    return DoctorReport(
        ok=not any(check.status == "fail" for check in checks),
        workspace=str(workspace),
        checks=checks,
        next_steps=next_steps,
    )


def render_doctor_markdown(report: DoctorReport) -> str:
    lines = [
        "# Maintainer Doctor",
        "",
        "A one-command readiness check for the local Open Growth Loop workspace.",
        "",
        "## Summary",
        "",
        *key_value_table(
            [
                ("Workspace", report.workspace),
                ("Overall status", status_label(report.ok)),
                ("Checks", len(report.checks)),
                ("Next steps", len(report.next_steps)),
            ]
        ),
        "",
        "## Checks",
        "",
        *markdown_table(
            ["Check", "Status", "Detail"],
            [(check.name, status_label(check.status), check.detail) for check in report.checks],
        ),
        "",
        "## Next Steps",
        "",
    ]
    lines.extend(f"- {step}" for step in report.next_steps)
    lines.append("")
    return "\n".join(lines)


def write_doctor_reports(report: DoctorReport, out_dir: Path) -> tuple[Path, Path, Path, Path]:
    md_path, md_history = write_text_report(out_dir / "latest-doctor.md", render_doctor_markdown(report))
    json_path, json_history = write_json_report(out_dir / "latest-doctor.json", asdict(report))
    return md_path, md_history, json_path, json_history


def _next_steps(checks: list[DoctorCheck]) -> list[str]:
    by_name = {check.name: check for check in checks}
    steps: list[str] = []
    if by_name.get("Workspace validation", DoctorCheck("", "pass", "")).status == "fail":
        steps.append("Run `ogl validate` and fix the listed CSV schema errors.")
    if by_name.get("Data freshness", DoctorCheck("", "pass", "")).status == "warn":
        steps.append("Refresh real CSV exports before trusting the next plan, or use sample data only for demos.")
    if by_name.get("Privacy scan", DoctorCheck("", "pass", "")).status == "fail":
        steps.append("Run `ogl privacy-scan` and remove private-looking fields or secret-like text before sharing reports.")
    if by_name.get("Candidate engine", DoctorCheck("", "pass", "")).status != "pass":
        steps.append("Add more aggregate evidence or planned assets so the candidate engine has useful choices.")
    if by_name.get("Daily plan", DoctorCheck("", "pass", "")).status != "pass":
        steps.append("Run `ogl plan` after validation and freshness are healthy enough for a concrete action.")
    if by_name.get("Release readiness", DoctorCheck("", "pass", "")).status == "warn":
        steps.append("Review `ogl release-brief` before tagging a release or making public claims.")
    if not steps:
        steps.append("Review `outbox/index.md`, ship one action, then record `ogl complete` and `ogl outcome`.")
    return steps
