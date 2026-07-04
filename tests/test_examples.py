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
            "staged-release-check": ("release_evidence", "/docs/configuration-checklist", "release_evidence"),
            "funnel-dropoff": ("fix_funnel", "/docs/getting-started", "fix_funnel"),
            "aliased-search-export": ("search_striking_distance", "/guides/plugin-migration", "search_opportunity"),
            "package-page-cta": ("fix_funnel", "/packages/example-cli", "fix_funnel"),
            "release-notes-search": ("search_striking_distance", "/changelog/v0.1.2", "search_opportunity"),
        }

        for workspace_name, (expected_action, expected_asset, expected_source) in expectations.items():
            with self.subTest(workspace=workspace_name):
                workspace = ROOT / "examples" / workspace_name
                config = load_config(workspace)
                validation = validate_workspace(workspace, config)
                inventory, search_rows, events = default_data_paths(workspace)

                plan = build_daily_plan(inventory, search_rows, events, aliases=config.schema_aliases)

                self.assertTrue(validation.ok, validation.errors)
                self.assertEqual(plan.action_type, expected_action)
                self.assertEqual(plan.asset, expected_asset)
                self.assertEqual(plan.evidence["decision"]["selected_rule"], expected_source)
                self.assertTrue((workspace / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
