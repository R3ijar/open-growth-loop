from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .io_utils import read_csv_rows


@dataclass(frozen=True)
class ContentItem:
    status: str
    type: str
    asset: str
    primary_query: str
    cta: str
    owner_note: str


def read_inventory(path: Path) -> list[ContentItem]:
    items: list[ContentItem] = []
    for row in read_csv_rows(path):
        items.append(
            ContentItem(
                status=row.get("status", "").strip().lower(),
                type=row.get("type", "").strip(),
                asset=row.get("asset", "").strip(),
                primary_query=row.get("primary_query", "").strip(),
                cta=row.get("cta", "").strip(),
                owner_note=row.get("owner_note", "").strip(),
            )
        )
    return items


def staged_items(items: list[ContentItem]) -> list[ContentItem]:
    return [item for item in items if item.status == "staged"]


def next_planned_item(items: list[ContentItem]) -> ContentItem | None:
    for item in items:
        if item.status == "planned":
            return item
    return None


def find_item(items: list[ContentItem], asset: str) -> ContentItem | None:
    for item in items:
        if item.asset == asset:
            return item
    return None
