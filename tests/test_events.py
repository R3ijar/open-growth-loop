from __future__ import annotations

import unittest
from pathlib import Path

from open_growth_loop.events import import_aggregate_events, read_event_rollups


class EventImportTests(unittest.TestCase):
    def test_import_aggregate_events_groups_rows(self) -> None:
        with self.subTest("aggregate rows"):
            import tempfile

            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                source = root / "events.csv"
                output = root / "out.csv"
                source.write_text(
                    "date,asset,event,count\n"
                    "2026-05-20,/docs/start,page_view,2\n"
                    "2026-05-20,/docs/start,view,3\n"
                    "2026-05-20,/docs/start,cta_click,1\n",
                    encoding="utf-8",
                )

                rows_written = import_aggregate_events(source, output)
                rollups = read_event_rollups(output)

        self.assertEqual(rows_written, 2)
        self.assertEqual(rollups[0].asset, "/docs/start")
        self.assertEqual(rollups[0].views, 5)
        self.assertEqual(rollups[0].ctas, 1)

    def test_import_rejects_private_columns(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "events.csv"
            output = root / "out.csv"
            source.write_text(
                "date,asset,event,count,email\n"
                "2026-05-20,/docs/start,view,1,a@example.com\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                import_aggregate_events(source, output)


if __name__ == "__main__":
    unittest.main()
