from __future__ import annotations

import csv
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv_rows(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: object) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def dated_report_path(latest_path: Path, report_date: str | None = None) -> Path:
    filename = latest_path.name
    if filename.startswith("latest-"):
        filename = filename.removeprefix("latest-")
    return latest_path.parent / "history" / f"{report_date or today_iso()}-{filename}"


def write_text_report(latest_path: Path, content: str, report_date: str | None = None) -> tuple[Path, Path]:
    history_path = dated_report_path(latest_path, report_date)
    ensure_parent(latest_path)
    ensure_parent(history_path)
    latest_path.write_text(content, encoding="utf-8")
    history_path.write_text(content, encoding="utf-8")
    return latest_path, history_path


def write_json_report(latest_path: Path, payload: object, report_date: str | None = None) -> tuple[Path, Path]:
    history_path = dated_report_path(latest_path, report_date)
    content = json.dumps(payload, indent=2, sort_keys=True)
    ensure_parent(latest_path)
    ensure_parent(history_path)
    latest_path.write_text(content, encoding="utf-8")
    history_path.write_text(content, encoding="utf-8")
    return latest_path, history_path


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(str(value).strip().replace("%", ""))
    except ValueError:
        return default


def parse_int(value: object, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(str(value).strip()))
    except ValueError:
        return default


def today_iso() -> str:
    return date.today().isoformat()


def future_iso(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


def first_existing(paths: list[Path]) -> Path:
    for path in paths:
        if path.exists():
            return path
    return paths[-1]
