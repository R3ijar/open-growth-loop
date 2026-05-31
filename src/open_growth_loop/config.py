from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib


SCHEMA_NAMES = {"content_inventory", "search_rows", "events", "experiments"}
SchemaAliases = Mapping[str, Mapping[str, str]]


@dataclass(frozen=True)
class GrowthConfig:
    path: Path | None
    schema_aliases: dict[str, dict[str, str]]

    def aliases_for(self, schema_name: str) -> dict[str, str]:
        return dict(self.schema_aliases.get(schema_name, {}))


def load_config(workspace: Path, config_path: Path | None = None) -> GrowthConfig:
    path = config_path or workspace / "open-growth-loop.toml"
    if not path.exists():
        return GrowthConfig(path=None, schema_aliases={})

    payload = tomllib.loads(path.read_text(encoding="utf-8-sig"))

    raw_aliases = payload.get("schema_aliases", {})
    if not isinstance(raw_aliases, dict):
        raise ValueError("schema_aliases must be a table in open-growth-loop.toml")

    aliases: dict[str, dict[str, str]] = {}
    for schema_name, raw_mapping in raw_aliases.items():
        if schema_name not in SCHEMA_NAMES:
            raise ValueError(f"unknown schema alias section: {schema_name}")
        if not isinstance(raw_mapping, dict):
            raise ValueError(f"schema_aliases.{schema_name} must be a table")
        aliases[schema_name] = _normalize_alias_mapping(raw_mapping, schema_name)

    return GrowthConfig(path=path, schema_aliases=aliases)


def apply_column_aliases(row: Mapping[str, str], aliases: Mapping[str, str] | None) -> dict[str, str]:
    if not aliases:
        return dict(row)

    normalized_aliases = _normalize_alias_mapping(aliases, "row")
    output: dict[str, str] = {}
    for field, value in row.items():
        output_field = normalized_aliases.get(_normalize_field(field), _clean_field(field))
        if output_field not in output or output[output_field] == "":
            output[output_field] = value
    return output


def apply_header_aliases(header: list[str], aliases: Mapping[str, str] | None) -> tuple[list[str], list[str]]:
    if not aliases:
        return header, []

    normalized_aliases = _normalize_alias_mapping(aliases, "header")
    applied: list[str] = []
    effective: list[str] = []
    for field in header:
        normalized = _normalize_field(field)
        target = normalized_aliases.get(normalized)
        if target:
            applied.append(f"{normalized} -> {target}")
            effective.append(target)
        else:
            effective.append(field.strip())
    return effective, applied


def _normalize_alias_mapping(raw_mapping: Mapping[str, object], section: str) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for source, target in raw_mapping.items():
        if not isinstance(target, str):
            raise ValueError(f"schema_aliases.{section}.{source} must map to a string field name")
        aliases[_normalize_field(source)] = _normalize_field(target)
    return aliases


def _normalize_field(value: object) -> str:
    return _clean_field(value).lower()


def _clean_field(value: object) -> str:
    return str(value or "").strip().lstrip("\ufeff")
