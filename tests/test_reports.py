from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_growth_loop.io_utils import write_json_report, write_text_report
from open_growth_loop.planner import DailyPlan, write_plan_reports


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


if __name__ == "__main__":
    unittest.main()
