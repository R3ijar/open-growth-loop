from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_growth_loop.candidates import build_candidates, render_candidates_markdown


class CandidateTests(unittest.TestCase):
    def test_candidates_rank_by_conservative_priority(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inventory = root / "inventory.csv"
            search = root / "search.csv"
            events = root / "events.csv"
            inventory.write_text(
                "status,type,asset,primary_query,cta,owner_note\n"
                "staged,guide,/docs/staged,staged query,Try it,Needs release\n"
                "planned,example,/examples/ci,ci workflow,Copy it,Queued\n",
                encoding="utf-8",
            )
            search.write_text(
                "query,page,clicks,impressions,ctr,position\n"
                "ci workflow,/examples/ci,0,100,0,12\n",
                encoding="utf-8",
            )
            events.write_text(
                "date,asset,event,count\n"
                "2026-05-20,/docs/home,view,80\n"
                "2026-05-20,/docs/home,cta,1\n",
                encoding="utf-8",
            )

            candidates = build_candidates(inventory, search, events)
            markdown = render_candidates_markdown(candidates)

        self.assertEqual(candidates[0].action_type, "release_evidence")
        self.assertEqual(candidates[1].action_type, "fix_funnel")
        self.assertTrue(any(candidate.action_type == "search_striking_distance" for candidate in candidates))
        self.assertIn("Growth Loop Candidates", markdown)

    def test_candidates_respect_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inventory = root / "inventory.csv"
            search = root / "search.csv"
            events = root / "events.csv"
            inventory.write_text("status,type,asset,primary_query,cta,owner_note\n", encoding="utf-8")
            search.write_text(
                "query,page,clicks,impressions,ctr,position\n"
                "setup,/docs/setup,0,20,0,12\n",
                encoding="utf-8",
            )
            events.write_text("date,asset,event,count\n", encoding="utf-8")

            candidates = build_candidates(inventory, search, events, minimum_impressions=25)

        self.assertEqual(candidates, [])


if __name__ == "__main__":
    unittest.main()
