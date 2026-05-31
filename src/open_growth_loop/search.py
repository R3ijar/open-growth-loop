from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .io_utils import parse_float, parse_int, read_csv_rows


@dataclass(frozen=True)
class SearchRow:
    query: str
    page: str
    clicks: int
    impressions: int
    ctr: float
    position: float


@dataclass(frozen=True)
class SearchOpportunity:
    page: str
    query: str
    opportunity_type: str
    score: float
    reason: str
    impressions: int
    clicks: int
    ctr: float
    position: float


def read_search_rows(path: Path) -> list[SearchRow]:
    rows: list[SearchRow] = []
    for row in read_csv_rows(path):
        rows.append(
            SearchRow(
                query=row.get("query", "").strip(),
                page=row.get("page", "").strip(),
                clicks=parse_int(row.get("clicks")),
                impressions=parse_int(row.get("impressions")),
                ctr=_normalize_ctr(row.get("ctr")),
                position=parse_float(row.get("position")),
            )
        )
    return rows


def rank_search_opportunities(rows: list[SearchRow], minimum_impressions: int = 25) -> list[SearchOpportunity]:
    opportunities: list[SearchOpportunity] = []
    for row in rows:
        if row.impressions < minimum_impressions or not row.page:
            continue

        if 8 <= row.position <= 20:
            score = row.impressions * (21 - row.position) / 20
            opportunities.append(
                SearchOpportunity(
                    page=row.page,
                    query=row.query,
                    opportunity_type="striking_distance",
                    score=score,
                    reason="Page is close enough to improve with clearer title, internal links, or examples.",
                    impressions=row.impressions,
                    clicks=row.clicks,
                    ctr=row.ctr,
                    position=row.position,
                )
            )
            continue

        if row.impressions >= minimum_impressions * 3 and row.ctr < 0.02:
            score = row.impressions * (0.02 - row.ctr + 0.01)
            opportunities.append(
                SearchOpportunity(
                    page=row.page,
                    query=row.query,
                    opportunity_type="low_ctr",
                    score=score,
                    reason="Query has impressions but weak clicks; snippet and promise may be unclear.",
                    impressions=row.impressions,
                    clicks=row.clicks,
                    ctr=row.ctr,
                    position=row.position,
                )
            )

    return sorted(opportunities, key=lambda item: item.score, reverse=True)


def search_baseline(rows: list[SearchRow], asset: str) -> tuple[int, int]:
    impressions = 0
    clicks = 0
    for row in rows:
        if row.page == asset:
            impressions += row.impressions
            clicks += row.clicks
    return impressions, clicks


def _normalize_ctr(value: object) -> float:
    parsed = parse_float(value)
    if parsed > 1:
        return parsed / 100
    return parsed
