from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .reporting import key_value_table, markdown_table
from .search import SearchOpportunity, rank_search_opportunities, read_search_rows


def build_query_backlog(search_rows_path: Path, minimum_impressions: int = 25, aliases: Mapping[str, str] | None = None) -> list[SearchOpportunity]:
    return rank_search_opportunities(read_search_rows(search_rows_path, aliases), minimum_impressions)


def render_query_backlog(opportunities: list[SearchOpportunity]) -> str:
    lines = ["# Query Opportunity Backlog", ""]
    if not opportunities:
        lines.append("No query opportunities met the current thresholds.")
        return "\n".join(lines) + "\n"

    top = opportunities[0]
    lines.extend(
        [
            "## Summary",
            "",
            *key_value_table(
                [
                    ("Opportunities reviewed", len(opportunities)),
                    ("Top page", top.page),
                    ("Top query", top.query),
                    ("Top opportunity type", top.opportunity_type),
                ]
            ),
            "",
            "## Ranked Opportunities",
            "",
            *markdown_table(
                ["Rank", "Page", "Query", "Type", "Impressions", "Clicks", "CTR", "Position", "Reason"],
                [
                    (
                        index,
                        item.page,
                        item.query,
                        item.opportunity_type,
                        item.impressions,
                        item.clicks,
                        f"{item.ctr:.3f}",
                        f"{item.position:.1f}",
                        item.reason,
                    )
                    for index, item in enumerate(opportunities, start=1)
                ],
            ),
            "",
            "## Review Notes",
            "",
            "Use this backlog to inspect query/page fit before editing titles, intros, examples, or internal links.",
            "",
        ]
    )

    for index, item in enumerate(opportunities, start=1):
        lines.extend(
            [
                f"### {index}. {item.page}",
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
