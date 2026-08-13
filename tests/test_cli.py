from __future__ import annotations

import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from test_audit import _write_healthy_repo

from open_growth_loop.cli import load_plan, run_steward


class LoadPlanTests(unittest.TestCase):
    def test_steward_no_write_does_not_create_outbox(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            _write_healthy_repo(workspace)
            output = StringIO()

            with redirect_stdout(output):
                run_steward(Namespace(repo="", no_write=True), workspace)

            self.assertFalse((workspace / "outbox").exists())
            self.assertIn('"written": false', output.getvalue())

    def test_missing_plan_json_raises_friendly_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            plan_json = workspace / "outbox" / "plans" / "latest-plan.json"

            with self.assertRaises(SystemExit) as raised:
                load_plan(plan_json, workspace)

        self.assertIn("Plan JSON not found", str(raised.exception))
        self.assertIn("ogl plan", str(raised.exception))

    def test_invalid_json_raises_friendly_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            plan_json = workspace / "latest-plan.json"
            plan_json.write_text("{not json", encoding="utf-8")

            with self.assertRaises(SystemExit) as raised:
                load_plan(plan_json, workspace)

        self.assertIn("could not be read", str(raised.exception))

    def test_wrong_schema_raises_friendly_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            plan_json = workspace / "latest-plan.json"
            plan_json.write_text('{"unexpected_field": true}', encoding="utf-8")

            with self.assertRaises(SystemExit) as raised:
                load_plan(plan_json, workspace)

        self.assertIn("does not match the expected plan schema", str(raised.exception))

    def test_non_object_payload_raises_friendly_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            plan_json = workspace / "latest-plan.json"
            plan_json.write_text('["not", "a", "plan"]', encoding="utf-8")

            with self.assertRaises(SystemExit) as raised:
                load_plan(plan_json, workspace)

        self.assertIn("must contain a JSON object", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
