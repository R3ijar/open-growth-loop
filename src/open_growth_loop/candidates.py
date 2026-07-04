from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from .events import EventRollup, read_event_rollups
from .inventory import ContentItem, read_inventory
from .memory import ActionMemoryRecord, read_action_memory
from .reporting import compact_join, key_value_table, markdown_table
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
    memory_path: Path | None = None,
    aliases: Mapping[str, Mapping[str, str]] | None = None,
) -> list[Candidate]:
    aliases = aliases or {}
    inventory = read_inventory(inventory_path, aliases.get("content_inventory"))
    search_rows = read_search_rows(search_rows_path, aliases.get("search_rows"))
    event_rollups = read_event_rollups(events_path, aliases.get("events"))
    memory = read_action_memory(memory_path, aliases.get("action_memory")) if memory_path else []

    candidates: list[Candidate] = []
    candidates.extend(_memory_candidates(memory))
    candidates.extend(_release_candidates(inventory))
    candidates.extend(_funnel_candidates(event_rollups, minimum_views, weak_cta_rate))
    candidates.extend(_search_candidates(search_rows, minimum_impressions))
    candidates.extend(_planned_candidates(inventory))
    candidates = _apply_memory_adjustments(candidates, memory)
    return sort_candidates(candidates)


def sort_candidates(candidates: list[Candidate]) -> list[Candidate]:
    return sorted(candidates, key=lambda item: (bool(item.blocked_by), item.priority, -item.score, item.asset))


def render_candidates_markdown(candidates: list[Candidate]) -> str:
    lines = ["# Growth Loop Candidates", ""]
    if not candidates:
        lines.append("No candidates met the current rules.")
        return "\n".join(lines) + "\n"

    selected = candidates[0]
    blocked = sum(1 for candidate in candidates if candidate.blocked_by)
    lines.extend(
        [
            "## Summary",
            "",
            *key_value_table(
                [
                    ("Candidates reviewed", len(candidates)),
                    ("Selected candidate", selected.title),
                    ("Blocked or cooled", blocked),
                ]
            ),
            "",
            "## Ranking",
            "",
            *markdown_table(
                ["Rank", "Action", "Asset", "Rule", "Confidence", "Priority", "Score", "Status"],
                [
                    (
                        index,
                        candidate.action_type,
                        candidate.asset or "none",
                        candidate.source,
                        candidate.confidence,
                        candidate.priority,
                        f"{candidate.score:.3f}",
                        "blocked" if candidate.blocked_by else "available",
                    )
                    for index, candidate in enumerate(candidates, start=1)
                ],
            ),
            "",
            "## Candidate Details",
            "",
        ]
    )

    for index, candidate in enumerate(candidates, start=1):
        lines.extend(
            [
                f"### {index}. {candidate.title}",
                "",
                *key_value_table(
                    [
                        ("Action", candidate.action_type),
                        ("Asset", candidate.asset or "none"),
                        ("Source", candidate.source),
                        ("Confidence", candidate.confidence),
                        ("Priority", candidate.priority),
                        ("Score", f"{candidate.score:.3f}"),
                        ("Reason", candidate.reason),
                    ]
                ),
                "",
            ]
        )
        notes = _candidate_notes(candidate)
        if notes:
            lines.extend(["Notes:", ""])
            lines.append(compact_join(notes, limit=6))
            lines.append("")
        if candidate.blocked_by:
            lines.extend(["Blocked by:", ""])
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


def _memory_candidates(memory: list[ActionMemoryRecord]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for index, record in enumerate(record for record in memory if record.pending_outcome):
        candidates.append(
            Candidate(
                action_type="record_outcome",
                asset=record.asset,
                title=f"Record outcome for {record.asset or record.action_type}",
                reason="A completed action needs an observed outcome before similar work is repeated.",
                confidence="high",
                priority=15,
                score=500 - index,
                source="action_memory",
                next_steps=[
                    "Compare current aggregate search and event signals with the recorded baseline or notes.",
                    "Record directionally_positive, needs_iteration, or insufficient_sample without overstating causality.",
                    "Let future candidate ranking use the recorded outcome.",
                ],
                evidence={
                    "memory_id": record.id,
                    "completed_on": record.completed_on,
                    "completed_action_type": record.action_type,
                    "artifact": record.artifact,
                    "note": record.note,
                },
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


def _apply_memory_adjustments(candidates: list[Candidate], memory: list[ActionMemoryRecord]) -> list[Candidate]:
    if not memory:
        return candidates

    adjusted: list[Candidate] = []
    positive_by_action = _count_by_action(record for record in memory if record.positive)
    negative_by_action = _count_by_action(record for record in memory if record.negative)
    pending_by_key = {
        (record.asset, record.action_type): record
        for record in memory
        if record.pending_outcome and record.action_type != "record_outcome"
    }
    measured_by_key = {
        (record.asset, record.action_type): record
        for record in memory
        if record.status == "measured" and record.action_type != "record_outcome"
    }

    for candidate in candidates:
        if candidate.action_type == "record_outcome":
            adjusted.append(candidate)
            continue

        multiplier = 1.0
        notes: list[str] = []
        blocked_by = list(candidate.blocked_by)
        pending = pending_by_key.get((candidate.asset, candidate.action_type))
        if pending:
            multiplier *= 0.2
            blocked_by.append(f"Action memory {pending.id} is completed but has no recorded outcome.")
            notes.append("repeat cooled until pending outcome is recorded")
        measured = measured_by_key.get((candidate.asset, candidate.action_type))
        if measured and not measured.negative:
            multiplier *= 0.2
            blocked_by.append(f"Action memory {measured.id} already measured this asset/action.")
            notes.append("exact repeat cooled until source data changes")

        positive_count = positive_by_action.get(candidate.action_type, 0)
        negative_count = negative_by_action.get(candidate.action_type, 0)
        if positive_count:
            boost = min(0.25, positive_count * 0.05)
            multiplier += boost
            notes.append(f"action type has {positive_count} positive outcome(s)")
        if negative_count:
            cooldown = min(0.30, negative_count * 0.05)
            multiplier -= cooldown
            notes.append(f"action type has {negative_count} weak outcome(s)")

        if not notes:
            adjusted.append(candidate)
            continue

        evidence = dict(candidate.evidence)
        evidence["memory_adjustment"] = {
            "score_multiplier": round(max(0.05, multiplier), 3),
            "notes": notes,
        }
        adjusted.append(
            replace(
                candidate,
                score=max(0.0, candidate.score * max(0.05, multiplier)),
                confidence="low" if blocked_by else candidate.confidence,
                evidence=evidence,
                blocked_by=blocked_by,
            )
        )

    return adjusted


def _count_by_action(records: Iterable[ActionMemoryRecord]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        action_type = record.action_type
        if not action_type:
            continue
        counts[action_type] = counts.get(action_type, 0) + 1
    return counts


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
        "confidence": candidate.confidence,
        "priority": candidate.priority,
        "score": round(candidate.score, 3),
        "reason": candidate.reason,
        "blocked_by": list(candidate.blocked_by),
    }


def _candidate_notes(candidate: Candidate) -> list[str]:
    notes: list[str] = []
    adjustment = candidate.evidence.get("memory_adjustment")
    if isinstance(adjustment, dict):
        raw_notes = adjustment.get("notes", [])
        if isinstance(raw_notes, list):
            notes.extend(str(item) for item in raw_notes if str(item).strip())
        multiplier = adjustment.get("score_multiplier")
        if multiplier is not None:
            notes.append(f"score multiplier: {multiplier}")
    return notes
