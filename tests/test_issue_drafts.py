from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_growth_loop.issue_drafts import (
    issue_title,
    render_issue_draft,
    write_issue_draft,
)
from open_growth_loop.planner import DailyPlan


class IssueDraftTests(unittest.TestCase):
    def test_render_issue_draft_is_public_reviewable_markdown(self) -> None:
        plan = DailyPlan(
            action_type="search_striking_distance",
            asset="/docs/setup",
            title="Improve search fit for /docs/setup",
            reason="The page ranks near page one with weak CTR.",
            confidence="medium",
            next_steps=[
                "Check whether the page answers the query directly.",
                "Improve the title, intro, example, or internal links without changing unrelated pages.",
            ],
            evidence={
                "query": "open source setup guide",
                "impressions": 120,
                "ctr": 0.01,
                "customer_email": "private@example.com",
                "decision": {
                    "selected_rule": "search_opportunity",
                    "why_selected": "Search opportunity outranked planned work.",
                    "skipped_rules": ["release_evidence: no staged inventory item was found"],
                    "alternatives": [
                        {
                            "action_type": "create_asset",
                            "asset": "/docs/examples",
                            "source": "create_asset",
                            "score": 40.0,
                        }
                    ],
                },
            },
        )

        draft = render_issue_draft(plan)

        self.assertIn("## Recommended Title", draft)
        self.assertIn("Improve search fit for /docs/setup", draft)
        self.assertIn("- Action type: `search_striking_distance`", draft)
        self.assertIn("- Selected rule: `search_opportunity`", draft)
        self.assertIn("- impressions: `120`", draft)
        self.assertIn("Review before posting publicly", draft)
        self.assertNotIn("private@example.com", draft)
        self.assertNotIn("customer_email", draft)

    def test_wait_for_data_title_is_actionable(self) -> None:
        plan = DailyPlan(
            action_type="wait_for_data",
            asset="",
            title="Wait for more evidence",
            reason="No signal exists yet.",
            confidence="high",
            next_steps=[],
            evidence={},
        )

        self.assertEqual(issue_title(plan), "Add enough aggregate data for the next maintainer action")

    def test_write_issue_draft_writes_latest_and_history(self) -> None:
        plan = DailyPlan(
            action_type="release_evidence",
            asset="/docs/setup",
            title="Verify staged release for /docs/setup",
            reason="Staged work should be proven public before creating another asset.",
            confidence="high",
            next_steps=["Open the public URL or release artifact."],
            evidence={"status": "staged"},
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            latest, history = write_issue_draft(plan, Path(temp_dir))
            latest_text = latest.read_text(encoding="utf-8")
            history_text = history.read_text(encoding="utf-8")

        self.assertEqual(latest.name, "latest-issue-draft.md")
        self.assertTrue(history.name.endswith("-issue-draft.md"))
        self.assertIn("Verify staged release", latest_text)
        self.assertEqual(latest_text, history_text)


if __name__ == "__main__":
    unittest.main()
