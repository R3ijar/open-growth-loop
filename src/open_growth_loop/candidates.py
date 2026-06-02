from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

from .events import EventRollup, read_event_rollups
from .inventory import ContentItem, read_inventory
from .search import SearchRow, rank_search_opportunities, read_search_rows


@dataclass(frozen=True)
class Candidate:
    action_type: str
    asset: str
    title: str
    reason: str
    confidence: str
    priority: int
    score: float
    source: str
    next_steps: list[str]
    evidence: dict[str, object]
    blocked_by: list[str]


RELEASE_EVIDENCE_CHECKLIST = [
    "Open the public URL or release artifact for the staged asset.",
    "Confirm the asset is reachable from the expected public surface, such as docs navigation, README, package metadata, sitemap, or changelog.",
    "Confirm the published content matches the staged change and avoids unverified adoption or impact claims.",
    "Record the public artifact URL before tracking or reviewing the experiment.",
]


def release_evidence_checklist() -> list[str]:
    return list(RELEASE_EVIDENCE_CHECKLIST)


def build_candidates(
    inventory_path: Path,
    search_rows_path: Path,
    events_path: Path,
    minimum_impressions: int = 25,
    minimum_views: int = 25,
    weak_cta_rate: float = 0.05,
    aliases: Mapping[str, Mapping[str, str]] | None = None,
) -> list[Candidate]:
    aliases = aliases or {}
    inventory = read_inventory(inventory_path, aliases.get("content_inventory"))
    search_rows = read_search_rows(search_rows_path, aliases.get("search_rows"))
    event_rollups = read_event_rollups(events_path, aliases.get("events"))

    candidates: list[Candidate] = []
    candidates.extend(_release_candidates(inventory))
    candidates.extend(_funnel_candidates(event_rollups, minimum_views, weak_cta_rate))
    candidates.extend(_search_candidates(search_rows, minimum_impressions))
    candidates.extend(_planned_candidates(inventory))
    return sort_candidates(candidates)


def sort_candidates(candidates: list[Candidate]) -> list[Candidate]:
    return sorted(candidates, key=lambda item: (item.priority, -item.score, item.asset))


def render_candidates_markdown(candidates: list[Candidate]) -> str:
    lines = ["# Growth Loop Candidates", ""]
    if not candidates:
        lines.append("No candidates met the current rules.")
        return "\n".join(lines) + "\n"

    for index, candidate in enumerate(candidates, start=1):
        lines.extend(
            [
                f"## {index}. {candidate.title}",
                "",
                f"- Action: {candidate.action_type}",
                f"- Asset: {candidate.asset or 'none'}",
                f"- Source: {candidate.source}",
                f"- Confidence: {candidate.confidence}",
                f"- Priority: {candidate.priority}",
                f"- Score: {candidate.score:.3f}",
                f"- Reason: {candidate.reason}",
                "",
            ]
        )
        if candidate.blocked_by:
            lines.extend(["Blocked by:"])
            lines.extend(f"- {item}" for item in candidate.blocked_by)
            lines.append("")
    return "\n".join(lines)


def _release_candidates(inventory: list[ContentItem]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for index, item in enumerate(item for item in inventory if item.status == "staged"):
        candidates.append(
            Candidate(
                action_type="release_evidence",
                asset=item.asset,
                title=f"Verify staged release for {item.asset}",
                reason="Staged work should be proven public before creating another asset.",
                confidence="high",
                priority=10,
                score=1000 - index,
                source="release_evidence",
                next_steps=release_evidence_checklist(),
                evidence={"status": item.status, "primary_query": item.primary_query, "owner_note": item.owner_note},
                blocked_by=[],
            )
        )
    return candidates


def _funnel_candidates(rollups: list[EventRollup], minimum_views: int, weak_cta_rate: float) -> list[Candidate]:
    candidates: list[Candidate] = []
    for rollup in rollups:
        if rollup.views < minimum_views:
            continue
        if rollup.cta_rate >= weak_cta_rate and rollup.conversions > 0:
            continue
        score = rollup.views * (1.0 - min(rollup.cta_rate, 1.0))
        if rollup.conversions == 0:
            score += rollup.views
        candidates.append(
            Candidate(
                action_type="fix_funnel",
                asset=rollup.asset,
                title=f"Improve CTA path for {rollup.asset}",
                reason="Aggregate events show enough views but weak downstream movement.",
                confidence="medium",
                priority=20,
                score=score,
                source="fix_funnel",
                next_steps=[
                    "Make the first payoff clearer above the fold.",
                    "Move the primary CTA closer to the solved user problem.",
                    "Track the change as an experiment before reviewing outcome.",
                ],
                evidence={
                    "views": rollup.views,
                    "ctas": rollup.ctas,
                    "conversions": rollup.conversions,
                    "cta_rate": round(rollup.cta_rate, 4),
                    "conversion_rate": round(rollup.conversion_rate, 4),
                },
                blocked_by=[],
            )
        )
    return candidates


def _search_candidates(rows: list[SearchRow], minimum_impressions: int) -> list[Candidate]:
    opportunities = rank_search_opportunities(rows, minimum_impressions)
    candidates: list[Candidate] = []
    for opportunity in opportunities:
        candidates.append(
            Candidate(
                action_type=f"search_{opportunity.opportunity_type}",
                asset=opportunity.page,
                title=f"Improve search fit for {opportunity.page}",
                reason=opportunity.reason,
                confidence="medium",
                priority=30,
                score=opportunity.score,
                source="search_opportunity",
                next_steps=[
                    "Check whether the page answers the query directly.",
                    "Improve the title, intro, example, or internal links without changing unrelated pages.",
                    "Track the change and wait for enough impressions before reviewing.",
                ],
                evidence=asdict(opportunity),
                blocked_by=[],
            )
        )
    return candidates


def _planned_candidates(inventory: list[ContentItem]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for index, item in enumerate(item for item in inventory if item.status == "planned"):
        candidates.append(
            Candidate(
                action_type="create_asset",
                asset=item.asset,
                title=f"Create planned {item.type}: {item.asset}",
                reason="No stronger measured opportunity is available, so use the next queued buyer/user-intent asset.",
                confidence="low",
                priority=40,
                score=max(1, 100 - index),
                source="create_asset",
                next_steps=[
                    "Draft the smallest useful version.",
                    "Connect it to the relevant docs, example, or project action.",
                    "Mark it staged until public release evidence exists.",
                ],
                evidence={"primary_query": item.primary_query, "cta": item.cta, "owner_note": item.owner_note},
                blocked_by=[],
            )
        )
    return candidates


def candidate_brief(candidate: Candidate) -> dict[str, object]:
    return {
        "action_type": candidate.action_type,
        "asset": candidate.asset,
        "source": candidate.source,
        "priority": candidate.priority,
        "score": round(candidate.score, 3),
        "reason": candidate.reason,
    }
