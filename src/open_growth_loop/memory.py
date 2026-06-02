from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .io_utils import parse_float, read_csv_rows, today_iso, write_csv_rows

FIELDS = [
    "id",
    "status",
    "asset",
    "action_type",
    "source",
    "completed_on",
    "outcome_on",
    "outcome",
    "impact",
    "confidence",
    "artifact",
    "note",
]

POSITIVE_OUTCOMES = {"directionally_positive", "positive", "worked", "improved"}
NEGATIVE_OUTCOMES = {"needs_iteration", "no_visible_change", "negative", "regressed"}
NEUTRAL_OUTCOMES = {"insufficient_sample", "not_enough_data", "unknown"}


@dataclass(frozen=True)
class ActionMemoryRecord:
    id: str
    status: str
    asset: str
    action_type: str
    source: str
    completed_on: str
    outcome_on: str
    outcome: str
    impact: float
    confidence: str
    artifact: str
    note: str

    @property
    def pending_outcome(self) -> bool:
        return self.status == "completed" and not self.outcome

    @property
    def positive(self) -> bool:
        return normalized_outcome(self.outcome) in POSITIVE_OUTCOMES or self.impact > 0

    @property
    def negative(self) -> bool:
        return normalized_outcome(self.outcome) in NEGATIVE_OUTCOMES or self.impact < 0


def read_action_memory(memory_path: Path, aliases: Mapping[str, str] | None = None) -> list[ActionMemoryRecord]:
    rows = read_csv_rows(memory_path, aliases)
    return [_record_from_row(row) for row in rows]


def record_completion(
    memory_path: Path,
    asset: str,
    action_type: str,
    source: str = "",
    artifact: str = "",
    note: str = "",
    aliases: Mapping[str, str] | None = None,
) -> dict[str, object]:
    action_type = action_type.strip()
    if not asset.strip() and action_type != "wait_for_data":
        raise ValueError("asset is required unless the action is wait_for_data")
    if not action_type:
        raise ValueError("action_type is required")

    rows = read_csv_rows(memory_path, aliases)
    row = {
        "id": f"{today_iso()}-{len(rows) + 1:03d}",
        "status": "completed",
        "asset": asset.strip(),
        "action_type": action_type,
        "source": source.strip(),
        "completed_on": today_iso(),
        "outcome_on": "",
        "outcome": "",
        "impact": "",
        "confidence": "",
        "artifact": artifact.strip(),
        "note": note.strip(),
    }
    rows.append(row)
    write_csv_rows(memory_path, FIELDS, rows)
    return row


def record_outcome(
    memory_path: Path,
    outcome: str,
    record_id: str = "",
    asset: str = "",
    impact: float | None = None,
    confidence: str = "",
    note: str = "",
    aliases: Mapping[str, str] | None = None,
) -> dict[str, object]:
    normalized = normalized_outcome(outcome)
    if not normalized:
        raise ValueError("outcome is required")
    if not record_id.strip() and not asset.strip():
        raise ValueError("record_id or asset is required")

    rows = read_csv_rows(memory_path, aliases)
    if not rows:
        raise ValueError(f"no action memory found in {memory_path}")

    index = _find_record_index(rows, record_id.strip(), asset.strip())
    if index is None:
        target = record_id.strip() or asset.strip()
        raise ValueError(f"no matching action memory record found for {target}")

    row = rows[index]
    row["status"] = "measured"
    row["outcome_on"] = today_iso()
    row["outcome"] = normalized
    row["impact"] = _impact_value(normalized, impact)
    if confidence.strip():
        row["confidence"] = confidence.strip()
    if note.strip():
        row["note"] = note.strip()
    rows[index] = row
    write_csv_rows(memory_path, FIELDS, rows)
    return row


def normalized_outcome(outcome: str) -> str:
    return outcome.strip().lower().replace(" ", "_").replace("-", "_")


def _record_from_row(row: dict[str, str]) -> ActionMemoryRecord:
    return ActionMemoryRecord(
        id=row.get("id", ""),
        status=row.get("status", ""),
        asset=row.get("asset", ""),
        action_type=row.get("action_type", ""),
        source=row.get("source", ""),
        completed_on=row.get("completed_on", ""),
        outcome_on=row.get("outcome_on", ""),
        outcome=normalized_outcome(row.get("outcome", "")),
        impact=parse_float(row.get("impact"), 0.0),
        confidence=row.get("confidence", ""),
        artifact=row.get("artifact", ""),
        note=row.get("note", ""),
    )


def _find_record_index(rows: list[dict[str, str]], record_id: str, asset: str) -> int | None:
    if record_id:
        for index, row in enumerate(rows):
            if row.get("id", "") == record_id:
                return index
        return None

    matched_index: int | None = None
    for index, row in enumerate(rows):
        if row.get("asset", "") == asset:
            matched_index = index
    return matched_index


def _impact_value(outcome: str, impact: float | None) -> float:
    if impact is not None:
        return impact
    if outcome in POSITIVE_OUTCOMES:
        return 1.0
    if outcome in NEGATIVE_OUTCOMES:
        return -1.0
    return 0.0
