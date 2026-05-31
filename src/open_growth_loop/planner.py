from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .events import EventRollup, read_event_rollups
from .inventory import ContentItem, next_planned_item, read_inventory, staged_items
from .io_utils import ensure_parent, first_existing, write_json
from .search import SearchOpportunity, rank_search_opportunities, read_search_rows


@dataclass(frozen=True)
class DailyPlan:
    action_type: str
    asset: str
    title: str
    reason: str
    confidence: str
    next_steps: list[str]
    evidence: dict[str, object]


RELEASE_EVIDENCE_CHECKLIST = [
    "Open the public URL or release artifact for the staged asset.",
    "Confirm the asset is reachable from the expected public surface, such as docs navigation, README, package metadata, sitemap, or changelog.",
    "Confirm the published content matches the staged change and avoids unverified adoption or impact claims.",
    "Record the public artifact URL before tracking or reviewing the experiment.",
]


def release_evidence_checklist() -> list[str]:
    return list(RELEASE_EVIDENCE_CHECKLIST)


def build_daily_plan(
    inventory_path: Path,
    search_rows_path: Path,
    events_path: Path,
    minimum_impressions: int = 25,
    minimum_views: int = 25,
) -> DailyPlan:
    inventory = read_inventory(inventory_path)
    search_rows = read_search_rows(search_rows_path)
    event_rollups = read_event_rollups(events_path)

    staged = staged_items(inventory)
    if staged:
        item = staged[0]
        return DailyPlan(
            action_type="release_evidence",
            asset=item.asset,
            title=f"Verify staged release for {item.asset}",
            reason="Staged work should be proven public before creating another asset.",
            confidence="high",
            next_steps=release_evidence_checklist(),
            evidence={"status": item.status, "primary_query": item.primary_query, "owner_note": item.owner_note},
        )

    funnel = best_funnel_dropoff(event_rollups, minimum_views)
    if funnel:
        return DailyPlan(
            action_type="fix_funnel",
            asset=funnel.asset,
            title=f"Improve CTA path for {funnel.asset}",
            reason="Aggregate events show enough views but weak downstream movement.",
            confidence="medium",
            next_steps=[
                "Make the first payoff clearer above the fold.",
                "Move the primary CTA closer to the solved user problem.",
                "Track the change as an experiment before reviewing outcome.",
            ],
            evidence={
                "views": funnel.views,
                "ctas": funnel.ctas,
                "conversions": funnel.conversions,
                "cta_rate": round(funnel.cta_rate, 4),
                "conversion_rate": round(funnel.conversion_rate, 4),
            },
        )

    opportunities = rank_search_opportunities(search_rows, minimum_impressions)
    if opportunities:
        opportunity = opportunities[0]
        return DailyPlan(
            action_type=f"search_{opportunity.opportunity_type}",
            asset=opportunity.page,
            title=f"Improve search fit for {opportunity.page}",
            reason=opportunity.reason,
            confidence="medium",
            next_steps=[
                "Check whether the page answers the query directly.",
                "Improve the title, intro, example, or internal links without changing unrelated pages.",
                "Track the change and wait for enough impressions before reviewing.",
            ],
            evidence=asdict(opportunity),
        )

    planned = next_planned_item(inventory)
    if planned:
        return DailyPlan(
            action_type="create_asset",
            asset=planned.asset,
            title=f"Create planned {planned.type}: {planned.asset}",
            reason="No stronger measured opportunity is available, so use the next queued buyer/user-intent asset.",
            confidence="low",
            next_steps=[
                "Draft the smallest useful version.",
                "Connect it to the relevant docs, example, or project action.",
                "Mark it staged until public release evidence exists.",
            ],
            evidence={"primary_query": planned.primary_query, "cta": planned.cta, "owner_note": planned.owner_note},
        )

    return DailyPlan(
        action_type="wait_for_data",
        asset="",
        title="Wait for more evidence",
        reason="No staged release, funnel dropoff, search opportunity, or planned asset is available.",
        confidence="high",
        next_steps=[
            "Add rows to content inventory.",
            "Import aggregate event data.",
            "Export Search Console rows after the next data window.",
        ],
        evidence={},
    )


def write_plan_reports(plan: DailyPlan, out_dir: Path) -> tuple[Path, Path]:
    ensure_parent(out_dir / "placeholder")
    json_path = out_dir / "latest-plan.json"
    md_path = out_dir / "latest-plan.md"
    write_json(json_path, asdict(plan))
    md_path.write_text(render_plan_markdown(plan), encoding="utf-8")
    return md_path, json_path


def default_data_paths(workspace: Path) -> tuple[Path, Path, Path]:
    data_dir = workspace / "data"
    inventory = first_existing([data_dir / "content_inventory.csv", data_dir / "content_inventory.example.csv"])
    search_rows = first_existing([data_dir / "search_console_rows.csv", data_dir / "search_console_rows.example.csv"])
    events = first_existing([data_dir / "events.csv", data_dir / "events.example.csv"])
    return inventory, search_rows, events


def best_funnel_dropoff(rollups: list[EventRollup], minimum_views: int) -> EventRollup | None:
    candidates = [
        rollup
        for rollup in rollups
        if rollup.views >= minimum_views and (rollup.cta_rate < 0.05 or rollup.conversions == 0)
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (item.conversions == 0, item.views), reverse=True)[0]


def render_plan_markdown(plan: DailyPlan) -> str:
    lines = [
        "# Daily Growth Loop Plan",
        "",
        f"**Action:** {plan.action_type}",
        f"**Asset:** {plan.asset or 'none'}",
        f"**Confidence:** {plan.confidence}",
        "",
        f"## {plan.title}",
        "",
        plan.reason,
        "",
        "## Next Steps",
        "",
    ]
    lines.extend(f"- {step}" for step in plan.next_steps)
    lines.extend(["", "## Evidence", "", "```json"])
    import json

    lines.append(json.dumps(plan.evidence, indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)
