from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

from .io_utils import read_csv_rows, write_json_report, write_text_report
from .reporting import key_value_table, markdown_table, status_label

DATE_FIELDS = {
    "events": ["date"],
    "experiments": ["shipped_on", "planned_on"],
}
FALLBACK_TO_MTIME = {"content_inventory", "search_rows"}
WARNING_STATUSES = {"stale", "missing", "empty", "future_dated", "unknown"}


@dataclass(frozen=True)
class FreshnessCheck:
    name: str
    path: str
    status: str
    source: str
    latest_date: str
    age_days: int | None
    reason: str


@dataclass(frozen=True)
class FreshnessReport:
    ok: bool
    checked_at: str
    warn_after_days: int
    checks: list[FreshnessCheck]
    warnings: list[str]


def build_freshness_report(
    paths: Mapping[str, Path],
    aliases: Mapping[str, Mapping[str, str]] | None = None,
    warn_after_days: int = 21,
    today: str | None = None,
) -> FreshnessReport:
    today_date = _today(today)
    checks = [
        _check_path(name, path, aliases.get(name, {}) if aliases else {}, warn_after_days, today_date)
        for name, path in paths.items()
    ]
    warnings = [f"{check.name}: {check.reason}" for check in checks if check.status in WARNING_STATUSES]
    return FreshnessReport(
        ok=not warnings,
        checked_at=today_date.isoformat(),
        warn_after_days=warn_after_days,
        checks=checks,
        warnings=warnings,
    )


def render_freshness_markdown(report: FreshnessReport) -> str:
    lines = [
        "# Data Freshness",
        "",
        "## Summary",
        "",
        *key_value_table(
            [
                ("Status", status_label(report.ok)),
                ("Checked at", report.checked_at),
                ("Warning window", f"{report.warn_after_days} days"),
                ("Inputs checked", len(report.checks)),
                ("Warnings", len(report.warnings)),
            ]
        ),
        "",
        "## Input Checks",
        "",
        *markdown_table(
            ["Input", "Status", "Source", "Latest", "Age", "Reason"],
            [
                (
                    check.name,
                    status_label(check.status),
                    check.source,
                    check.latest_date or "n/a",
                    "n/a" if check.age_days is None else f"{check.age_days} days",
                    check.reason,
                )
                for check in report.checks
            ],
        ),
    ]
    if report.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report.warnings)
    else:
        lines.extend(["", "## Warnings", "", "No stale-data warnings were found for the configured inputs."])
    lines.append("")
    return "\n".join(lines)


def write_freshness_reports(report: FreshnessReport, out_dir: Path) -> tuple[Path, Path, Path, Path]:
    md_path, md_history = write_text_report(out_dir / "latest-freshness.md", render_freshness_markdown(report))
    json_path, json_history = write_json_report(out_dir / "latest-freshness.json", asdict(report))
    return md_path, md_history, json_path, json_history


def _check_path(
    name: str,
    path: Path,
    aliases: Mapping[str, str],
    warn_after_days: int,
    today: date,
) -> FreshnessCheck:
    display_path = _display_path(path)
    if path.name.endswith(".example.csv"):
        return FreshnessCheck(
            name=name,
            path=display_path,
            status="sample",
            source="sample_file",
            latest_date="",
            age_days=None,
            reason="Sample data is bundled for demos; freshness is evaluated after copying to real data files.",
        )
    if not path.exists():
        return FreshnessCheck(name, display_path, "missing", "missing_file", "", None, f"{display_path} does not exist.")

    date_fields = DATE_FIELDS.get(name, [])
    if date_fields:
        rows = read_csv_rows(path, aliases)
        if not rows:
            return FreshnessCheck(name, display_path, "empty", "csv_rows", "", None, f"{display_path} has no rows.")
        latest = _latest_row_date(rows, date_fields)
        if latest is None:
            return FreshnessCheck(
                name,
                display_path,
                "unknown",
                "date_columns",
                "",
                None,
                f"No parseable date was found in {', '.join(date_fields)}.",
            )
        return _dated_check(name, display_path, "latest_date", latest, warn_after_days, today)

    if name in FALLBACK_TO_MTIME:
        return _mtime_check(name, display_path, path, warn_after_days, today)

    return FreshnessCheck(name, display_path, "unknown", "not_configured", "", None, "No freshness rule is configured for this input.")


def _dated_check(name: str, display_path: str, source: str, latest: date, warn_after_days: int, today: date) -> FreshnessCheck:
    age_days = (today - latest).days
    if age_days < 0:
        return FreshnessCheck(
            name,
            display_path,
            "future_dated",
            source,
            latest.isoformat(),
            age_days,
            f"Latest date {latest.isoformat()} is after the check date {today.isoformat()}.",
        )
    if age_days > warn_after_days:
        return FreshnessCheck(
            name,
            display_path,
            "stale",
            source,
            latest.isoformat(),
            age_days,
            f"Latest data is {age_days} days old, above the {warn_after_days}-day warning window.",
        )
    return FreshnessCheck(
        name,
        display_path,
        "fresh",
        source,
        latest.isoformat(),
        age_days,
        f"Latest data is within the {warn_after_days}-day warning window.",
    )


def _mtime_check(name: str, display_path: str, path: Path, warn_after_days: int, today: date) -> FreshnessCheck:
    modified = datetime.fromtimestamp(path.stat().st_mtime).date()
    if modified > today:
        # A modification time after the check date only means the file is
        # current relative to a historical reference date; future_dated is
        # reserved for dates parsed from data rows.
        return FreshnessCheck(
            name,
            display_path,
            "fresh",
            "file_modified",
            modified.isoformat(),
            0,
            f"File was modified after the check date {today.isoformat()}; treating it as current.",
        )
    return _dated_check(name, display_path, "file_modified", modified, warn_after_days, today)


def _latest_row_date(rows: list[Mapping[str, str]], fields: list[str]) -> date | None:
    dates: list[date] = []
    for row in rows:
        for field in fields:
            parsed = _parse_date(row.get(field, ""))
            if parsed:
                dates.append(parsed)
    return max(dates) if dates else None


def _parse_date(value: object) -> date | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _today(value: str | None) -> date:
    return date.fromisoformat(value) if value else date.today()


def _display_path(path: Path) -> str:
    if path.parent.name:
        return f"{path.parent.name}/{path.name}"
    return path.name
