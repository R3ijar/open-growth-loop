from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from open_growth_loop.io_utils import read_csv_rows
from open_growth_loop.memory import (
    read_action_memory,
    record_completion,
    record_outcome,
)


class MemoryTests(unittest.TestCase):
    def test_record_completion_creates_pending_action_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory = Path(temp_dir) / "action_memory.csv"

            row = record_completion(
                memory,
                asset="/docs/setup",
                action_type="search_striking_distance",
                source="search_opportunity",
                artifact="https://example.org/docs/setup",
                note="Updated setup intro",
            )
            records = read_action_memory(memory)

        self.assertEqual(row["status"], "completed")
        self.assertEqual(records[0].asset, "/docs/setup")
        self.assertTrue(records[0].pending_outcome)

    def test_record_outcome_updates_latest_matching_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory = Path(temp_dir) / "action_memory.csv"
            record_completion(memory, asset="/docs/setup", action_type="search_striking_distance")

            row = record_outcome(
                memory,
                asset="/docs/setup",
                outcome="directionally positive",
                confidence="medium",
                note="Clicks moved up after the docs change",
            )
            rows = read_csv_rows(memory)

        self.assertEqual(row["status"], "measured")
        self.assertEqual(row["outcome"], "directionally_positive")
        self.assertEqual(row["impact"], 1.0)
        self.assertEqual(rows[0]["confidence"], "medium")


if __name__ == "__main__":
    unittest.main()
