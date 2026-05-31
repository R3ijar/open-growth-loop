from __future__ import annotations

from pathlib import Path

from .search import SearchOpportunity, rank_search_opportunities, read_search_rows


def build_query_backlog(search_rows_path: Path, minimum_impressions: int = 25) -> list[SearchOpportunity]:
    return rank_search_opportunities(read_search_rows(search_rows_path), minimum_impressions)


def render_query_backlog(opportunities: list[SearchOpportunity]) -> str:
    lines = ["# Query Opportunity Backlog", ""]
    if not opportunities:
        lines.append("No query opportunities met the current thresholds.")
        return "\n".join(lines) + "\n"

    for index, item in enumerate(opportunities, start=1):
        lines.extend(
            [
                f"## {index}. {item.page}",
                "",
                f"- Query: {item.query}",
                f"- Type: {item.opportunity_type}",
                f"- Impressions: {item.impressions}",
                f"- Clicks: {item.clicks}",
                f"- CTR: {item.ctr:.3f}",
                f"- Position: {item.position:.1f}",
                f"- Reason: {item.reason}",
                "",
            ]
        )
    return "\n".join(lines)
