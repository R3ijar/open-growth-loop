from __future__ import annotations

from .planner import DailyPlan


def render_codex_prompt(plan: DailyPlan) -> str:
    return f"""You are helping maintain an open-source project.

Work from this single growth-loop action:

Action type: {plan.action_type}
Asset: {plan.asset or "none"}
Title: {plan.title}
Reason: {plan.reason}
Confidence: {plan.confidence}

Constraints:
- Make one focused, reviewable change.
- Do not invent analytics or adoption claims.
- Preserve private user data boundaries.
- Add or update tests/docs when the change affects maintainer workflows.
- Record what changed so the experiment can be reviewed later.

Next steps:
{_bullet_lines(plan.next_steps)}

Evidence:
{plan.evidence}
"""


def _bullet_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)
