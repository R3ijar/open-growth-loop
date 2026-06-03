from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

from .candidates import Candidate, build_candidates, candidate_brief, release_evidence_checklist
from .events import EventRollup
from .freshness import FreshnessReport, build_freshness_report
from .io_utils import first_existing, write_json_report, write_text_report
from .reporting import collapsible_section, compact_join, key_value_table, markdown_table, status_label, task_list


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
    memory_path: Path | None = None,
    aliases: Mapping[str, Mapping[str, str]] | None = None,
    freshness_warn_days: int = 21,
    today: str | None = None,
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
        memory_path=memory_path,
        aliases=aliases,
    )
    freshness = build_freshness_report(
        {"content_inventory": inventory_path, "search_rows": search_rows_path, "events": events_path},
        aliases=aliases,
        warn_after_days=freshness_warn_days,
        today=today,
    )
    if candidates:
        selected = candidates[0]
        return _plan_from_candidate(selected, candidates[1:], thresholds, freshness)

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
            None,
            freshness,
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


def default_memory_path(workspace: Path) -> Path:
    return workspace / "data" / "action_memory.csv"


def best_funnel_dropoff(rollups: list[EventRollup], minimum_views: int, weak_cta_rate: float = 0.05) -> EventRollup | None:
    candidates = [
        rollup
        for rollup in rollups
        if rollup.views >= minimum_views and (rollup.cta_rate < weak_cta_rate or rollup.conversions == 0)
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (item.conversions == 0, item.views), reverse=True)[0]


def _plan_from_candidate(candidate: Candidate, alternatives: list[Candidate], thresholds: dict[str, object], freshness: FreshnessReport) -> DailyPlan:
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
            candidate,
            freshness,
        ),
    )


def render_plan_markdown(plan: DailyPlan) -> str:
    decision = plan.evidence.get("decision") if isinstance(plan.evidence, dict) else None
    freshness = plan.evidence.get("freshness") if isinstance(plan.evidence, dict) else None
    selected_rule = decision.get("selected_rule", "unknown") if isinstance(decision, dict) else "unknown"
    freshness_status = status_label(freshness.get("ok", "")) if isinstance(freshness, dict) else "UNKNOWN"
    lines = [
        "# Daily Growth Loop Plan",
        "",
        "## Summary",
        "",
        *key_value_table(
            [
                ("Recommended action", plan.action_type),
                ("Asset", plan.asset or "none"),
                ("Confidence", plan.confidence),
                ("Selected rule", selected_rule),
                ("Data freshness", freshness_status),
            ]
        ),
        "",
        "## Recommended Action",
        "",
        f"**{plan.title}**",
        "",
        plan.reason.strip() or "Open Growth Loop selected this as the next conservative maintainer action.",
        "",
        "## Action Checklist",
        "",
    ]
    lines.extend(task_list(plan.next_steps, "- No next steps were generated. Review the local evidence before acting."))
    if isinstance(decision, dict):
        lines.extend(
            [
                "",
                "## Decision Trace",
                "",
                "### Candidate Comparison",
                "",
            ]
        )
        comparison_rows: list[tuple[object, ...]] = []
        winner = decision.get("winner")
        if isinstance(winner, dict):
            comparison_rows.append(
                (
                    winner.get("rank", 1),
                    "selected",
                    winner.get("action_type", plan.action_type),
                    winner.get("asset") or plan.asset or "none",
                    winner.get("source", selected_rule),
                    winner.get("confidence", plan.confidence),
                    winner.get("score", "n/a"),
                    winner.get("selection_reason", decision.get("why_selected", "")),
                )
            )
        comparison = decision.get("comparison", [])
        if isinstance(comparison, list):
            for item in comparison:
                if not isinstance(item, dict):
                    continue
                comparison_rows.append(
                    (
                        item.get("rank", "?"),
                        "alternative",
                        item.get("action_type", "unknown"),
                        item.get("asset") or "none",
                        item.get("source", "unknown"),
                        item.get("confidence", "unknown"),
                        item.get("score", "n/a"),
                        "lost because: "
                        + compact_join(
                            item.get("lost_because", [])
                            if isinstance(item.get("lost_because"), list)
                            else [item.get("lost_because", "")]
                        ),
                    )
                )
        if comparison_rows:
            lines.extend(
                markdown_table(
                    ["Rank", "Role", "Action", "Asset", "Rule", "Confidence", "Score", "Decision note"],
                    comparison_rows,
                )
            )
        else:
            lines.append(decision.get("why_selected", "") or "No candidate comparison was available.")

        skipped = decision.get("skipped_rules", [])
        if skipped:
            lines.extend(["", "### Skipped Higher-Priority Rules", ""])
            lines.extend(f"- {item}" for item in skipped)

        audit_notes = decision.get("audit_notes", [])
        if audit_notes:
            lines.extend(
                [
                    "",
                    "### Audit Notes",
                    "",
                    *collapsible_section("Audit notes", [f"- {item}" for item in audit_notes if str(item).strip()]),
                ]
            )
    if isinstance(freshness, dict):
        lines.extend(["", "## Data Freshness", ""])
        checks = freshness.get("checks", [])
        if isinstance(checks, list) and checks:
            lines.extend(
                markdown_table(
                    ["Input", "Status", "Source", "Latest", "Age", "Reason"],
                    [
                        (
                            check.get("name", "unknown"),
                            status_label(check.get("status", "")),
                            check.get("source", ""),
                            check.get("latest_date", "") or "n/a",
                            "n/a" if check.get("age_days") is None else f"{check.get('age_days')} days",
                            check.get("reason", ""),
                        )
                        for check in checks
                        if isinstance(check, dict)
                    ],
                )
            )
        else:
            lines.append(f"Status: {'ok' if freshness.get('ok') else 'warnings'}")
        warnings = freshness.get("warnings", [])
        if warnings:
            lines.extend(["", "### Freshness Warnings", ""])
            lines.extend(f"- {item}" for item in warnings if str(item).strip())
        else:
            lines.extend(["", "- No stale data warnings for the inputs used by this plan."])
    lines.extend(
        [
            "",
            *collapsible_section(
                "Raw evidence JSON",
                ["```json", json.dumps(plan.evidence, indent=2, sort_keys=True), "```"],
            ),
        ]
    )
    lines.append("")
    return "\n".join(lines)


def _with_decision(
    evidence: dict[str, object],
    selected_rule: str,
    why_selected: str,
    skipped_rules: list[str],
    thresholds: dict[str, object],
    alternatives: list[Candidate],
    selected: Candidate | None,
    freshness: FreshnessReport,
) -> dict[str, object]:
    payload = dict(evidence)
    payload["decision"] = {
        "trace_version": 2,
        "selected_rule": selected_rule,
        "why_selected": why_selected,
        "skipped_rules": list(skipped_rules),
        "thresholds": dict(thresholds),
        "alternatives": [candidate_brief(item) for item in alternatives],
        "winner": _winner_trace(selected, selected_rule, why_selected, thresholds),
        "comparison": [_candidate_comparison(item, selected, index + 2, thresholds) for index, item in enumerate(alternatives)],
        "audit_notes": _audit_notes(selected, skipped_rules),
    }
    payload["freshness"] = asdict(freshness)
    return payload


def _winner_trace(
    selected: Candidate | None,
    selected_rule: str,
    why_selected: str,
    thresholds: dict[str, object],
) -> dict[str, object]:
    if selected is None:
        return {
            "action_type": "wait_for_data",
            "asset": "",
            "source": selected_rule,
            "selection_reason": why_selected,
            "threshold_notes": _wait_threshold_notes(thresholds),
            "signal_summary": [],
            "memory_notes": [],
            "blocked_by": [],
        }
    trace = _candidate_trace(selected, rank=1, thresholds=thresholds)
    trace["selection_reason"] = "Selected as the highest-ranked unblocked candidate after conservative rule priority, score, and asset tie-breaks."
    return trace


def _candidate_comparison(
    candidate: Candidate,
    selected: Candidate | None,
    rank: int,
    thresholds: dict[str, object],
) -> dict[str, object]:
    trace = _candidate_trace(candidate, rank=rank, thresholds=thresholds)
    trace["lost_because"] = _lost_because(candidate, selected)
    return trace


def _candidate_trace(candidate: Candidate, rank: int, thresholds: dict[str, object]) -> dict[str, object]:
    return {
        "rank": rank,
        "action_type": candidate.action_type,
        "asset": candidate.asset,
        "source": candidate.source,
        "priority": candidate.priority,
        "score": round(candidate.score, 3),
        "confidence": candidate.confidence,
        "blocked_by": list(candidate.blocked_by),
        "signal_summary": _signal_summary(candidate),
        "threshold_notes": _threshold_notes(candidate, thresholds),
        "memory_notes": _memory_notes(candidate),
    }


def _lost_because(candidate: Candidate, selected: Candidate | None) -> list[str]:
    if selected is None:
        return ["No selected candidate was available."]

    reasons: list[str] = []
    if candidate.blocked_by:
        reasons.append("blocked by local action memory or missing follow-up evidence")
    if selected.source == "release_evidence" and candidate.source != "release_evidence":
        reasons.append("staged release evidence has the highest conservative priority")
    elif selected.source == "action_memory" and candidate.source != "action_memory":
        reasons.append("pending outcomes are reviewed before repeating or starting similar work")
    if candidate.priority > selected.priority:
        reasons.append(f"lower rule priority ({candidate.priority}) than the selected priority ({selected.priority})")
    elif candidate.priority == selected.priority and candidate.score < selected.score:
        reasons.append(f"lower score ({candidate.score:.3f}) than the selected score ({selected.score:.3f})")
    elif candidate.priority == selected.priority and candidate.score == selected.score and candidate.asset > selected.asset:
        reasons.append("same priority and score, but asset tie-break ranked later")
    if not reasons:
        reasons.append("ranked below the selected action after conservative sort order")
    return reasons


def _signal_summary(candidate: Candidate) -> list[str]:
    summary: list[str] = []
    for key in (
        "status",
        "primary_query",
        "views",
        "ctas",
        "conversions",
        "cta_rate",
        "conversion_rate",
        "query",
        "impressions",
        "clicks",
        "ctr",
        "position",
        "opportunity_type",
        "memory_id",
        "completed_on",
        "completed_action_type",
    ):
        value = candidate.evidence.get(key)
        if value is None or value == "":
            continue
        summary.append(f"{key}={value}")
    return summary[:8]


def _threshold_notes(candidate: Candidate, thresholds: dict[str, object]) -> list[str]:
    if candidate.source == "fix_funnel":
        return [
            f"minimum_views={thresholds['minimum_views']}",
            f"weak_cta_rate={float(thresholds['weak_cta_rate']):.3f}",
        ]
    if candidate.source == "search_opportunity":
        return [f"minimum_impressions={thresholds['minimum_impressions']}"]
    if candidate.source == "release_evidence":
        return ["staged inventory status outranks new work"]
    if candidate.source == "action_memory":
        return ["completed actions with pending outcomes outrank new work"]
    if candidate.source == "create_asset":
        return ["planned inventory items are used only after stronger signals are absent"]
    return []


def _wait_threshold_notes(thresholds: dict[str, object]) -> list[str]:
    return [
        f"minimum_impressions={thresholds['minimum_impressions']}",
        f"minimum_views={thresholds['minimum_views']}",
        f"weak_cta_rate={float(thresholds['weak_cta_rate']):.3f}",
    ]


def _memory_notes(candidate: Candidate) -> list[str]:
    notes: list[str] = []
    adjustment = candidate.evidence.get("memory_adjustment")
    if isinstance(adjustment, dict):
        raw_notes = adjustment.get("notes", [])
        if isinstance(raw_notes, list):
            notes.extend(str(item) for item in raw_notes if str(item).strip())
        multiplier = adjustment.get("score_multiplier")
        if multiplier is not None:
            notes.append(f"score_multiplier={multiplier}")
    if candidate.blocked_by:
        notes.extend(candidate.blocked_by)
    return notes


def _audit_notes(selected: Candidate | None, skipped_rules: list[str]) -> list[str]:
    notes = [
        "Candidates are sorted by blocked state, conservative rule priority, descending score, and asset path.",
        "Scores rank candidates inside a rule; conservative rule priority can intentionally beat a higher raw score.",
    ]
    if selected is None:
        notes.append("No candidate met the current thresholds or inventory states.")
    if skipped_rules:
        notes.append("Skipped rules document stronger-priority rules that produced no candidate.")
    return notes


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
