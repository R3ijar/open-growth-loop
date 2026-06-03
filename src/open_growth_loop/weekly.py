from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Mapping

from .inventory import read_inventory
from .io_utils import read_csv_rows, today_iso
from .reporting import key_value_table, markdown_table


@dataclass(frozen=True)
class WeeklyReview:
    generated_on: str
    inventory_counts: dict[str, int]
    experiment_counts: dict[str, int]
    staged_assets: list[str]
    waiting_for_artifact: list[dict[str, str]]
    ready_for_review: list[dict[str, str]]
    waiting_for_data: list[dict[str, str]]
    stale_work: list[dict[str, str]]
    next_attention: list[str]


def build_weekly_review(
    inventory_path: Path,
    ledger_path: Path,
    aliases: Mapping[str, Mapping[str, str]] | None = None,
    today: str | None = None,
    stale_planned_days: int = 14,
    stale_shipped_days: int = 21,
) -> WeeklyReview:
    aliases = aliases or {}
    today = today or today_iso()
    inventory = read_inventory(inventory_path, aliases.get("content_inventory"))
    experiments = read_csv_rows(ledger_path, aliases.get("experiments"))

    inventory_counts = dict(Counter(item.status or "unknown" for item in inventory))
    experiment_counts = dict(Counter((row.get("status") or "unknown").strip() for row in experiments))
    staged_assets = [item.asset for item in inventory if item.status == "staged" and item.asset]

    waiting_for_artifact: list[dict[str, str]] = []
    ready_for_review: list[dict[str, str]] = []
    waiting_for_data: list[dict[str, str]] = []
    stale_work: list[dict[str, str]] = []
    for row in experiments:
        status = (row.get("status") or "planned").strip()
        artifact = (row.get("artifact") or "").strip()
        summary = _experiment_summary(row)
        if status in {"planned", "staged"} or not artifact:
            waiting_for_artifact.append(summary)
            stale = _stale_artifact_issue(row, today, stale_planned_days)
            if stale:
                stale_work.append(stale)
            continue
        if status == "shipped" and (row.get("review_after") or "") <= today:
            ready_for_review.append(summary)
            stale_work.append(_stale_review_issue(row, today))
            continue
        if status == "shipped":
            waiting_for_data.append(summary)
            stale = _stale_shipped_wait_issue(row, today, stale_shipped_days)
            if stale:
                stale_work.append(stale)

    return WeeklyReview(
        generated_on=today,
        inventory_counts=inventory_counts,
        experiment_counts=experiment_counts,
        staged_assets=staged_assets,
        waiting_for_artifact=waiting_for_artifact,
        ready_for_review=ready_for_review,
        waiting_for_data=waiting_for_data,
        stale_work=stale_work,
        next_attention=_next_attention(staged_assets, stale_work, waiting_for_artifact, ready_for_review),
    )


def render_weekly_review(review: WeeklyReview) -> str:
    lines = [
        "# Weekly Growth Loop Review",
        "",
        "## Summary",
        "",
        *key_value_table(
            [
                ("Generated", review.generated_on),
                ("Staged assets", len(review.staged_assets)),
                ("Waiting for artifact", len(review.waiting_for_artifact)),
                ("Ready for review", len(review.ready_for_review)),
                ("Waiting for more data", len(review.waiting_for_data)),
                ("Stale work", len(review.stale_work)),
            ]
        ),
        "",
        "## Inventory State",
        "",
    ]
    lines.extend(_count_table(review.inventory_counts))
    lines.extend(["", "## Experiment State", ""])
    lines.extend(_count_table(review.experiment_counts))
    lines.extend(["", "## Staged Assets", ""])
    lines.extend(_list_lines(review.staged_assets, "No staged assets."))
    lines.extend(["", "## Waiting For Artifact", ""])
    lines.extend(_experiment_table(review.waiting_for_artifact, "No experiments are waiting for artifact evidence."))
    lines.extend(["", "## Ready For Review", ""])
    lines.extend(_experiment_table(review.ready_for_review, "No shipped experiments are ready for review."))
    lines.extend(["", "## Waiting For More Data", ""])
    lines.extend(_experiment_table(review.waiting_for_data, "No shipped experiments are waiting for more data."))
    lines.extend(["", "## Stale Work", ""])
    lines.extend(_stale_table(review.stale_work, "No stale work detected."))
    lines.extend(["", "## Next Attention", ""])
    lines.extend(_list_lines(review.next_attention, "Generate the next plan."))
    return "\n".join(lines) + "\n"


def _experiment_summary(row: Mapping[str, str]) -> dict[str, str]:
    return {
        "id": row.get("id", ""),
        "asset": row.get("asset", ""),
        "status": row.get("status", ""),
        "review_after": row.get("review_after", ""),
        "artifact": row.get("artifact", ""),
    }


def _next_attention(
    staged_assets: list[str],
    stale_work: list[dict[str, str]],
    waiting_for_artifact: list[dict[str, str]],
    ready_for_review: list[dict[str, str]],
) -> list[str]:
    if stale_work:
        first = stale_work[0]
        target = first.get("asset") or first.get("id") or "stale work"
        return [f"Resolve stale work for {target}: {first.get('reason', 'needs attention')}."]
    if staged_assets:
        return [f"Verify release evidence for {staged_assets[0]}."]
    if waiting_for_artifact:
        asset = waiting_for_artifact[0].get("asset") or waiting_for_artifact[0].get("id") or "the oldest experiment"
        return [f"Ship or record artifact evidence for {asset}."]
    if ready_for_review:
        return ["Run review-experiments and inspect shipped changes with enough elapsed time."]
    return ["Generate a fresh daily plan from current aggregate data."]


def _count_lines(counts: dict[str, int]) -> list[str]:
    if not counts:
        return ["No rows found."]
    return [f"- {name}: {count}" for name, count in sorted(counts.items())]


def _count_table(counts: dict[str, int]) -> list[str]:
    if not counts:
        return ["No rows found."]
    return markdown_table(["State", "Count"], sorted(counts.items()))


def _list_lines(items: list[str], empty: str) -> list[str]:
    if not items:
        return [empty]
    return [f"- {item}" for item in items]


def _experiment_lines(items: list[dict[str, str]], empty: str) -> list[str]:
    if not items:
        return [empty]
    lines: list[str] = []
    for item in items:
        label = item.get("id") or "unknown"
        asset = item.get("asset") or "none"
        status = item.get("status") or "unknown"
        review_after = item.get("review_after") or "unset"
        artifact = item.get("artifact") or "none"
        lines.append(f"- {label}: {asset} ({status}, review_after={review_after}, artifact={artifact})")
    return lines


def _experiment_table(items: list[dict[str, str]], empty: str) -> list[str]:
    if not items:
        return [empty]
    return markdown_table(
        ["ID", "Asset", "Status", "Review after", "Artifact"],
        [
            (
                item.get("id") or "unknown",
                item.get("asset") or "none",
                item.get("status") or "unknown",
                item.get("review_after") or "unset",
                item.get("artifact") or "none",
            )
            for item in items
        ],
    )


def _stale_lines(items: list[dict[str, str]], empty: str) -> list[str]:
    if not items:
        return [empty]
    lines: list[str] = []
    for item in items:
        label = item.get("id") or "unknown"
        asset = item.get("asset") or "none"
        reason = item.get("reason") or "needs attention"
        age = item.get("age_days")
        suffix = f", age_days={age}" if age else ""
        lines.append(f"- {label}: {asset} [{item.get('kind', 'stale')}] {reason}{suffix}")
    return lines


def _stale_table(items: list[dict[str, str]], empty: str) -> list[str]:
    if not items:
        return [empty]
    return markdown_table(
        ["ID", "Asset", "Kind", "Age", "Reason"],
        [
            (
                item.get("id") or "unknown",
                item.get("asset") or "none",
                item.get("kind") or "stale",
                item.get("age_days") or "n/a",
                item.get("reason") or "needs attention",
            )
            for item in items
        ],
    )


def _stale_artifact_issue(row: Mapping[str, str], today: str, stale_planned_days: int) -> dict[str, str] | None:
    summary = _experiment_summary(row)
    status = (row.get("status") or "planned").strip()
    if status == "shipped" and not (row.get("artifact") or "").strip():
        return _stale_summary(summary, "missing_artifact", "Shipped experiment has no artifact evidence.", row.get("shipped_on", ""), today)

    review_after = row.get("review_after") or ""
    if review_after and review_after <= today:
        return _stale_summary(summary, "artifact_overdue", "Experiment reached review_after before artifact evidence was recorded.", review_after, today)

    planned_on = row.get("planned_on") or ""
    age = _age_days(planned_on, today)
    if age is not None and age >= stale_planned_days:
        stale = _stale_summary(summary, "planned_stale", f"Experiment has waited at least {stale_planned_days} days without artifact evidence.", planned_on, today)
        return stale
    return None


def _stale_review_issue(row: Mapping[str, str], today: str) -> dict[str, str]:
    summary = _experiment_summary(row)
    review_after = row.get("review_after") or ""
    return _stale_summary(summary, "review_ready", "Shipped experiment is ready for review.", review_after, today)


def _stale_shipped_wait_issue(row: Mapping[str, str], today: str, stale_shipped_days: int) -> dict[str, str] | None:
    shipped_on = row.get("shipped_on") or ""
    age = _age_days(shipped_on, today)
    if age is not None and age >= stale_shipped_days:
        return _stale_summary(
            _experiment_summary(row),
            "shipped_stale",
            f"Shipped experiment has waited at least {stale_shipped_days} days without becoming review-ready.",
            shipped_on,
            today,
        )
    return None


def _stale_summary(summary: dict[str, str], kind: str, reason: str, start_date: str, today: str) -> dict[str, str]:
    stale = dict(summary)
    stale["kind"] = kind
    stale["reason"] = reason
    age = _age_days(start_date, today)
    stale["age_days"] = str(age) if age is not None else ""
    return stale


def _age_days(start_date: str, today: str) -> int | None:
    start = _parse_iso_date(start_date)
    end = _parse_iso_date(today)
    if not start or not end:
        return None
    return (end - start).days


def _parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
