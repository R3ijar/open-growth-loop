from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib


SCHEMA_NAMES = {"content_inventory", "search_rows", "events", "experiments", "action_memory"}
SchemaAliases = Mapping[str, Mapping[str, str]]

AUDIT_PURPOSES = {"standard", "example", "template", "monorepo"}
AUDIT_CHECK_IDS = {
    "readme",
    "license",
    "install",
    "quickstart",
    "docs",
    "examples",
    "contributing",
    "code_of_conduct",
    "security_policy",
    "issue_templates",
    "pr_template",
    "changelog",
    "ci",
    "release_tags",
}
AUDIT_DISPOSITIONS = {"qualify", "skip"}
ESSENTIAL_AUDIT_CHECK_IDS = {"readme", "license"}


@dataclass(frozen=True)
class AuditDisposition:
    disposition: str
    reason: str


@dataclass(frozen=True)
class AuditProfile:
    purpose: str
    checks: dict[str, AuditDisposition]


@dataclass(frozen=True)
class GrowthThresholds:
    minimum_impressions: int = 25
    minimum_views: int = 25
    weak_cta_rate: float = 0.05
    review_days: int = 14
    stale_planned_days: int = 14
    stale_shipped_days: int = 21
    freshness_warn_days: int = 21


@dataclass(frozen=True)
class GrowthConfig:
    path: Path | None
    schema_aliases: dict[str, dict[str, str]]
    thresholds: GrowthThresholds = GrowthThresholds()
    audit_profile: AuditProfile | None = None

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

    thresholds = _load_thresholds(payload.get("thresholds", {}))
    audit_profile = _load_audit_profile(payload.get("audit_profile"))
    return GrowthConfig(path=path, schema_aliases=aliases, thresholds=thresholds, audit_profile=audit_profile)


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


def _load_thresholds(raw_thresholds: object) -> GrowthThresholds:
    if raw_thresholds in ({}, None):
        return GrowthThresholds()
    if not isinstance(raw_thresholds, dict):
        raise ValueError("thresholds must be a table in open-growth-loop.toml")

    allowed = {
        "minimum_impressions",
        "minimum_views",
        "weak_cta_rate",
        "review_days",
        "stale_planned_days",
        "stale_shipped_days",
        "freshness_warn_days",
    }
    unknown = sorted(set(raw_thresholds) - allowed)
    if unknown:
        raise ValueError(f"unknown threshold setting: {', '.join(unknown)}")

    thresholds = GrowthThresholds()
    minimum_impressions = _positive_int(raw_thresholds.get("minimum_impressions", thresholds.minimum_impressions), "minimum_impressions")
    minimum_views = _positive_int(raw_thresholds.get("minimum_views", thresholds.minimum_views), "minimum_views")
    weak_cta_rate = _rate(raw_thresholds.get("weak_cta_rate", thresholds.weak_cta_rate), "weak_cta_rate")
    review_days = _positive_int(raw_thresholds.get("review_days", thresholds.review_days), "review_days")
    stale_planned_days = _positive_int(raw_thresholds.get("stale_planned_days", thresholds.stale_planned_days), "stale_planned_days")
    stale_shipped_days = _positive_int(raw_thresholds.get("stale_shipped_days", thresholds.stale_shipped_days), "stale_shipped_days")
    freshness_warn_days = _positive_int(raw_thresholds.get("freshness_warn_days", thresholds.freshness_warn_days), "freshness_warn_days")
    return GrowthThresholds(
        minimum_impressions=minimum_impressions,
        minimum_views=minimum_views,
        weak_cta_rate=weak_cta_rate,
        review_days=review_days,
        stale_planned_days=stale_planned_days,
        stale_shipped_days=stale_shipped_days,
        freshness_warn_days=freshness_warn_days,
    )


def _load_audit_profile(raw_profile: object) -> AuditProfile | None:
    if raw_profile is None:
        return None
    if not isinstance(raw_profile, dict):
        raise ValueError("audit_profile must be a table in open-growth-loop.toml")

    unknown = sorted(set(raw_profile) - {"purpose", "checks"})
    if unknown:
        raise ValueError(f"unknown audit_profile setting: {', '.join(unknown)}")

    purpose = str(raw_profile.get("purpose") or "").strip().lower()
    if purpose not in AUDIT_PURPOSES:
        allowed = ", ".join(sorted(AUDIT_PURPOSES))
        raise ValueError(f"audit_profile.purpose must be one of: {allowed}")

    raw_checks = raw_profile.get("checks", {})
    if not isinstance(raw_checks, dict):
        raise ValueError("audit_profile.checks must be a table")

    checks: dict[str, AuditDisposition] = {}
    for raw_check_id, raw_disposition in raw_checks.items():
        check_id = str(raw_check_id).strip().lower()
        if check_id not in AUDIT_CHECK_IDS:
            raise ValueError(f"unknown audit check in audit_profile.checks: {check_id}")
        if check_id in ESSENTIAL_AUDIT_CHECK_IDS:
            raise ValueError(f"audit_profile.checks.{check_id} cannot override an essential open-source check")
        if not isinstance(raw_disposition, dict):
            raise ValueError(f"audit_profile.checks.{check_id} must be a table")

        unknown_fields = sorted(set(raw_disposition) - {"disposition", "reason"})
        if unknown_fields:
            raise ValueError(f"unknown audit_profile.checks.{check_id} setting: {', '.join(unknown_fields)}")

        disposition = str(raw_disposition.get("disposition") or "").strip().lower()
        if disposition not in AUDIT_DISPOSITIONS:
            allowed = ", ".join(sorted(AUDIT_DISPOSITIONS))
            raise ValueError(f"audit_profile.checks.{check_id}.disposition must be one of: {allowed}")
        reason = str(raw_disposition.get("reason") or "").strip()
        if not reason:
            raise ValueError(f"audit_profile.checks.{check_id}.reason must explain the repository-specific context")
        if len(reason) > 300:
            raise ValueError(f"audit_profile.checks.{check_id}.reason must be 300 characters or fewer")
        checks[check_id] = AuditDisposition(disposition=disposition, reason=reason)

    return AuditProfile(purpose=purpose, checks=checks)


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"thresholds.{name} must be a positive integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"thresholds.{name} must be a positive integer") from exc
    if parsed <= 0:
        raise ValueError(f"thresholds.{name} must be a positive integer")
    return parsed


def _rate(value: object, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"thresholds.{name} must be a number between 0 and 1")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"thresholds.{name} must be a number between 0 and 1") from exc
    if parsed <= 0 or parsed >= 1:
        raise ValueError(f"thresholds.{name} must be a number between 0 and 1")
    return parsed


def _normalize_field(value: object) -> str:
    return _clean_field(value).lower()


def _clean_field(value: object) -> str:
    return str(value or "").strip().lstrip("\ufeff")
