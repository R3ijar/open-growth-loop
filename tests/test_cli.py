from __future__ import annotations

import json
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from test_audit import _write_healthy_repo

from open_growth_loop.cli import load_plan, run_audit, run_steward
from open_growth_loop.config import GrowthConfig


class LoadPlanTests(unittest.TestCase):
    def test_audit_loads_profile_from_explicit_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            repository = Path(temp_dir) / "repository"
            workspace.mkdir()
            repository.mkdir()
            _write_healthy_repo(repository)
            readme = (repository / "README.md").read_text(encoding="utf-8")
            (repository / "README.md").write_text(
                readme.replace("## Install\n\n```bash\npip install example-project\n```\n\n", ""),
                encoding="utf-8",
            )
            (repository / "open-growth-loop.toml").write_text(
                "[audit_profile]\n"
                'purpose = "example"\n'
                "\n[audit_profile.checks.install]\n"
                'disposition = "qualify"\n'
                'reason = "Installation is taught by the surrounding tutorial."\n',
                encoding="utf-8",
            )
            output = StringIO()

            with redirect_stdout(output):
                run_audit(
                    Namespace(repo=str(repository), summary="", strict=False),
                    workspace,
                    GrowthConfig(path=None, schema_aliases={}),
                )

            result = json.loads(output.getvalue())
            report = json.loads((workspace / "outbox" / "audit" / "latest-audit.json").read_text(encoding="utf-8"))

        self.assertEqual(result["score"]["qualified"], 1)
        self.assertIsNone(result["recommended_action"])
        self.assertEqual(report["profile"]["purpose"], "example")

    def test_steward_no_write_does_not_create_outbox(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            _write_healthy_repo(workspace)
            output = StringIO()

            with redirect_stdout(output):
                run_steward(Namespace(repo="", no_write=True), workspace, GrowthConfig(path=None, schema_aliases={}))

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
