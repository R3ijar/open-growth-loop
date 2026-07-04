from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_growth_loop.config import load_config
from open_growth_loop.release_brief import (
    build_release_brief,
    render_release_brief_markdown,
    write_release_brief_reports,
)


class ReleaseBriefTests(unittest.TestCase):
    def test_release_brief_summarizes_workspace_and_examples(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_release_workspace(root)
            _write_example_workspace(root / "examples" / "package-page-cta")

            brief = build_release_brief(root, load_config(root), generated_at="2026-06-03")
            markdown = render_release_brief_markdown(brief)
            md_path, md_history, json_path, json_history = write_release_brief_reports(brief, root / "outbox" / "release-brief")

            md_text = md_path.read_text(encoding="utf-8")

        self.assertTrue(brief.ready)
        self.assertEqual(brief.project_name, "example-project")
        self.assertEqual(brief.version, "0.9.0")
        self.assertEqual(brief.latest_plan["action_type"], "release_evidence")
        self.assertEqual(brief.examples[0].action_type, "fix_funnel")
        self.assertTrue(brief.changelog.release_notes_present)
        self.assertIn("Claim Guardrails", markdown)
        self.assertIn("Do not claim stars", md_text)
        self.assertEqual(md_path.name, "latest-release-brief.md")
        self.assertTrue(md_history.name.endswith("-release-brief.md"))
        self.assertEqual(json_path.name, "latest-release-brief.json")
        self.assertTrue(json_history.name.endswith("-release-brief.json"))

    def test_release_brief_fails_when_readme_coverage_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _write_release_workspace(root, readme="No planner coverage yet.\n")

            brief = build_release_brief(root, load_config(root), generated_at="2026-06-03")

        self.assertFalse(brief.ready)
        self.assertTrue(any(item.name == "README explains planner coverage" and item.status == "fail" for item in brief.checklist))


def _write_release_workspace(root: Path, readme: str = "# Example\n\n## Planner Engine Coverage\n\nGeneric maintainer surfaces.\n") -> None:
    (root / "data").mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        "[project]\n"
        "name = \"example-project\"\n"
        "version = \"0.9.0\"\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text(readme, encoding="utf-8")
    (root / "CHANGELOG.md").write_text(
        "# Changelog\n"
        "\n"
        "## Unreleased\n"
        "\n"
        "- Add release brief workflow.\n"
        "\n"
        "## 0.9.0 - 2026-06-03\n"
        "\n"
        "- Previous release.\n",
        encoding="utf-8",
    )
    (root / "data" / "content_inventory.csv").write_text(
        "status,type,asset,primary_query,cta,owner_note\n"
        "staged,docs,/docs/setup,setup docs,Try setup,Needs release evidence\n",
        encoding="utf-8",
    )
    (root / "data" / "search_console_rows.csv").write_text(
        "query,page,clicks,impressions,ctr,position\n"
        "setup docs,/docs/setup,2,120,0.016,12.0\n",
        encoding="utf-8",
    )
    (root / "data" / "events.csv").write_text(
        "date,asset,event,count\n"
        "2026-06-01,/docs/setup,view,90\n"
        "2026-06-01,/docs/setup,cta,2\n"
        "2026-06-01,/docs/setup,conversion,0\n",
        encoding="utf-8",
    )
    (root / "data" / "experiments.csv").write_text(
        "id,status,asset,action_type,planned_on,review_after,shipped_on,baseline_impressions,baseline_clicks,baseline_views,baseline_conversions,artifact,note,outcome\n"
        "2026-05-20-001,shipped,/docs/old,search_striking_distance,2026-05-20,2026-06-03,2026-06-01,100,1,80,2,https://example.org/docs/old,Synthetic old docs follow-up,directionally_positive\n",
        encoding="utf-8",
    )


def _write_example_workspace(root: Path) -> None:
    (root / "data").mkdir(parents=True)
    (root / "README.md").write_text("# Package Page CTA\n", encoding="utf-8")
    (root / "data" / "content_inventory.csv").write_text(
        "status,type,asset,primary_query,cta,owner_note\n"
        "published,package_page,/packages/example-cli,example cli package,Install package,Synthetic package page\n",
        encoding="utf-8",
    )
    (root / "data" / "search_console_rows.csv").write_text(
        "query,page,clicks,impressions,ctr,position\n"
        "example cli package,/packages/example-cli,20,400,0.05,4.0\n",
        encoding="utf-8",
    )
    (root / "data" / "events.csv").write_text(
        "date,asset,event,count\n"
        "2026-06-01,/packages/example-cli,view,300\n"
        "2026-06-01,/packages/example-cli,cta,3\n"
        "2026-06-01,/packages/example-cli,conversion,0\n",
        encoding="utf-8",
    )
    (root / "data" / "experiments.csv").write_text(
        "id,status,asset,action_type,planned_on,review_after,shipped_on,baseline_impressions,baseline_clicks,baseline_views,baseline_conversions,artifact,note,outcome\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
