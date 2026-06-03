from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .events import PRIVATE_COLUMN_HINTS
from .io_utils import write_text_report
from .planner import DailyPlan
from .reporting import key_value_table


PRIVATE_EVIDENCE_HINTS = PRIVATE_COLUMN_HINTS | {
    "api_key",
    "client_secret",
    "customer",
    "password",
    "payload",
    "private_key",
    "secret",
    "session",
    "token",
    "user",
}


def issue_title(plan: DailyPlan) -> str:
    if plan.action_type == "wait_for_data":
        return "Add enough aggregate data for the next maintainer action"
    return plan.title.strip() or "Review the next maintainer action"


def render_issue_draft(plan: DailyPlan) -> str:
    title = issue_title(plan)
    lines = [
        "# GitHub Issue Draft",
        "",
        "Generated locally by Open Growth Loop. Review before posting publicly.",
        "",
        "## Recommended Title",
        "",
        title,
        "",
        "## Draft Snapshot",
        "",
        *key_value_table(
            [
                ("Action", plan.action_type),
                ("Asset", plan.asset or "none"),
                ("Confidence", plan.confidence),
                ("Review state", "local draft only"),
            ]
        ),
        "",
        "## Issue Body",
        "",
        "### Context",
        "",
        plan.reason.strip() or "Open Growth Loop selected this as the next conservative maintainer action.",
        "",
        "### Proposed Work",
        "",
        f"- Action type: `{plan.action_type}`",
        f"- Asset: `{plan.asset or 'none'}`",
        f"- Confidence: `{plan.confidence}`",
        "",
        "### Acceptance Criteria",
        "",
    ]
    lines.extend(_bullet_lines(plan.next_steps or ["Review the plan evidence and make one focused, public maintainer improvement."]))
    lines.extend(
        [
            "- Avoid unverified adoption, traffic, revenue, or impact claims.",
            "- Keep private analytics, customer data, credentials, and raw user data out of the issue.",
            "",
            "### Evidence Summary",
            "",
        ]
    )
    lines.extend(_evidence_lines(plan.evidence))
    lines.extend(
        [
            "",
            "### Review Notes",
            "",
            "- This is a local draft, not an automatically created GitHub issue.",
            "- Remove or generalize any project-private details before posting.",
            "- Link the final public artifact or pull request after the work ships.",
            "",
        ]
    )
    return "\n".join(lines)


def write_issue_draft(plan: DailyPlan, out_dir: Path) -> tuple[Path, Path]:
    return write_text_report(out_dir / "latest-issue-draft.md", render_issue_draft(plan))


def _evidence_lines(evidence: dict[str, object]) -> list[str]:
    lines: list[str] = []
    decision = evidence.get("decision") if isinstance(evidence, dict) else None
    if isinstance(decision, dict):
        selected_rule = str(decision.get("selected_rule") or "unknown")
        why_selected = str(decision.get("why_selected") or "").strip()
        lines.append(f"- Selected rule: `{selected_rule}`")
        if why_selected:
            lines.append(f"- Why selected: {why_selected}")
        alternatives = [item for item in decision.get("alternatives", []) if isinstance(item, dict)]
        if alternatives:
            lines.append(f"- Alternatives reviewed: {len(alternatives)}")
            for item in alternatives[:3]:
                asset = str(item.get("asset") or "none")
                action_type = str(item.get("action_type") or "unknown")
                source = str(item.get("source") or "unknown")
                score = item.get("score", "unknown")
                lines.append(f"  - `{action_type}` for `{asset}` from `{source}` (score: {score})")
        skipped_rules = [str(item) for item in decision.get("skipped_rules", []) if str(item).strip()]
        if skipped_rules:
            lines.append(f"- Skipped rules: {'; '.join(skipped_rules[:3])}")

    public_fields = _public_scalar_lines((key, value) for key, value in evidence.items() if key != "decision")
    if public_fields:
        lines.extend(public_fields)
    if not lines:
        lines.append("- No public-safe evidence summary is available. Review the local plan before posting.")
    return lines


def _public_scalar_lines(items: Iterable[tuple[str, object]], prefix: str = "") -> list[str]:
    lines: list[str] = []
    for key, value in items:
        if _private_key(key):
            continue
        display_key = f"{prefix}{key}" if prefix else key
        if isinstance(value, dict):
            lines.extend(_public_scalar_lines(value.items(), f"{display_key}."))
            continue
        if isinstance(value, list):
            continue
        if not isinstance(value, (str, int, float, bool)) or value == "":
            continue
        text = str(value).strip()
        if not text:
            continue
        if len(text) > 160:
            text = f"{text[:157].rstrip()}..."
        lines.append(f"- {display_key}: `{text}`")
    return lines


def _private_key(key: str) -> bool:
    lowered = key.strip().lower().replace("-", "_")
    return any(hint in lowered for hint in PRIVATE_EVIDENCE_HINTS)


def _bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items if item.strip()]
