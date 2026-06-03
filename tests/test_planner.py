from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_growth_loop.planner import build_daily_plan, render_plan_markdown


def write_defaults(root: Path, inventory: str) -> tuple[Path, Path, Path]:
    inventory_path = root / "inventory.csv"
    search_path = root / "search.csv"
    events_path = root / "events.csv"
    inventory_path.write_text(inventory, encoding="utf-8")
    search_path.write_text(
        "query,page,clicks,impressions,ctr,position\n"
        "setup guide,/docs/setup,0,100,0,12\n",
        encoding="utf-8",
    )
    events_path.write_text(
        "date,asset,event,count\n"
        "2026-05-20,/docs/home,view,80\n"
        "2026-05-20,/docs/home,cta,1\n",
        encoding="utf-8",
    )
    return inventory_path, search_path, events_path


class PlannerTests(unittest.TestCase):
    def test_planner_prioritizes_staged_release(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = write_defaults(
                Path(temp_dir),
                "status,type,asset,primary_query,cta,owner_note\n"
                "staged,guide,/docs/staged,staged query,Try it,Needs release\n",
            )

            plan = build_daily_plan(*paths)

        self.assertEqual(plan.action_type, "release_evidence")
        self.assertEqual(plan.asset, "/docs/staged")
        self.assertTrue(any("public URL" in step for step in plan.next_steps))
        self.assertTrue(any("unverified adoption" in step for step in plan.next_steps))
        self.assertEqual(plan.evidence["decision"]["selected_rule"], "release_evidence")
        self.assertEqual(plan.evidence["decision"]["thresholds"]["minimum_impressions"], 25)
        self.assertEqual(plan.evidence["decision"]["trace_version"], 2)
        self.assertEqual(plan.evidence["decision"]["winner"]["source"], "release_evidence")
        self.assertTrue(plan.evidence["decision"]["comparison"])
        self.assertTrue(any("priority" in reason for reason in plan.evidence["decision"]["comparison"][0]["lost_because"]))
        self.assertIn("freshness", plan.evidence)

    def test_planner_uses_funnel_before_search_when_no_staged_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = write_defaults(
                Path(temp_dir),
                "status,type,asset,primary_query,cta,owner_note\n"
                "published,docs,/docs/home,home query,Try it,Published\n",
            )

            plan = build_daily_plan(*paths)

        self.assertEqual(plan.action_type, "fix_funnel")
        self.assertEqual(plan.asset, "/docs/home")
        self.assertIn("release_evidence", plan.evidence["decision"]["skipped_rules"][0])
        self.assertIn("minimum_views=25", plan.evidence["decision"]["winner"]["threshold_notes"])

    def test_planner_uses_search_when_no_staged_or_funnel(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inventory_path = root / "inventory.csv"
            search_path = root / "search.csv"
            events_path = root / "events.csv"
            inventory_path.write_text("status,type,asset,primary_query,cta,owner_note\n", encoding="utf-8")
            search_path.write_text(
                "query,page,clicks,impressions,ctr,position\n"
                "setup guide,/docs/setup,0,100,0,12\n",
                encoding="utf-8",
            )
            events_path.write_text("date,asset,event,count\n", encoding="utf-8")

            plan = build_daily_plan(inventory_path, search_path, events_path)

        self.assertEqual(plan.action_type, "search_striking_distance")
        self.assertEqual(plan.asset, "/docs/setup")
        self.assertEqual(plan.evidence["decision"]["selected_rule"], "search_opportunity")
        self.assertEqual(plan.evidence["decision"]["winner"]["signal_summary"][0], "query=setup guide")

    def test_planner_uses_configurable_funnel_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inventory_path = root / "inventory.csv"
            search_path = root / "search.csv"
            events_path = root / "events.csv"
            inventory_path.write_text(
                "status,type,asset,primary_query,cta,owner_note\n"
                "published,docs,/docs/home,home query,Try it,Published\n",
                encoding="utf-8",
            )
            search_path.write_text(
                "query,page,clicks,impressions,ctr,position\n"
                "setup guide,/docs/setup,0,100,0,12\n",
                encoding="utf-8",
            )
            events_path.write_text(
                "date,asset,event,count\n"
                "2026-05-20,/docs/home,view,100\n"
                "2026-05-20,/docs/home,cta,4\n"
                "2026-05-20,/docs/home,conversion,1\n",
                encoding="utf-8",
            )

            plan = build_daily_plan(inventory_path, search_path, events_path, weak_cta_rate=0.03)

        self.assertEqual(plan.action_type, "search_striking_distance")
        self.assertIn("weak_cta_rate", plan.evidence["decision"]["thresholds"])

    def test_planner_uses_schema_aliases_for_search_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inventory_path = root / "inventory.csv"
            search_path = root / "search.csv"
            events_path = root / "events.csv"
            inventory_path.write_text("status,type,asset,primary_query,cta,owner_note\n", encoding="utf-8")
            search_path.write_text(
                "search_term,url,clicks,shown,ctr,rank\n"
                "setup guide,/docs/setup,0,100,0,12\n",
                encoding="utf-8",
            )
            events_path.write_text("date,asset,event,count\n", encoding="utf-8")

            plan = build_daily_plan(
                inventory_path,
                search_path,
                events_path,
                aliases={"search_rows": {"search_term": "query", "url": "page", "shown": "impressions", "rank": "position"}},
            )

        self.assertEqual(plan.action_type, "search_striking_distance")
        self.assertEqual(plan.asset, "/docs/setup")

    def test_plan_markdown_renders_candidate_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = write_defaults(
                Path(temp_dir),
                "status,type,asset,primary_query,cta,owner_note\n"
                "staged,guide,/docs/staged,staged query,Try it,Needs release\n",
            )

            plan = build_daily_plan(*paths)
            markdown = render_plan_markdown(plan)

        self.assertIn("### Candidate Comparison", markdown)
        self.assertIn("lost because", markdown)
        self.assertIn("### Audit Notes", markdown)
        self.assertIn("## Data Freshness", markdown)

    def test_plan_records_stale_freshness_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = write_defaults(
                Path(temp_dir),
                "status,type,asset,primary_query,cta,owner_note\n"
                "staged,guide,/docs/staged,staged query,Try it,Needs release\n",
            )

            plan = build_daily_plan(*paths, freshness_warn_days=7, today="2026-06-03")

        self.assertFalse(plan.evidence["freshness"]["ok"])
        self.assertTrue(any("events" in warning for warning in plan.evidence["freshness"]["warnings"]))

    def test_decision_trace_explains_memory_cooldown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inventory_path = root / "inventory.csv"
            search_path = root / "search.csv"
            events_path = root / "events.csv"
            memory_path = root / "action_memory.csv"
            inventory_path.write_text("status,type,asset,primary_query,cta,owner_note\n", encoding="utf-8")
            search_path.write_text(
                "query,page,clicks,impressions,ctr,position\n"
                "setup guide,/docs/setup,0,100,0,12\n",
                encoding="utf-8",
            )
            events_path.write_text("date,asset,event,count\n", encoding="utf-8")
            memory_path.write_text(
                "id,status,asset,action_type,source,completed_on,outcome_on,outcome,impact,confidence,artifact,note\n"
                "2026-05-20-001,completed,/docs/setup,search_striking_distance,search_opportunity,2026-05-20,,,,,,Improved title\n",
                encoding="utf-8",
            )

            plan = build_daily_plan(inventory_path, search_path, events_path, memory_path=memory_path)

        self.assertEqual(plan.action_type, "record_outcome")
        comparison = plan.evidence["decision"]["comparison"][0]
        self.assertTrue(comparison["blocked_by"])
        self.assertTrue(any("pending outcome" in note for note in comparison["memory_notes"]))
        self.assertTrue(any("blocked" in reason for reason in comparison["lost_because"]))


if __name__ == "__main__":
    unittest.main()
