from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_growth_loop.config import load_config
from open_growth_loop.doctor import build_doctor_report, write_doctor_reports


class DoctorTests(unittest.TestCase):
    def test_doctor_report_summarizes_workspace_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_workspace(root)

            report = build_doctor_report(root, load_config(root))
            md_path, _, json_path, _ = write_doctor_reports(report, root / "outbox" / "doctor")
            markdown_exists = md_path.exists()
            json_exists = json_path.exists()

        self.assertTrue(report.ok)
        self.assertTrue(markdown_exists)
        self.assertTrue(json_exists)
        self.assertIn("Workspace validation", [check.name for check in report.checks])
        self.assertIn("Daily plan", [check.name for check in report.checks])
        self.assertTrue(report.next_steps)


def _write_workspace(root: Path) -> None:
    data = root / "data"
    data.mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        "[project]\n"
        "name = \"doctor-project\"\n"
        "version = \"0.1.0\"\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text("# Doctor Project\n\n## Planner Engine Coverage\n\nGeneric maintainer surfaces.\n", encoding="utf-8")
    (root / "CHANGELOG.md").write_text("# Changelog\n\n## Unreleased\n\n- Add doctor workflow.\n", encoding="utf-8")
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
