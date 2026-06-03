from __future__ import annotations

from typing import Iterable, Sequence


def markdown_table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> list[str]:
    table_rows = [list(row) for row in rows]
    lines = [
        "| " + " | ".join(_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in table_rows:
        cells = [_cell(value) for value in row]
        if len(cells) < len(headers):
            cells.extend("" for _ in range(len(headers) - len(cells)))
        lines.append("| " + " | ".join(cells[: len(headers)]) + " |")
    return lines


def key_value_table(items: Iterable[tuple[str, object]]) -> list[str]:
    return markdown_table(["Field", "Value"], items)


def status_label(value: object) -> str:
    raw = str(value).strip().lower().replace("-", "_")
    if raw in {"true", "ok", "pass", "passed", "fresh", "sample", "ready"}:
        return "PASS"
    if raw in {"false", "warn", "warning", "warnings", "stale", "missing", "empty", "future_dated", "unknown"}:
        return "WARN"
    if raw in {"fail", "failed", "error", "errors", "blocked", "findings"}:
        return "FAIL"
    if raw in {"manual", "review", "required"}:
        return "MANUAL"
    if not raw:
        return "UNKNOWN"
    return raw.upper()


def collapsible_section(summary: str, body_lines: Sequence[str]) -> list[str]:
    body = list(body_lines)
    return [
        "<details>",
        f"<summary>{_inline(summary)}</summary>",
        "",
        *body,
        "",
        "</details>",
    ]


def bullet_list(items: Iterable[object], empty: str) -> list[str]:
    lines = [f"- {str(item).strip()}" for item in items if str(item).strip()]
    return lines or [empty]


def task_list(items: Iterable[object], empty: str) -> list[str]:
    lines = [f"- [ ] {str(item).strip()}" for item in items if str(item).strip()]
    return lines or [empty]


def compact_join(items: Iterable[object], limit: int = 3) -> str:
    values = [str(item).strip() for item in items if str(item).strip()]
    if not values:
        return "none"
    visible = values[:limit]
    suffix = "" if len(values) <= limit else f"; +{len(values) - limit} more"
    return "; ".join(visible) + suffix


def _cell(value: object) -> str:
    text = "none" if value is None or value == "" else str(value)
    text = text.strip().replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("|", "\\|").replace("\n", "<br>")
    return text


def _inline(value: object) -> str:
    return str(value).replace("<", "&lt;").replace(">", "&gt;").strip()
