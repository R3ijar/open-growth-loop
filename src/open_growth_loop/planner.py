from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

from .candidates import Candidate, build_candidates, candidate_brief, release_evidence_checklist
from .events import EventRollup
from .io_utils import first_existing, write_json_report, write_text_report


@dataclass(frozen=True)
class DailyPlan:
    action_type: str
    asset: str
    title: str
    reason: str
    confidence: str
    next_steps: list[str]
    evidence: dict[str, object]


def build_daily_plan(
    inventory_path: Path,
    search_rows_path: Path,
    events_path: Path,
    minimum_impressions: int = 25,
    minimum_views: int = 25,
    weak_cta_rate: float = 0.05,
    aliases: Mapping[str, Mapping[str, str]] | None = None,
) -> DailyPlan:
    thresholds = {
        "minimum_impressions": minimum_impressions,
        "minimum_views": minimum_views,
        "weak_cta_rate": weak_cta_rate,
    }
    candidates = build_candidates(
        inventory_path,
        search_rows_path,
        events_path,
        minimum_impressions=minimum_impressions,
        minimum_views=minimum_views,
        weak_cta_rate=weak_cta_rate,
        aliases=aliases,
    )
    if candidates:
        selected = candidates[0]
        return _plan_from_candidate(selected, candidates[1:], thresholds)

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
            _missing_rule_summaries(set(), thresholds),
            thresholds,
            [],
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


def _plan_from_candidate(candidate: Candidate, alternatives: list[Candidate], thresholds: dict[str, object]) -> DailyPlan:
    present_sources = {candidate.source, *(item.source for item in alternatives)}
    skipped_rules = _missing_rule_summaries(present_sources, thresholds, before_priority=candidate.priority)
    return DailyPlan(
        action_type=candidate.action_type,
        asset=candidate.asset,
        title=candidate.title,
        reason=candidate.reason,
        confidence=candidate.confidence,
        next_steps=list(candidate.next_steps),
        evidence=_with_decision(
            dict(candidate.evidence),
            candidate.source,
            candidate.reason,
            skipped_rules,
            thresholds,
            alternatives[:5],
        ),
    )


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
        alternatives = decision.get("alternatives", [])
        if alternatives:
            lines.extend(["", "### Alternatives", ""])
            for item in alternatives:
                if isinstance(item, dict):
                    lines.append(
                        f"- {item.get('action_type', 'unknown')} for {item.get('asset') or 'none'} "
                        f"(source={item.get('source', 'unknown')}, score={item.get('score', 'unknown')})"
                    )
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
    alternatives: list[Candidate],
) -> dict[str, object]:
    payload = dict(evidence)
    payload["decision"] = {
        "selected_rule": selected_rule,
        "why_selected": why_selected,
        "skipped_rules": list(skipped_rules),
        "thresholds": dict(thresholds),
        "alternatives": [candidate_brief(item) for item in alternatives],
    }
    return payload


def _missing_rule_summaries(present_sources: set[str], thresholds: dict[str, object], before_priority: int = 100) -> list[str]:
    minimum_impressions = int(thresholds["minimum_impressions"])
    minimum_views = int(thresholds["minimum_views"])
    weak_cta_rate = float(thresholds["weak_cta_rate"])
    rules = [
        ("release_evidence", 10, "release_evidence: no staged inventory item was found"),
        ("fix_funnel", 20, f"fix_funnel: no asset met {minimum_views} views with CTA rate below {weak_cta_rate:.3f} or zero conversions"),
        ("search_opportunity", 30, f"search_opportunity: no search row met the {minimum_impressions} impression threshold and opportunity rules"),
        ("create_asset", 40, "create_asset: no planned inventory item was found"),
    ]
    return [message for source, priority, message in rules if priority < before_priority and source not in present_sources]
