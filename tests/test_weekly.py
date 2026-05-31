from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_growth_loop.weekly import build_weekly_review, render_weekly_review


class WeeklyReviewTests(unittest.TestCase):
    def test_weekly_review_groups_operating_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inventory = root / "inventory.csv"
            ledger = root / "experiments.csv"
            inventory.write_text(
                "status,type,asset,primary_query,cta,owner_note\n"
                "staged,guide,/docs/setup,setup,Try it,Needs release\n"
                "planned,example,/examples/ci,ci,Copy it,Queued\n",
                encoding="utf-8",
            )
            ledger.write_text(
                "id,status,asset,action_type,planned_on,review_after,shipped_on,baseline_impressions,baseline_clicks,baseline_views,baseline_conversions,artifact,note,outcome\n"
                "2026-05-01-001,planned,/docs/setup,search,2026-05-01,2026-05-15,,10,1,20,0,,Needs artifact,\n"
                "2026-05-02-001,shipped,/docs/intro,search,2026-05-02,2026-05-10,2026-05-03,10,1,20,0,https://example.org/docs/intro,Released,\n"
                "2026-05-03-001,shipped,/docs/later,search,2026-05-03,2026-06-10,2026-05-04,10,1,20,0,https://example.org/docs/later,Released,\n",
                encoding="utf-8",
            )

            review = build_weekly_review(inventory, ledger, today="2026-05-30")
            markdown = render_weekly_review(review)

        self.assertEqual(review.inventory_counts["staged"], 1)
        self.assertEqual(len(review.waiting_for_artifact), 1)
        self.assertEqual(len(review.ready_for_review), 1)
        self.assertEqual(len(review.waiting_for_data), 1)
        self.assertEqual(len(review.stale_work), 3)
        self.assertIn("Weekly Growth Loop Review", markdown)
        self.assertIn("Resolve stale work", review.next_attention[0])
        self.assertIn("Stale Work", markdown)

    def test_weekly_review_uses_configurable_stale_windows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inventory = root / "inventory.csv"
            ledger = root / "experiments.csv"
            inventory.write_text("status,type,asset,primary_query,cta,owner_note\n", encoding="utf-8")
            ledger.write_text(
                "id,status,asset,action_type,planned_on,review_after,shipped_on,baseline_impressions,baseline_clicks,baseline_views,baseline_conversions,artifact,note,outcome\n"
                "2026-05-01-001,planned,/docs/setup,search,2026-05-20,2026-06-20,,10,1,20,0,,Needs artifact,\n"
                "2026-05-02-001,shipped,/docs/later,search,2026-05-02,2026-06-20,2026-05-01,10,1,20,0,https://example.org/docs/later,Released,\n",
                encoding="utf-8",
            )

            review = build_weekly_review(inventory, ledger, today="2026-05-30", stale_planned_days=10, stale_shipped_days=21)

        kinds = {item["kind"] for item in review.stale_work}
        self.assertIn("planned_stale", kinds)
        self.assertIn("shipped_stale", kinds)


if __name__ == "__main__":
    unittest.main()
