from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .events import event_baseline, read_event_rollups
from .io_utils import future_iso, read_csv_rows, today_iso, write_csv_rows
from .planner import DailyPlan
from .search import read_search_rows, search_baseline

FIELDS = [
    "id",
    "status",
    "asset",
    "action_type",
    "planned_on",
    "review_after",
    "baseline_impressions",
    "baseline_clicks",
    "baseline_views",
    "baseline_conversions",
    "artifact",
    "note",
    "outcome",
]


@dataclass(frozen=True)
class ExperimentReview:
    id: str
    asset: str
    status: str
    outcome: str
    reason: str


def track_plan(
    plan: DailyPlan,
    ledger_path: Path,
    search_rows_path: Path,
    events_path: Path,
    review_days: int = 14,
    artifact: str = "",
    note: str = "",
) -> dict[str, object]:
    rows = read_csv_rows(ledger_path)
    experiment_id = f"{today_iso()}-{len(rows) + 1:03d}"
    search_rows = read_search_rows(search_rows_path)
    event_rollups = read_event_rollups(events_path)
    impressions, clicks = search_baseline(search_rows, plan.asset)
    views, conversions = event_baseline(event_rollups, plan.asset)
    row = {
        "id": experiment_id,
        "status": "planned",
        "asset": plan.asset,
        "action_type": plan.action_type,
        "planned_on": today_iso(),
        "review_after": future_iso(review_days),
        "baseline_impressions": impressions,
        "baseline_clicks": clicks,
        "baseline_views": views,
        "baseline_conversions": conversions,
        "artifact": artifact,
        "note": note or plan.title,
        "outcome": "",
    }
    rows.append(row)
    write_csv_rows(ledger_path, FIELDS, rows)
    return row


def review_experiments(
    ledger_path: Path,
    search_rows_path: Path,
    events_path: Path,
    minimum_impressions: int = 25,
    minimum_views: int = 25,
) -> list[ExperimentReview]:
    rows = read_csv_rows(ledger_path)
    search_rows = read_search_rows(search_rows_path)
    event_rollups = read_event_rollups(events_path)
    reviews: list[ExperimentReview] = []
    for row in rows:
        asset = row.get("asset", "")
        status = row.get("status", "planned")
        if status in {"planned", "staged"}:
            reviews.append(
                ExperimentReview(
                    id=row.get("id", ""),
                    asset=asset,
                    status=status,
                    outcome="not_publicly_applied",
                    reason="Planned or staged work should not be treated as evidence.",
                )
            )
            continue

        current_impressions, current_clicks = search_baseline(search_rows, asset)
        current_views, current_conversions = event_baseline(event_rollups, asset)
        if current_impressions < minimum_impressions and current_views < minimum_views:
            reviews.append(
                ExperimentReview(
                    id=row.get("id", ""),
                    asset=asset,
                    status=status,
                    outcome="insufficient_sample",
                    reason="Not enough search impressions or aggregate views to judge the change.",
                )
            )
            continue

        baseline_clicks = int(float(row.get("baseline_clicks") or 0))
        baseline_conversions = int(float(row.get("baseline_conversions") or 0))
        if current_clicks > baseline_clicks or current_conversions > baseline_conversions:
            outcome = "directionally_positive"
            reason = "Clicks or conversions improved versus the recorded baseline."
        else:
            outcome = "needs_iteration"
            reason = "Usable sample exists, but clicks and conversions have not improved yet."
        reviews.append(ExperimentReview(id=row.get("id", ""), asset=asset, status=status, outcome=outcome, reason=reason))
    return reviews


def render_reviews_markdown(reviews: list[ExperimentReview]) -> str:
    lines = ["# Experiment Review", ""]
    if not reviews:
        lines.append("No experiments found.")
        return "\n".join(lines) + "\n"
    for review in reviews:
        lines.extend(
            [
                f"## {review.id or 'unknown'}",
                "",
                f"- Asset: {review.asset or 'none'}",
                f"- Status: {review.status}",
                f"- Outcome: {review.outcome}",
                f"- Reason: {review.reason}",
                "",
            ]
        )
    return "\n".join(lines)
