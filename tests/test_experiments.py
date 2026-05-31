from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_growth_loop.experiments import review_experiments, track_plan
from open_growth_loop.planner import DailyPlan


class ExperimentTests(unittest.TestCase):
    def test_track_plan_records_baselines(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ledger = root / "experiments.csv"
            search = root / "search.csv"
            events = root / "events.csv"
            search.write_text(
                "query,page,clicks,impressions,ctr,position\n"
                "setup,/docs/setup,2,50,0.04,8\n",
                encoding="utf-8",
            )
            events.write_text(
                "date,asset,event,count\n"
                "2026-05-20,/docs/setup,view,40\n"
                "2026-05-20,/docs/setup,conversion,3\n",
                encoding="utf-8",
            )
            plan = DailyPlan(
                action_type="search_striking_distance",
                asset="/docs/setup",
                title="Improve setup",
                reason="Close to ranking",
                confidence="medium",
                next_steps=[],
                evidence={},
            )

            row = track_plan(plan, ledger, search, events)

        self.assertEqual(row["baseline_impressions"], 50)
        self.assertEqual(row["baseline_clicks"], 2)
        self.assertEqual(row["baseline_views"], 40)
        self.assertEqual(row["baseline_conversions"], 3)

    def test_review_keeps_planned_work_out_of_outcome_claims(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ledger = root / "experiments.csv"
            search = root / "search.csv"
            events = root / "events.csv"
            ledger.write_text(
                "id,status,asset,action_type,planned_on,review_after,baseline_impressions,baseline_clicks,baseline_views,baseline_conversions,artifact,note,outcome\n"
                "2026-05-20-001,planned,/docs/setup,search,2026-05-20,2026-06-03,0,0,0,0,,,\n",
                encoding="utf-8",
            )
            search.write_text("query,page,clicks,impressions,ctr,position\n", encoding="utf-8")
            events.write_text("date,asset,event,count\n", encoding="utf-8")

            reviews = review_experiments(ledger, search, events)

        self.assertEqual(reviews[0].outcome, "not_publicly_applied")


if __name__ == "__main__":
    unittest.main()
