from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_growth_loop.config import load_config
from open_growth_loop.doctor import build_doctor_report, write_doctor_reports

from .test_demo import _write_workspace


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


if __name__ == "__main__":
    unittest.main()
