from __future__ import annotations

import unittest
from pathlib import Path

from open_growth_loop.config import load_config
from open_growth_loop.planner import build_daily_plan, default_data_paths
from open_growth_loop.workspace import validate_workspace


ROOT = Path(__file__).resolve().parents[1]


class ExampleWorkspaceTests(unittest.TestCase):
    def test_example_workspaces_validate_and_plan_as_documented(self) -> None:
        expectations = {
            "staged-release-check": ("release_evidence", "/docs/configuration-checklist"),
            "funnel-dropoff": ("fix_funnel", "/docs/getting-started"),
            "aliased-search-export": ("search_striking_distance", "/guides/plugin-migration"),
        }

        for workspace_name, (expected_action, expected_asset) in expectations.items():
            with self.subTest(workspace=workspace_name):
                workspace = ROOT / "examples" / workspace_name
                config = load_config(workspace)
                validation = validate_workspace(workspace, config)
                inventory, search_rows, events = default_data_paths(workspace)

                plan = build_daily_plan(inventory, search_rows, events, aliases=config.schema_aliases)

                self.assertTrue(validation.ok, validation.errors)
                self.assertEqual(plan.action_type, expected_action)
                self.assertEqual(plan.asset, expected_asset)
                self.assertTrue((workspace / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
