from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .config import apply_header_aliases
from .io_utils import parse_int, read_csv_header, read_csv_rows, write_csv_rows

ALLOWED_EVENT_COLUMNS = {"date", "asset", "event", "count"}
PRIVATE_COLUMN_HINTS = {
    "email",
    "user",
    "userid",
    "user_id",
    "session",
    "sessionid",
    "session_id",
    "ip",
    "address",
    "payload",
    "token",
    "secret",
    "key",
    "file",
    "phone",
    "name",
    "sku",
}


@dataclass(frozen=True)
class EventRollup:
    asset: str
    views: int
    ctas: int
    conversions: int
    events: dict[str, int]

    @property
    def cta_rate(self) -> float:
        return self.ctas / self.views if self.views else 0.0

    @property
    def conversion_rate(self) -> float:
        return self.conversions / self.views if self.views else 0.0


def validate_event_columns(fieldnames: list[str]) -> None:
    normalized = {field.strip().lower() for field in fieldnames}
    private = {field for field in normalized if field in PRIVATE_COLUMN_HINTS}
    if private:
        raise ValueError(f"Private-looking event columns are not allowed: {', '.join(sorted(private))}")
    unknown = normalized - ALLOWED_EVENT_COLUMNS
    if unknown:
        raise ValueError(f"Unexpected event columns: {', '.join(sorted(unknown))}")


def import_aggregate_events(source: Path, output: Path, aliases: Mapping[str, str] | None = None) -> int:
    raw_header = read_csv_header(source)
    private = sorted({field for field in _normalize_fields(raw_header) if field in PRIVATE_COLUMN_HINTS})
    if private:
        raise ValueError(f"Private-looking event columns are not allowed: {', '.join(private)}")

    effective_header, _ = apply_header_aliases(raw_header, aliases)
    if effective_header:
        validate_event_columns(effective_header)

    rows = read_csv_rows(source, aliases)
    if not rows:
        write_csv_rows(output, ["date", "asset", "event", "count"], [])
        return 0

    grouped: dict[tuple[str, str, str], int] = defaultdict(int)
    for row in rows:
        date = row.get("date", "").strip()
        asset = row.get("asset", "").strip()
        event = normalize_event(row.get("event", ""))
        count = parse_int(row.get("count"), 1)
        if not date or not asset or not event:
            continue
        grouped[(date, asset, event)] += max(count, 0)

    output_rows = [
        {"date": date, "asset": asset, "event": event, "count": count}
        for (date, asset, event), count in sorted(grouped.items())
    ]
    write_csv_rows(output, ["date", "asset", "event", "count"], output_rows)
    return len(output_rows)


def read_event_rollups(path: Path, aliases: Mapping[str, str] | None = None) -> list[EventRollup]:
    per_asset: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in read_csv_rows(path, aliases):
        asset = row.get("asset", "").strip()
        event = normalize_event(row.get("event", ""))
        count = parse_int(row.get("count"), 1)
        if asset and event:
            per_asset[asset][event] += max(count, 0)

    rollups: list[EventRollup] = []
    for asset, counts in per_asset.items():
        views = counts.get("view", 0)
        ctas = counts.get("cta", 0)
        conversions = counts.get("conversion", 0)
        rollups.append(EventRollup(asset=asset, views=views, ctas=ctas, conversions=conversions, events=dict(counts)))
    return sorted(rollups, key=lambda item: (item.views, item.conversions), reverse=True)


def event_baseline(rollups: list[EventRollup], asset: str) -> tuple[int, int]:
    for rollup in rollups:
        if rollup.asset == asset:
            return rollup.views, rollup.conversions
    return 0, 0


def normalize_event(value: object) -> str:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if raw in {"page_view", "viewed", "views", "visited"}:
        return "view"
    if raw in {"click", "cta_click", "cta_clicked", "signup_click", "try_click"}:
        return "cta"
    if raw in {"lead", "signup", "start", "install", "conversion", "converted"}:
        return "conversion"
    return raw


def _normalize_fields(fields: list[str]) -> set[str]:
    return {field.strip().lstrip("\ufeff").lower() for field in fields}
