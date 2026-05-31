from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

from .events import EventRollup, read_event_rollups
from .inventory import ContentItem, next_planned_item, read_inventory, staged_items
from .io_utils import first_existing, write_json_report, write_text_report
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
    weak_cta_rate: float = 0.05,
    aliases: Mapping[str, Mapping[str, str]] | None = None,
) -> DailyPlan:
    aliases = aliases or {}
    inventory = read_inventory(inventory_path, aliases.get("content_inventory"))
    search_rows = read_search_rows(search_rows_path, aliases.get("search_rows"))
    event_rollups = read_event_rollups(events_path, aliases.get("events"))
    thresholds = {
        "minimum_impressions": minimum_impressions,
        "minimum_views": minimum_views,
        "weak_cta_rate": weak_cta_rate,
    }
    skipped_rules: list[str] = []

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
            evidence=_with_decision(
                {"status": item.status, "primary_query": item.primary_query, "owner_note": item.owner_note},
                "release_evidence",
                "A staged inventory item is the highest-priority rule because pending work should be proven public before starting another action.",
                skipped_rules,
                thresholds,
            ),
        )
    skipped_rules.append("release_evidence: no staged inventory item was found")

    funnel = best_funnel_dropoff(event_rollups, minimum_views, weak_cta_rate)
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
            evidence=_with_decision(
                {
                    "views": funnel.views,
                    "ctas": funnel.ctas,
                    "conversions": funnel.conversions,
                    "cta_rate": round(funnel.cta_rate, 4),
                    "conversion_rate": round(funnel.conversion_rate, 4),
                },
                "fix_funnel",
                "An aggregate event rollup has enough views and weak downstream movement.",
                skipped_rules,
                thresholds,
            ),
        )
    skipped_rules.append(f"fix_funnel: no asset met {minimum_views} views with CTA rate below {weak_cta_rate:.3f} or zero conversions")

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
            evidence=_with_decision(
                asdict(opportunity),
                "search_opportunity",
                "A Search Console row met the impression threshold and ranked as the strongest search opportunity.",
                skipped_rules,
                thresholds,
            ),
        )
    skipped_rules.append(f"search_opportunity: no search row met the {minimum_impressions} impression threshold and opportunity rules")

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
            evidence=_with_decision(
                {"primary_query": planned.primary_query, "cta": planned.cta, "owner_note": planned.owner_note},
                "create_asset",
                "No stronger measured signal exists, so the next planned inventory item is selected.",
                skipped_rules,
                thresholds,
            ),
        )
    skipped_rules.append("create_asset: no planned inventory item was found")

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
        evidence=_with_decision(
            {},
            "wait_for_data",
            "No staged work, measured funnel issue, search opportunity, or planned item is available.",
            skipped_rules,
            thresholds,
        ),
    )


def write_plan_reports(plan: DailyPlan, out_dir: Path) -> tuple[Path, Path]:
    json_path = out_dir / "latest-plan.json"
    md_path = out_dir / "latest-plan.md"
    write_json_report(json_path, asdict(plan))
    write_text_report(md_path, render_plan_markdown(plan))
    return md_path, json_path


def default_data_paths(workspace: Path) -> tuple[Path, Path, Path]:
    data_dir = workspace / "data"
    inventory = first_existing([data_dir / "content_inventory.csv", data_dir / "content_inventory.example.csv"])
    search_rows = first_existing([data_dir / "search_console_rows.csv", data_dir / "search_console_rows.example.csv"])
    events = first_existing([data_dir / "events.csv", data_dir / "events.example.csv"])
    return inventory, search_rows, events


def best_funnel_dropoff(rollups: list[EventRollup], minimum_views: int, weak_cta_rate: float = 0.05) -> EventRollup | None:
    candidates = [
        rollup
        for rollup in rollups
        if rollup.views >= minimum_views and (rollup.cta_rate < weak_cta_rate or rollup.conversions == 0)
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (item.conversions == 0, item.views), reverse=True)[0]


def render_plan_markdown(plan: DailyPlan) -> str:
    decision = plan.evidence.get("decision") if isinstance(plan.evidence, dict) else None
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
    if isinstance(decision, dict):
        lines.extend(
            [
                "",
                "## Decision",
                "",
                f"- Selected rule: {decision.get('selected_rule', 'unknown')}",
                f"- Why: {decision.get('why_selected', '')}",
            ]
        )
        skipped = decision.get("skipped_rules", [])
        if skipped:
            lines.extend(["", "### Rules Skipped", ""])
            lines.extend(f"- {item}" for item in skipped)
    lines.extend(["", "## Evidence", "", "```json"])
    import json

    lines.append(json.dumps(plan.evidence, indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def _with_decision(
    evidence: dict[str, object],
    selected_rule: str,
    why_selected: str,
    skipped_rules: list[str],
    thresholds: dict[str, object],
) -> dict[str, object]:
    payload = dict(evidence)
    payload["decision"] = {
        "selected_rule": selected_rule,
        "why_selected": why_selected,
        "skipped_rules": list(skipped_rules),
        "thresholds": dict(thresholds),
    }
    return payload
