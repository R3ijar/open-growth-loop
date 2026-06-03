from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_growth_loop.io_utils import write_json_report, write_text_report
from open_growth_loop.planner import DailyPlan, render_plan_markdown, write_plan_reports
from open_growth_loop.report_index import build_report_index, render_report_index, write_report_index


class ReportHistoryTests(unittest.TestCase):
    def test_text_report_writes_latest_and_dated_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            latest, history = write_text_report(Path(temp_dir) / "latest-report.md", "hello\n", "2026-05-30")

            latest_text = latest.read_text(encoding="utf-8")
            history_text = history.read_text(encoding="utf-8")

        self.assertEqual(latest.name, "latest-report.md")
        self.assertEqual(history.name, "2026-05-30-report.md")
        self.assertEqual(latest_text, "hello\n")
        self.assertEqual(history_text, "hello\n")

    def test_json_report_writes_latest_and_dated_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            latest, history = write_json_report(Path(temp_dir) / "latest-report.json", {"b": 2, "a": 1}, "2026-05-30")

            latest_text = latest.read_text(encoding="utf-8")
            history_text = history.read_text(encoding="utf-8")

        self.assertEqual(history.name, "2026-05-30-report.json")
        self.assertEqual(latest_text, history_text)
        self.assertIn('"a": 1', latest_text)

    def test_plan_report_writes_history_files(self) -> None:
        plan = DailyPlan(
            action_type="wait_for_data",
            asset="",
            title="Wait for more evidence",
            reason="No stronger signal exists.",
            confidence="high",
            next_steps=[],
            evidence={},
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            md_path, json_path = write_plan_reports(plan, Path(temp_dir))

            md_history = next((Path(temp_dir) / "history").glob("*-plan.md"))
            json_history = next((Path(temp_dir) / "history").glob("*-plan.json"))

        self.assertEqual(md_path.name, "latest-plan.md")
        self.assertEqual(json_path.name, "latest-plan.json")
        self.assertTrue(md_history.name.endswith("-plan.md"))
        self.assertTrue(json_history.name.endswith("-plan.json"))

    def test_plan_markdown_has_reader_first_sections(self) -> None:
        plan = DailyPlan(
            action_type="search_striking_distance",
            asset="/docs/setup",
            title="Improve search fit for /docs/setup",
            reason="The page is close to page one with weak CTR.",
            confidence="medium",
            next_steps=["Review the query/page fit."],
            evidence={
                "decision": {
                    "selected_rule": "search_opportunity",
                    "why_selected": "Search opportunity ranked first.",
                    "winner": {
                        "rank": 1,
                        "action_type": "search_striking_distance",
                        "asset": "/docs/setup",
                        "source": "search_opportunity",
                        "confidence": "medium",
                        "score": 12.5,
                        "selection_reason": "Selected after conservative ranking.",
                    },
                    "comparison": [],
                    "audit_notes": ["Scores rank candidates inside a rule."],
                },
                "freshness": {
                    "ok": True,
                    "checks": [
                        {
                            "name": "events",
                            "status": "fresh",
                            "source": "latest_date",
                            "latest_date": "2026-06-02",
                            "age_days": 1,
                            "reason": "Latest data is within the warning window.",
                        }
                    ],
                    "warnings": [],
                },
            },
        )

        markdown = render_plan_markdown(plan)

        self.assertIn("## Summary", markdown)
        self.assertIn("| Recommended action | search_striking_distance |", markdown)
        self.assertIn("## Decision Trace", markdown)
        self.assertIn("Raw evidence JSON", markdown)

    def test_report_index_links_generated_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = root / "outbox" / "plans" / "latest-plan.md"
            report_path.parent.mkdir(parents=True)
            report_path.write_text("# Plan\n", encoding="utf-8")

            index = build_report_index(root)
            markdown = render_report_index(index)
            latest, history = write_report_index(index, root / "outbox")

        self.assertEqual(index.available_count, 1)
        self.assertIn("[plans/latest-plan.md](plans/latest-plan.md)", markdown)
        self.assertIn("Recommended Reading Order", markdown)
        self.assertEqual(latest.name, "index.md")
        self.assertTrue(history.name.endswith("-index.md"))


if __name__ == "__main__":
    unittest.main()
