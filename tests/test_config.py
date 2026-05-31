from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_growth_loop.config import apply_column_aliases, load_config


class ConfigTests(unittest.TestCase):
    def test_loads_schema_aliases_from_workspace_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "open-growth-loop.toml").write_text(
                "[schema_aliases.search_rows]\n"
                "search_term = \"query\"\n"
                "url = \"page\"\n",
                encoding="utf-8",
            )

            config = load_config(root)

        self.assertEqual(config.aliases_for("search_rows"), {"search_term": "query", "url": "page"})

    def test_apply_column_aliases_renames_source_fields(self) -> None:
        row = apply_column_aliases(
            {"search_term": "setup guide", "url": "/docs/setup", "impressions": "100"},
            {"search_term": "query", "url": "page"},
        )

        self.assertEqual(row["query"], "setup guide")
        self.assertEqual(row["page"], "/docs/setup")
        self.assertNotIn("search_term", row)

    def test_load_config_accepts_utf8_bom(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "open-growth-loop.toml").write_text(
                "[schema_aliases.events]\n"
                "path = \"asset\"\n",
                encoding="utf-8-sig",
            )

            config = load_config(root)

        self.assertEqual(config.aliases_for("events"), {"path": "asset"})

    def test_loads_thresholds_from_workspace_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "open-growth-loop.toml").write_text(
                "[thresholds]\n"
                "minimum_impressions = 50\n"
                "minimum_views = 75\n"
                "weak_cta_rate = 0.03\n"
                "review_days = 21\n",
                encoding="utf-8",
            )

            config = load_config(root)

        self.assertEqual(config.thresholds.minimum_impressions, 50)
        self.assertEqual(config.thresholds.minimum_views, 75)
        self.assertEqual(config.thresholds.weak_cta_rate, 0.03)
        self.assertEqual(config.thresholds.review_days, 21)

    def test_rejects_invalid_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "open-growth-loop.toml").write_text(
                "[thresholds]\n"
                "weak_cta_rate = 2\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_config(root)


if __name__ == "__main__":
    unittest.main()
