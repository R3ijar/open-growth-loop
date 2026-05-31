from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .inventory import read_inventory
from .io_utils import read_csv_rows, today_iso


@dataclass(frozen=True)
class WeeklyReview:
    generated_on: str
    inventory_counts: dict[str, int]
    experiment_counts: dict[str, int]
    staged_assets: list[str]
    waiting_for_artifact: list[dict[str, str]]
    ready_for_review: list[dict[str, str]]
    waiting_for_data: list[dict[str, str]]
    next_attention: list[str]


def build_weekly_review(
    inventory_path: Path,
    ledger_path: Path,
    aliases: Mapping[str, Mapping[str, str]] | None = None,
    today: str | None = None,
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
    for row in experiments:
        status = (row.get("status") or "planned").strip()
        artifact = (row.get("artifact") or "").strip()
        summary = _experiment_summary(row)
        if status in {"planned", "staged"} or not artifact:
            waiting_for_artifact.append(summary)
            continue
        if status == "shipped" and (row.get("review_after") or "") <= today:
            ready_for_review.append(summary)
            continue
        if status == "shipped":
            waiting_for_data.append(summary)

    return WeeklyReview(
        generated_on=today,
        inventory_counts=inventory_counts,
        experiment_counts=experiment_counts,
        staged_assets=staged_assets,
        waiting_for_artifact=waiting_for_artifact,
        ready_for_review=ready_for_review,
        waiting_for_data=waiting_for_data,
        next_attention=_next_attention(staged_assets, waiting_for_artifact, ready_for_review),
    )


def render_weekly_review(review: WeeklyReview) -> str:
    lines = [
        "# Weekly Growth Loop Review",
        "",
        f"Generated: {review.generated_on}",
        "",
        "## Inventory",
        "",
    ]
    lines.extend(_count_lines(review.inventory_counts))
    lines.extend(["", "## Experiments", ""])
    lines.extend(_count_lines(review.experiment_counts))
    lines.extend(["", "## Staged Assets", ""])
    lines.extend(_list_lines(review.staged_assets, "No staged assets."))
    lines.extend(["", "## Waiting For Artifact", ""])
    lines.extend(_experiment_lines(review.waiting_for_artifact, "No experiments are waiting for artifact evidence."))
    lines.extend(["", "## Ready For Review", ""])
    lines.extend(_experiment_lines(review.ready_for_review, "No shipped experiments are ready for review."))
    lines.extend(["", "## Waiting For More Data", ""])
    lines.extend(_experiment_lines(review.waiting_for_data, "No shipped experiments are waiting for more data."))
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


def _next_attention(staged_assets: list[str], waiting_for_artifact: list[dict[str, str]], ready_for_review: list[dict[str, str]]) -> list[str]:
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
