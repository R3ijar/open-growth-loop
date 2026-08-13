from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_growth_loop.cli import generate_demo_reports
from open_growth_loop.config import load_config


class DemoCommandTests(unittest.TestCase):
    def test_generate_demo_reports_writes_reviewable_report_set(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_workspace(root)

            payload = generate_demo_reports(root, load_config(root))
            reports = payload["reports"]
            plan_exists = Path(reports["plan"]).exists()
            doctor_exists = Path(reports["doctor"]).exists()
            release_brief_exists = Path(reports["release_brief"]).exists()
            steward_exists = Path(reports["steward"]).exists()
            report_index_exists = Path(reports["report_index"]).exists()
            report_index_json_exists = Path(reports["report_index_json"]).exists()

        self.assertTrue(payload["validation_ok"])
        self.assertTrue(payload["privacy_ok"])
        self.assertEqual(payload["candidates"], 3)
        self.assertEqual(payload["opportunities"], 1)
        self.assertEqual(payload["report_index_available"], 13)
        self.assertIn("audit_score_percent", payload)
        self.assertTrue(plan_exists)
        self.assertTrue(doctor_exists)
        self.assertTrue(release_brief_exists)
        self.assertTrue(steward_exists)
        self.assertTrue(report_index_exists)
        self.assertTrue(report_index_json_exists)


def _write_workspace(root: Path) -> None:
    data = root / "data"
    data.mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        "[project]\n"
        "name = \"demo-project\"\n"
        "version = \"0.1.0\"\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text("# Demo Project\n\n## Planner Engine Coverage\n\nGeneric maintainer surfaces.\n", encoding="utf-8")
    (root / "CHANGELOG.md").write_text("# Changelog\n\n## Unreleased\n\n- Add demo report workflow.\n", encoding="utf-8")
    (data / "content_inventory.csv").write_text(
        "status,type,asset,primary_query,cta,owner_note\n"
        "staged,guide,/docs/setup,setup docs,Try setup,Needs release evidence\n",
        encoding="utf-8",
    )
    (data / "search_console_rows.csv").write_text(
        "query,page,clicks,impressions,ctr,position\n"
        "setup docs,/docs/setup,0,100,0.0,12.0\n",
        encoding="utf-8",
    )
    (data / "events.csv").write_text(
        "date,asset,event,count\n"
        "2026-06-01,/docs/setup,view,50\n"
        "2026-06-01,/docs/setup,cta,1\n",
        encoding="utf-8",
    )
    (data / "experiments.csv").write_text(
        "id,status,asset,action_type,planned_on,review_after,shipped_on,baseline_impressions,baseline_clicks,baseline_views,baseline_conversions,artifact,note,outcome\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
