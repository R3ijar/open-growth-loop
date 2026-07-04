from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .config import GrowthConfig, apply_header_aliases
from .events import PRIVATE_COLUMN_HINTS, validate_event_columns
from .experiments import FIELDS as EXPERIMENT_FIELDS
from .experiments import REQUIRED_FIELDS as EXPERIMENT_REQUIRED_FIELDS
from .io_utils import first_existing, write_csv_rows
from .memory import FIELDS as ACTION_MEMORY_FIELDS

CONTENT_INVENTORY_FIELDS = ["status", "type", "asset", "primary_query", "cta", "owner_note"]
SEARCH_ROW_FIELDS = ["query", "page", "clicks", "impressions", "ctr", "position"]
EVENT_FIELDS = ["date", "asset", "event", "count"]


@dataclass(frozen=True)
class WorkspaceInitResult:
    created: list[str]
    skipped: list[str]


@dataclass(frozen=True)
class WorkspaceValidation:
    ok: bool
    checked: list[str]
    errors: list[str]
    aliases_applied: list[str]


DATA_FILES = {
    "content_inventory.csv": CONTENT_INVENTORY_FIELDS,
    "search_console_rows.csv": SEARCH_ROW_FIELDS,
    "events.csv": EVENT_FIELDS,
    "experiments.csv": EXPERIMENT_FIELDS,
    "action_memory.csv": ACTION_MEMORY_FIELDS,
}


def init_workspace(workspace: Path, overwrite: bool = False) -> WorkspaceInitResult:
    created: list[str] = []
    skipped: list[str] = []
    data_dir = workspace / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    for filename, fieldnames in DATA_FILES.items():
        path = data_dir / filename
        if path.exists() and not overwrite:
            skipped.append(str(path))
            continue
        write_csv_rows(path, fieldnames, [])
        created.append(str(path))

    return WorkspaceInitResult(created=created, skipped=skipped)


def validate_workspace(workspace: Path, config: GrowthConfig | None = None) -> WorkspaceValidation:
    data_dir = workspace / "data"
    paths = {
        "content_inventory": first_existing([data_dir / "content_inventory.csv", data_dir / "content_inventory.example.csv"]),
        "search_rows": first_existing([data_dir / "search_console_rows.csv", data_dir / "search_console_rows.example.csv"]),
        "events": first_existing([data_dir / "events.csv", data_dir / "events.example.csv"]),
        "experiments": first_existing([data_dir / "experiments.csv", data_dir / "experiments.example.csv"]),
    }
    required = {
        "content_inventory": CONTENT_INVENTORY_FIELDS,
        "search_rows": SEARCH_ROW_FIELDS,
        "events": EVENT_FIELDS,
        "experiments": EXPERIMENT_REQUIRED_FIELDS,
    }
    optional_paths = {
        "action_memory": first_existing([data_dir / "action_memory.csv", data_dir / "action_memory.example.csv"]),
    }
    optional_required = {"action_memory": ACTION_MEMORY_FIELDS}

    checked: list[str] = []
    errors: list[str] = []
    aliases_applied: list[str] = []
    for name, path in paths.items():
        if not path.exists():
            errors.append(f"{name}: missing {path}")
            continue

        checked.append(str(path))
        header = _read_header(path)
        if not header:
            errors.append(f"{name}: empty CSV or missing header at {path}")
            continue

        private = sorted({field for field in _normalize_fields(header) if field in PRIVATE_COLUMN_HINTS})
        if private:
            errors.append(f"{name}: private-looking columns are not allowed: {', '.join(private)}")

        effective_header, applied = apply_header_aliases(header, config.aliases_for(name) if config else None)
        aliases_applied.extend(f"{name}.{entry}" for entry in applied)

        missing = sorted(set(required[name]) - set(effective_header))
        if missing:
            errors.append(f"{name}: missing required columns: {', '.join(missing)}")

        if name == "events":
            try:
                validate_event_columns(effective_header)
            except ValueError as exc:
                errors.append(f"{name}: {exc}")

    for name, path in optional_paths.items():
        if not path.exists():
            continue
        checked.append(str(path))
        header = _read_header(path)
        if not header:
            errors.append(f"{name}: empty CSV or missing header at {path}")
            continue
        effective_header, applied = apply_header_aliases(header, config.aliases_for(name) if config else None)
        aliases_applied.extend(f"{name}.{entry}" for entry in applied)
        missing = sorted(set(optional_required[name]) - set(effective_header))
        if missing:
            errors.append(f"{name}: missing required columns: {', '.join(missing)}")

    return WorkspaceValidation(ok=not errors, checked=checked, errors=errors, aliases_applied=aliases_applied)


def _read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            return [field.strip().lstrip("\ufeff") for field in next(reader)]
        except StopIteration:
            return []


def _normalize_fields(fields: list[str]) -> set[str]:
    return {field.strip().lstrip("\ufeff").lower() for field in fields}
