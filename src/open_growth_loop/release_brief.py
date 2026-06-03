from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib  # type: ignore[no-redef]

from .config import GrowthConfig, load_config
from .freshness import build_freshness_report
from .io_utils import first_existing, read_json, today_iso, write_json_report, write_text_report
from .planner import build_daily_plan, default_data_paths, default_memory_path
from .privacy import scan_privacy
from .reporting import key_value_table, markdown_table, status_label
from .workspace import validate_workspace


@dataclass(frozen=True)
class ChecklistItem:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class ChangelogState:
    path: str
    release_notes_present: bool
    current_version_documented: bool
    release_note_items: list[str]
    detail: str


@dataclass(frozen=True)
class ExampleCoverage:
    name: str
    path: str
    ok: bool
    validation_ok: bool
    action_type: str
    asset: str
    selected_rule: str
    detail: str


@dataclass(frozen=True)
class ReleaseBrief:
    ready: bool
    generated_at: str
    project_name: str
    version: str
    workspace: str
    summary: dict[str, object]
    latest_plan: dict[str, object]
    changelog: ChangelogState
    examples: list[ExampleCoverage]
    checklist: list[ChecklistItem]
    warnings: list[str]


def build_release_brief(
    workspace: Path,
    config: GrowthConfig,
    include_tests: bool = False,
    generated_at: str | None = None,
) -> ReleaseBrief:
    generated_at = generated_at or today_iso()
    metadata = _project_metadata(workspace)
    inventory, search_rows, events = default_data_paths(workspace)
    data_dir = workspace / "data"
    experiments = first_existing([data_dir / "experiments.csv", data_dir / "experiments.example.csv"])

    validation = validate_workspace(workspace, config)
    freshness = build_freshness_report(
        {
            "content_inventory": inventory,
            "search_rows": search_rows,
            "events": events,
            "experiments": experiments,
        },
        config.schema_aliases,
        warn_after_days=config.thresholds.freshness_warn_days,
        today=generated_at,
    )
    privacy = scan_privacy(workspace, include_tests=include_tests)
    latest_plan = _latest_plan_summary(workspace, config)
    examples = build_example_coverage(workspace)
    changelog = inspect_changelog(workspace, str(metadata["version"]))
    readme_has_engine_coverage = "Planner Engine Coverage" in _read_text(workspace / "README.md")

    examples_ok = bool(examples) and all(example.ok for example in examples)
    checklist = [
        _check("Workspace validates", validation.ok, "All required CSV schemas validate.", "; ".join(validation.errors)),
        _check("Data freshness checked", freshness.ok, "No stale-data warnings for release inputs.", "; ".join(freshness.warnings)),
        _check("Privacy scan clean", privacy.ok, "No private-looking CSV headers, emails, or secret assignments found.", f"{len(privacy.findings)} finding(s)."),
        _check("Daily plan can be generated", bool(latest_plan.get("action_type")), f"{latest_plan.get('action_type', '')} for {latest_plan.get('asset', 'none')}", str(latest_plan.get("error", ""))),
        _check("Example workspaces validate", examples_ok, f"{len(examples)} runnable example workspace(s) validated.", "No runnable examples found or at least one example failed."),
        _check("Changelog has release notes", changelog.release_notes_present, "Changelog has notes for the pending or current release.", "Add an Unreleased or current-version changelog entry before tagging."),
        _check("README explains planner coverage", readme_has_engine_coverage, "README describes the generic planner surfaces.", "Add or update README planner coverage before applying or releasing."),
        ChecklistItem(
            name="Adoption and impact claims reviewed",
            status="manual",
            detail="Do not claim stars, downloads, users, or ecosystem impact unless those metrics are public and verified.",
        ),
    ]
    ready = not any(item.status == "fail" for item in checklist)
    warnings = [f"{item.name}: {item.detail}" for item in checklist if item.status in {"warn", "manual"}]

    return ReleaseBrief(
        ready=ready,
        generated_at=generated_at,
        project_name=str(metadata["name"]),
        version=str(metadata["version"]),
        workspace=str(workspace),
        summary={
            "validation_ok": validation.ok,
            "validation_errors": validation.errors,
            "freshness_ok": freshness.ok,
            "freshness_warnings": freshness.warnings,
            "privacy_ok": privacy.ok,
            "privacy_findings": len(privacy.findings),
            "examples_checked": len(examples),
            "examples_ok": examples_ok,
            "manual_review_required": True,
        },
        latest_plan=latest_plan,
        changelog=changelog,
        examples=examples,
        checklist=checklist,
        warnings=warnings,
    )


def build_example_coverage(workspace: Path) -> list[ExampleCoverage]:
    examples_dir = workspace / "examples"
    if not examples_dir.exists():
        return []

    examples: list[ExampleCoverage] = []
    for path in sorted(item for item in examples_dir.iterdir() if item.is_dir()):
        if not (path / "data").exists():
            continue
        examples.append(_example_coverage(path))
    return examples


def inspect_changelog(workspace: Path, version: str) -> ChangelogState:
    path = workspace / "CHANGELOG.md"
    text = _read_text(path)
    unreleased_items = _section_bullets(text, "Unreleased")
    current_version_items = _section_bullets_with_prefix(text, version)
    release_note_items = unreleased_items or current_version_items
    version_documented = f"## {version}" in text
    if unreleased_items:
        detail = "Unreleased notes are present."
    elif current_version_items:
        detail = f"Current version {version} release notes are present."
    else:
        detail = "No Unreleased or current-version bullets found."
    if version_documented:
        detail += f" Current version {version} is documented."
    else:
        detail += f" Current version {version} is not documented yet."
    return ChangelogState(
        path=str(path),
        release_notes_present=bool(release_note_items),
        current_version_documented=version_documented,
        release_note_items=release_note_items,
        detail=detail,
    )


def render_release_brief_markdown(brief: ReleaseBrief) -> str:
    lines = [
        "# Release Brief",
        "",
        "## Summary",
        "",
        *key_value_table(
            [
                ("Project", f"{brief.project_name} {brief.version}"),
                ("Generated at", brief.generated_at),
                ("Release status", "ready with manual review" if brief.ready else "blocked"),
                ("Workspace validation", status_label(brief.summary["validation_ok"])),
                ("Data freshness", status_label(brief.summary["freshness_ok"])),
                ("Privacy scan", status_label(brief.summary["privacy_ok"])),
                (
                    "Example workspaces",
                    f"{brief.summary['examples_checked']} checked, {status_label(brief.summary['examples_ok'])}",
                ),
                ("Manual review", "required before public release or application claims"),
            ]
        ),
        "",
        "## Latest Daily Plan",
        "",
        *key_value_table(
            [
                ("Action", brief.latest_plan.get("action_type") or "none"),
                ("Asset", brief.latest_plan.get("asset") or "none"),
                ("Selected rule", brief.latest_plan.get("selected_rule") or "unknown"),
                ("Confidence", brief.latest_plan.get("confidence") or "unknown"),
                ("Reason", brief.latest_plan.get("reason") or "not available"),
            ]
        ),
        "",
        "## Example Coverage",
        "",
    ]
    if not brief.examples:
        lines.append("No runnable example workspaces found.")
    else:
        lines.extend(
            markdown_table(
                ["Example", "Status", "Validation", "Action", "Asset", "Rule", "Detail"],
                [
                    (
                        example.name,
                        status_label(example.ok),
                        status_label(example.validation_ok),
                        example.action_type or "none",
                        example.asset or "none",
                        example.selected_rule or "unknown",
                        example.detail,
                    )
                    for example in brief.examples
                ],
            )
        )

    lines.extend(
        [
            "",
            "## Changelog",
            "",
            *key_value_table(
                [
                    ("Release notes", "present" if brief.changelog.release_notes_present else "missing"),
                    ("Current version documented", "yes" if brief.changelog.current_version_documented else "no"),
                    ("Detail", brief.changelog.detail),
                ]
            ),
        ]
    )
    if brief.changelog.release_note_items:
        lines.extend(["", "Release note items:"])
        lines.extend(f"- {item}" for item in brief.changelog.release_note_items)

    lines.extend(["", "## Release Checklist", ""])
    lines.extend(
        markdown_table(
            ["Check", "Status", "Detail"],
            [(item.name, status_label(item.status), item.detail) for item in brief.checklist],
        )
    )

    lines.extend(
        [
            "",
            "## Claim Guardrails",
            "",
            "- Do not claim stars, downloads, users, broad adoption, or ecosystem importance unless verified from public sources.",
            "- Say the project is early if it is early.",
            "- Describe real maintenance workflows: validation, freshness, planning, issue drafts, privacy checks, examples, and release review.",
            "- Keep private product data, private analytics, customer data, and project-specific strategy out of public examples and application text.",
            "",
        ]
    )
    return "\n".join(lines)


def write_release_brief_reports(brief: ReleaseBrief, out_dir: Path) -> tuple[Path, Path, Path, Path]:
    md_path, md_history = write_text_report(out_dir / "latest-release-brief.md", render_release_brief_markdown(brief))
    json_path, json_history = write_json_report(out_dir / "latest-release-brief.json", asdict(brief))
    return md_path, md_history, json_path, json_history


def _example_coverage(path: Path) -> ExampleCoverage:
    try:
        config = load_config(path)
        validation = validate_workspace(path, config)
        inventory, search_rows, events = default_data_paths(path)
        plan = build_daily_plan(
            inventory,
            search_rows,
            events,
            minimum_impressions=config.thresholds.minimum_impressions,
            minimum_views=config.thresholds.minimum_views,
            weak_cta_rate=config.thresholds.weak_cta_rate,
            memory_path=default_memory_path(path),
            aliases=config.schema_aliases,
            freshness_warn_days=config.thresholds.freshness_warn_days,
        )
        decision = plan.evidence.get("decision") if isinstance(plan.evidence, dict) else None
        selected_rule = str(decision.get("selected_rule", "")) if isinstance(decision, dict) else ""
        ok = validation.ok and plan.action_type != "wait_for_data"
        detail = "Validates and selects a concrete plan." if ok else "; ".join(validation.errors) or "Planner waited for more data."
        return ExampleCoverage(
            name=path.name,
            path=str(path),
            ok=ok,
            validation_ok=validation.ok,
            action_type=plan.action_type,
            asset=plan.asset,
            selected_rule=selected_rule,
            detail=detail,
        )
    except Exception as exc:  # pragma: no cover - defensive report output
        return ExampleCoverage(
            name=path.name,
            path=str(path),
            ok=False,
            validation_ok=False,
            action_type="",
            asset="",
            selected_rule="",
            detail=str(exc),
        )


def _latest_plan_summary(workspace: Path, config: GrowthConfig) -> dict[str, object]:
    plan_json = workspace / "outbox" / "plans" / "latest-plan.json"
    if plan_json.exists():
        try:
            payload = read_json(plan_json)
            if isinstance(payload, dict):
                return _plan_summary(payload)
        except (OSError, ValueError):
            pass

    try:
        inventory, search_rows, events = default_data_paths(workspace)
        plan = build_daily_plan(
            inventory,
            search_rows,
            events,
            minimum_impressions=config.thresholds.minimum_impressions,
            minimum_views=config.thresholds.minimum_views,
            weak_cta_rate=config.thresholds.weak_cta_rate,
            memory_path=default_memory_path(workspace),
            aliases=config.schema_aliases,
            freshness_warn_days=config.thresholds.freshness_warn_days,
        )
        return _plan_summary(asdict(plan))
    except Exception as exc:  # pragma: no cover - defensive report output
        return {"action_type": "", "asset": "", "selected_rule": "", "confidence": "", "reason": "", "error": str(exc)}


def _plan_summary(payload: Mapping[str, object]) -> dict[str, object]:
    evidence = payload.get("evidence")
    decision = evidence.get("decision") if isinstance(evidence, dict) else None
    selected_rule = decision.get("selected_rule", "") if isinstance(decision, dict) else ""
    return {
        "action_type": payload.get("action_type", ""),
        "asset": payload.get("asset", ""),
        "title": payload.get("title", ""),
        "reason": payload.get("reason", ""),
        "confidence": payload.get("confidence", ""),
        "selected_rule": selected_rule,
    }


def _project_metadata(workspace: Path) -> dict[str, object]:
    pyproject = workspace / "pyproject.toml"
    if not pyproject.exists():
        return {"name": workspace.name, "version": "unknown"}
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = data.get("project", {})
    if not isinstance(project, dict):
        return {"name": workspace.name, "version": "unknown"}
    return {"name": project.get("name", workspace.name), "version": project.get("version", "unknown")}


def _section_bullets(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    in_section = False
    bullets: list[str] = []
    for line in lines:
        if line.startswith("## "):
            title = line.removeprefix("## ").strip()
            if in_section and title != heading:
                break
            in_section = title == heading
            continue
        if in_section and line.strip().startswith("- "):
            bullets.append(line.strip().removeprefix("- ").strip())
    return bullets


def _section_bullets_with_prefix(text: str, heading_prefix: str) -> list[str]:
    lines = text.splitlines()
    in_section = False
    bullets: list[str] = []
    for line in lines:
        if line.startswith("## "):
            title = line.removeprefix("## ").strip()
            if in_section and not title.startswith(heading_prefix):
                break
            in_section = title.startswith(heading_prefix)
            continue
        if in_section and line.strip().startswith("- "):
            bullets.append(line.strip().removeprefix("- ").strip())
    return bullets


def _check(name: str, passed: bool, pass_detail: str, fail_detail: str) -> ChecklistItem:
    return ChecklistItem(name=name, status="pass" if passed else "fail", detail=pass_detail if passed else fail_detail)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""
