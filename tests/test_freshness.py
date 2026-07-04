from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_growth_loop.freshness import (
    build_freshness_report,
    render_freshness_markdown,
    write_freshness_reports,
)


class FreshnessTests(unittest.TestCase):
    def test_events_warn_when_latest_date_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            events = root / "events.csv"
            events.write_text(
                "date,asset,event,count\n"
                "2026-05-01,/docs/setup,view,10\n",
                encoding="utf-8",
            )

            report = build_freshness_report({"events": events}, warn_after_days=14, today="2026-06-03")
            markdown = render_freshness_markdown(report)

        self.assertFalse(report.ok)
        self.assertEqual(report.checks[0].status, "stale")
        self.assertEqual(report.checks[0].age_days, 33)
        self.assertIn("events: Latest data is 33 days old", markdown)

    def test_sample_files_are_not_treated_as_stale_real_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            events = root / "events.example.csv"
            events.write_text(
                "date,asset,event,count\n"
                "2020-01-01,/docs/setup,view,10\n",
                encoding="utf-8",
            )

            report = build_freshness_report({"events": events}, warn_after_days=14, today="2026-06-03")

        self.assertTrue(report.ok)
        self.assertEqual(report.checks[0].status, "sample")
        self.assertEqual(report.warnings, [])

    def test_aliases_are_used_for_date_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            events = root / "events.csv"
            events.write_text(
                "day,path,kind,total\n"
                "2026-06-01,/docs/setup,view,10\n",
                encoding="utf-8",
            )

            report = build_freshness_report(
                {"events": events},
                aliases={"events": {"day": "date", "path": "asset", "kind": "event", "total": "count"}},
                warn_after_days=14,
                today="2026-06-03",
            )

        self.assertTrue(report.ok)
        self.assertEqual(report.checks[0].latest_date, "2026-06-01")

    def test_mtime_inputs_are_current_when_modified_after_check_date(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inventory = root / "content_inventory.csv"
            inventory.write_text(
                "status,type,asset,primary_query,cta,owner_note\n"
                "planned,docs,/docs/setup,setup docs,Try setup,Planned page\n",
                encoding="utf-8",
            )

            report = build_freshness_report({"content_inventory": inventory}, warn_after_days=14, today="2020-01-01")

        self.assertTrue(report.ok)
        self.assertEqual(report.checks[0].status, "fresh")
        self.assertEqual(report.checks[0].age_days, 0)
        self.assertIn("modified after the check date", report.checks[0].reason)

    def test_write_freshness_reports_writes_latest_and_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            events = root / "events.example.csv"
            events.write_text("date,asset,event,count\n", encoding="utf-8")
            report = build_freshness_report({"events": events}, today="2026-06-03")

            md_path, md_history, json_path, json_history = write_freshness_reports(report, root / "outbox")

        self.assertEqual(md_path.name, "latest-freshness.md")
        self.assertTrue(md_history.name.endswith("-freshness.md"))
        self.assertEqual(json_path.name, "latest-freshness.json")
        self.assertTrue(json_history.name.endswith("-freshness.json"))


if __name__ == "__main__":
    unittest.main()
