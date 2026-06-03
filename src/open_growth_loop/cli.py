from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .candidates import build_candidates, render_candidates_markdown
from .config import GrowthConfig, load_config
from .doctor import build_doctor_report, write_doctor_reports
from .events import import_aggregate_events
from .experiments import render_reviews_markdown, review_experiments, ship_experiment, track_plan
from .freshness import build_freshness_report, write_freshness_reports
from .io_utils import dated_report_path, first_existing, read_json, write_json_report, write_text_report
from .issue_drafts import issue_title, write_issue_draft
from .memory import record_completion, record_outcome
from .planner import DailyPlan, build_daily_plan, default_data_paths, default_memory_path, write_plan_reports
from .privacy import render_privacy_scan_markdown, scan_privacy
from .prompts import render_codex_prompt
from .query_backlog import build_query_backlog, render_query_backlog
from .release_brief import build_release_brief, write_release_brief_reports
from .report_index import build_report_index, write_report_index
from .weekly import build_weekly_review, render_weekly_review
from .workspace import init_workspace, validate_workspace


def main() -> None:
    parser = argparse.ArgumentParser(description="Open Growth Loop CLI.")
    parser.add_argument("--workspace", dest="global_workspace", default="", help="Project workspace containing data/ and outbox/.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Show the current data file status.")
    add_workspace_argument(status)

    init = subparsers.add_parser("init", help="Create local data CSV files with the expected headers.")
    add_workspace_argument(init)
    init.add_argument("--overwrite", action="store_true", help="Rewrite existing data CSV files.")

    validate = subparsers.add_parser("validate", help="Validate local CSV inputs and privacy-safe headers.")
    add_workspace_argument(validate)

    doctor = subparsers.add_parser("doctor", help="Run one-shot workspace readiness checks.")
    add_workspace_argument(doctor)
    doctor.add_argument("--include-tests", action="store_true", help="Include tests/ directories in privacy checks.")

    freshness = subparsers.add_parser("freshness", help="Report whether local CSV inputs are fresh enough to trust.")
    add_workspace_argument(freshness)
    freshness.add_argument("--warn-after-days", type=int, default=None, help="Warn when real input data is older than this many days.")

    plan = subparsers.add_parser("plan", help="Build the next daily growth-loop plan.")
    add_workspace_argument(plan)
    plan.add_argument("--inventory", default="", help="Content inventory CSV.")
    plan.add_argument("--search-rows", default="", help="Search Console rows CSV.")
    plan.add_argument("--events", default="", help="Aggregate events CSV.")
    plan.add_argument("--minimum-impressions", type=int, default=None)
    plan.add_argument("--minimum-views", type=int, default=None)
    plan.add_argument("--weak-cta-rate", type=float, default=None)

    candidates = subparsers.add_parser("candidates", help="Write all ranked action candidates considered by the planner.")
    add_workspace_argument(candidates)
    candidates.add_argument("--inventory", default="", help="Content inventory CSV.")
    candidates.add_argument("--search-rows", default="", help="Search Console rows CSV.")
    candidates.add_argument("--events", default="", help="Aggregate events CSV.")
    candidates.add_argument("--minimum-impressions", type=int, default=None)
    candidates.add_argument("--minimum-views", type=int, default=None)
    candidates.add_argument("--weak-cta-rate", type=float, default=None)
    candidates.add_argument("--memory", default="", help="Action memory CSV.")

    complete = subparsers.add_parser("complete", help="Record that the latest plan or a manual action was completed.")
    add_workspace_argument(complete)
    complete.add_argument("--memory", default="", help="Action memory CSV.")
    complete.add_argument("--plan-json", default="", help="Plan JSON. Defaults to outbox/plans/latest-plan.json.")
    complete.add_argument("--asset", default="", help="Manual asset if not reading a plan.")
    complete.add_argument("--action-type", default="", help="Manual action type if not reading a plan.")
    complete.add_argument("--source", default="", help="Manual source if not reading a plan.")
    complete.add_argument("--artifact", default="", help="Optional public URL, release, path, or evidence.")
    complete.add_argument("--note", default="", help="Optional completion note.")

    outcome = subparsers.add_parser("outcome", help="Record the observed outcome for a completed action.")
    add_workspace_argument(outcome)
    outcome.add_argument("--memory", default="", help="Action memory CSV.")
    outcome.add_argument("--id", default="", help="Action memory record id.")
    outcome.add_argument("--asset", default="", help="Use the latest matching action for this asset.")
    outcome.add_argument("--outcome", required=True, help="Outcome such as directionally_positive, needs_iteration, or insufficient_sample.")
    outcome.add_argument("--impact", type=float, default=None, help="Optional numeric local impact score.")
    outcome.add_argument("--confidence", default="", help="Optional confidence label.")
    outcome.add_argument("--note", default="", help="Optional outcome note.")

    query_backlog = subparsers.add_parser("query-backlog", help="Write ranked query opportunities.")
    add_workspace_argument(query_backlog)
    query_backlog.add_argument("--search-rows", default="", help="Search Console rows CSV.")
    query_backlog.add_argument("--minimum-impressions", type=int, default=None)

    import_events = subparsers.add_parser("import-events", help="Import privacy-safe aggregate event rows.")
    add_workspace_argument(import_events)
    import_events.add_argument("--source", required=True, help="Source aggregate event CSV.")
    import_events.add_argument("--output", required=True, help="Output aggregate event CSV.")

    track = subparsers.add_parser("track-experiment", help="Track the latest plan as an experiment baseline.")
    add_workspace_argument(track)
    track.add_argument("--ledger", default="", help="Experiment ledger CSV.")
    track.add_argument("--search-rows", default="", help="Search Console rows CSV.")
    track.add_argument("--events", default="", help="Aggregate events CSV.")
    track.add_argument("--plan-json", default="", help="Plan JSON. Defaults to outbox/plans/latest-plan.json.")
    track.add_argument("--review-days", type=int, default=None)
    track.add_argument("--artifact", default="")
    track.add_argument("--note", default="")

    ship = subparsers.add_parser("ship", help="Mark an experiment as publicly shipped with an artifact.")
    add_workspace_argument(ship)
    ship.add_argument("--ledger", default="", help="Experiment ledger CSV.")
    ship.add_argument("--experiment-id", default="", help="Experiment id to mark shipped.")
    ship.add_argument("--asset", default="", help="Asset to mark shipped. Uses the latest matching row.")
    ship.add_argument("--artifact", required=True, help="Public URL, release, path, or other artifact evidence.")
    ship.add_argument("--note", default="", help="Optional note to store on the shipped experiment.")

    review = subparsers.add_parser("review-experiments", help="Review experiment outcomes conservatively.")
    add_workspace_argument(review)
    review.add_argument("--ledger", default="", help="Experiment ledger CSV.")
    review.add_argument("--search-rows", default="", help="Search Console rows CSV.")
    review.add_argument("--events", default="", help="Aggregate events CSV.")
    review.add_argument("--minimum-impressions", type=int, default=None)
    review.add_argument("--minimum-views", type=int, default=None)

    weekly = subparsers.add_parser("weekly-review", help="Summarize current operating state across inventory and experiments.")
    add_workspace_argument(weekly)
    weekly.add_argument("--inventory", default="", help="Content inventory CSV.")
    weekly.add_argument("--ledger", default="", help="Experiment ledger CSV.")

    privacy = subparsers.add_parser("privacy-scan", help="Scan local workspace files for private-data leakage risks.")
    add_workspace_argument(privacy)
    privacy.add_argument("--include-tests", action="store_true", help="Include tests/ directories in the scan.")

    prompt = subparsers.add_parser("prompt", help="Write a Codex-ready prompt from the latest plan.")
    add_workspace_argument(prompt)
    prompt.add_argument("--plan-json", default="", help="Plan JSON. Defaults to outbox/plans/latest-plan.json.")

    issue_drafts = subparsers.add_parser("issue-drafts", help="Write a local GitHub issue draft from the latest plan.")
    add_workspace_argument(issue_drafts)
    issue_drafts.add_argument("--plan-json", default="", help="Plan JSON. Defaults to outbox/plans/latest-plan.json.")

    release_brief = subparsers.add_parser("release-brief", help="Write a release-readiness brief for maintainers.")
    add_workspace_argument(release_brief)
    release_brief.add_argument("--include-tests", action="store_true", help="Include tests/ directories in the privacy scan.")

    report_index = subparsers.add_parser("report-index", help="Write a local index of generated outbox reports.")
    add_workspace_argument(report_index)

    demo = subparsers.add_parser("demo", help="Generate the main local reports in one reviewable demo run.")
    add_workspace_argument(demo)
    demo.add_argument("--include-tests", action="store_true", help="Include tests/ directories in privacy checks.")

    args = parser.parse_args()
    workspace = Path(args.workspace or args.global_workspace or ".").resolve()
    try:
        config = load_config(workspace)
    except ValueError as exc:
        parser.error(str(exc))

    if args.command == "status":
        run_status(workspace, config)
    elif args.command == "init":
        run_init(args, workspace)
    elif args.command == "validate":
        run_validate(workspace, config)
    elif args.command == "doctor":
        run_doctor(args, workspace, config)
    elif args.command == "freshness":
        run_freshness(args, workspace, config)
    elif args.command == "plan":
        run_plan(args, workspace, config)
    elif args.command == "candidates":
        run_candidates(args, workspace, config)
    elif args.command == "complete":
        run_complete(args, workspace, config)
    elif args.command == "outcome":
        run_outcome(args, workspace, config)
    elif args.command == "query-backlog":
        run_query_backlog(args, workspace, config)
    elif args.command == "import-events":
        count = import_aggregate_events(Path(args.source), Path(args.output), config.aliases_for("events"))
        print(json.dumps({"rows_written": count, "output": args.output}, indent=2))
    elif args.command == "track-experiment":
        run_track_experiment(args, workspace, config)
    elif args.command == "ship":
        run_ship(args, workspace, config)
    elif args.command == "review-experiments":
        run_review_experiments(args, workspace, config)
    elif args.command == "weekly-review":
        run_weekly_review(args, workspace, config)
    elif args.command == "privacy-scan":
        run_privacy_scan(args, workspace)
    elif args.command == "prompt":
        run_prompt(args, workspace)
    elif args.command == "issue-drafts":
        run_issue_drafts(args, workspace)
    elif args.command == "release-brief":
        run_release_brief(args, workspace, config)
    elif args.command == "report-index":
        run_report_index(workspace)
    elif args.command == "demo":
        run_demo(args, workspace, config)


def add_workspace_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", default="", help="Project workspace containing data/ and outbox/.")


def run_status(workspace: Path, config: GrowthConfig) -> None:
    inventory, search_rows, events = default_data_paths(workspace)
    ledger = first_existing([workspace / "data" / "experiments.csv", workspace / "data" / "experiments.example.csv"])
    payload = {
        "workspace": str(workspace),
        "inventory": str(inventory),
        "search_rows": str(search_rows),
        "events": str(events),
        "experiments": str(ledger),
        "action_memory": str(default_memory_path(workspace)),
        "config": str(config.path) if config.path else "",
        "thresholds": asdict(config.thresholds),
        "latest_plan": str(workspace / "outbox" / "plans" / "latest-plan.json"),
    }
    print(json.dumps(payload, indent=2))


def run_init(args: argparse.Namespace, workspace: Path) -> None:
    result = init_workspace(workspace, overwrite=args.overwrite)
    print(json.dumps(asdict(result), indent=2))


def run_validate(workspace: Path, config: GrowthConfig) -> None:
    result = validate_workspace(workspace, config)
    print(json.dumps(asdict(result), indent=2))
    if not result.ok:
        raise SystemExit(1)


def run_doctor(args: argparse.Namespace, workspace: Path, config: GrowthConfig) -> None:
    report = build_doctor_report(workspace, config, include_tests=args.include_tests)
    md_path, md_history, json_path, json_history = write_doctor_reports(report, workspace / "outbox" / "doctor")
    print(
        json.dumps(
            {
                "ok": report.ok,
                "checks": [asdict(check) for check in report.checks],
                "next_steps": report.next_steps,
                "markdown": str(md_path),
                "markdown_history": str(md_history),
                "json": str(json_path),
                "json_history": str(json_history),
            },
            indent=2,
        )
    )
    if not report.ok:
        raise SystemExit(1)


def run_freshness(args: argparse.Namespace, workspace: Path, config: GrowthConfig) -> None:
    inventory, search_rows, events = default_data_paths(workspace)
    data_dir = workspace / "data"
    paths = {
        "content_inventory": inventory,
        "search_rows": search_rows,
        "events": events,
        "experiments": first_existing([data_dir / "experiments.csv", data_dir / "experiments.example.csv"]),
    }
    warn_after_days = args.warn_after_days if args.warn_after_days is not None else config.thresholds.freshness_warn_days
    report = build_freshness_report(paths, config.schema_aliases, warn_after_days=warn_after_days)
    md_path, md_history, json_path, json_history = write_freshness_reports(report, workspace / "outbox" / "freshness")
    print(
        json.dumps(
            {
                "ok": report.ok,
                "warnings": len(report.warnings),
                "markdown": str(md_path),
                "markdown_history": str(md_history),
                "json": str(json_path),
                "json_history": str(json_history),
            },
            indent=2,
        )
    )


def run_plan(args: argparse.Namespace, workspace: Path, config: GrowthConfig) -> None:
    default_inventory, default_search_rows, default_events = default_data_paths(workspace)
    inventory = Path(args.inventory) if args.inventory else default_inventory
    search_rows = Path(args.search_rows) if args.search_rows else default_search_rows
    events = Path(args.events) if args.events else default_events
    minimum_impressions = args.minimum_impressions if args.minimum_impressions is not None else config.thresholds.minimum_impressions
    minimum_views = args.minimum_views if args.minimum_views is not None else config.thresholds.minimum_views
    weak_cta_rate = args.weak_cta_rate if args.weak_cta_rate is not None else config.thresholds.weak_cta_rate
    plan = build_daily_plan(
        inventory,
        search_rows,
        events,
        minimum_impressions=minimum_impressions,
        minimum_views=minimum_views,
        weak_cta_rate=weak_cta_rate,
        memory_path=default_memory_path(workspace),
        aliases=config.schema_aliases,
        freshness_warn_days=config.thresholds.freshness_warn_days,
    )
    md_path, json_path = write_plan_reports(plan, workspace / "outbox" / "plans")
    print(
        json.dumps(
            {
                "plan": asdict(plan),
                "markdown": str(md_path),
                "json": str(json_path),
                "markdown_history": str(dated_report_path(md_path)),
                "json_history": str(dated_report_path(json_path)),
            },
            indent=2,
        )
    )


def run_candidates(args: argparse.Namespace, workspace: Path, config: GrowthConfig) -> None:
    default_inventory, default_search_rows, default_events = default_data_paths(workspace)
    inventory = Path(args.inventory) if args.inventory else default_inventory
    search_rows = Path(args.search_rows) if args.search_rows else default_search_rows
    events = Path(args.events) if args.events else default_events
    minimum_impressions = args.minimum_impressions if args.minimum_impressions is not None else config.thresholds.minimum_impressions
    minimum_views = args.minimum_views if args.minimum_views is not None else config.thresholds.minimum_views
    weak_cta_rate = args.weak_cta_rate if args.weak_cta_rate is not None else config.thresholds.weak_cta_rate
    candidates = build_candidates(
        inventory,
        search_rows,
        events,
        minimum_impressions=minimum_impressions,
        minimum_views=minimum_views,
        weak_cta_rate=weak_cta_rate,
        memory_path=Path(args.memory) if args.memory else default_memory_path(workspace),
        aliases=config.schema_aliases,
    )
    md_path = workspace / "outbox" / "candidates" / "latest-candidates.md"
    json_path = workspace / "outbox" / "candidates" / "latest-candidates.json"
    latest_md, history_md = write_text_report(md_path, render_candidates_markdown(candidates))
    latest_json, history_json = write_json_report(json_path, [asdict(candidate) for candidate in candidates])
    print(
        json.dumps(
            {
                "candidates": len(candidates),
                "markdown": str(latest_md),
                "markdown_history": str(history_md),
                "json": str(latest_json),
                "json_history": str(history_json),
            },
            indent=2,
        )
    )


def run_complete(args: argparse.Namespace, workspace: Path, config: GrowthConfig) -> None:
    memory = Path(args.memory) if args.memory else default_memory_path(workspace)
    asset = args.asset.strip()
    action_type = args.action_type.strip()
    source = args.source.strip()
    note = args.note.strip()
    if not asset and not action_type:
        plan_json = Path(args.plan_json) if args.plan_json else workspace / "outbox" / "plans" / "latest-plan.json"
        payload = read_json(plan_json)
        plan = DailyPlan(**payload)
        asset = plan.asset
        action_type = plan.action_type
        decision = plan.evidence.get("decision") if isinstance(plan.evidence, dict) else None
        source = source or (str(decision.get("selected_rule", "")) if isinstance(decision, dict) else "")
        note = note or plan.title
    row = record_completion(
        memory,
        asset=asset,
        action_type=action_type,
        source=source,
        artifact=args.artifact,
        note=note,
        aliases=config.aliases_for("action_memory"),
    )
    print(json.dumps(row, indent=2))


def run_outcome(args: argparse.Namespace, workspace: Path, config: GrowthConfig) -> None:
    memory = Path(args.memory) if args.memory else default_memory_path(workspace)
    try:
        row = record_outcome(
            memory,
            outcome=args.outcome,
            record_id=args.id,
            asset=args.asset,
            impact=args.impact,
            confidence=args.confidence,
            note=args.note,
            aliases=config.aliases_for("action_memory"),
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(row, indent=2))


def run_query_backlog(args: argparse.Namespace, workspace: Path, config: GrowthConfig) -> None:
    _, default_search_rows, _ = default_data_paths(workspace)
    search_rows = Path(args.search_rows) if args.search_rows else default_search_rows
    minimum_impressions = args.minimum_impressions if args.minimum_impressions is not None else config.thresholds.minimum_impressions
    opportunities = build_query_backlog(search_rows, minimum_impressions, config.aliases_for("search_rows"))
    out_path = workspace / "outbox" / "query-backlog.md"
    latest_path, history_path = write_text_report(out_path, render_query_backlog(opportunities))
    print(json.dumps({"opportunities": len(opportunities), "markdown": str(latest_path), "markdown_history": str(history_path)}, indent=2))


def run_track_experiment(args: argparse.Namespace, workspace: Path, config: GrowthConfig) -> None:
    _, default_search_rows, default_events = default_data_paths(workspace)
    ledger = Path(args.ledger) if args.ledger else workspace / "data" / "experiments.csv"
    search_rows = Path(args.search_rows) if args.search_rows else default_search_rows
    events = Path(args.events) if args.events else default_events
    plan_json = Path(args.plan_json) if args.plan_json else workspace / "outbox" / "plans" / "latest-plan.json"
    payload = read_json(plan_json)
    from .planner import DailyPlan

    plan = DailyPlan(**payload)
    review_days = args.review_days if args.review_days is not None else config.thresholds.review_days
    row = track_plan(plan, ledger, search_rows, events, review_days, args.artifact, args.note, config.schema_aliases)
    print(json.dumps(row, indent=2))


def run_ship(args: argparse.Namespace, workspace: Path, config: GrowthConfig) -> None:
    ledger = Path(args.ledger) if args.ledger else workspace / "data" / "experiments.csv"
    try:
        row = ship_experiment(
            ledger,
            artifact=args.artifact,
            experiment_id=args.experiment_id,
            asset=args.asset,
            note=args.note,
            aliases=config.schema_aliases,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(row, indent=2))


def run_review_experiments(args: argparse.Namespace, workspace: Path, config: GrowthConfig) -> None:
    _, default_search_rows, default_events = default_data_paths(workspace)
    ledger = Path(args.ledger) if args.ledger else first_existing([workspace / "data" / "experiments.csv", workspace / "data" / "experiments.example.csv"])
    search_rows = Path(args.search_rows) if args.search_rows else default_search_rows
    events = Path(args.events) if args.events else default_events
    minimum_impressions = args.minimum_impressions if args.minimum_impressions is not None else config.thresholds.minimum_impressions
    minimum_views = args.minimum_views if args.minimum_views is not None else config.thresholds.minimum_views
    reviews = review_experiments(ledger, search_rows, events, minimum_impressions, minimum_views, config.schema_aliases)
    out_path = workspace / "outbox" / "experiment-review.md"
    latest_path, history_path = write_text_report(out_path, render_reviews_markdown(reviews))
    json_path, json_history_path = write_json_report(workspace / "outbox" / "experiment-review.json", [asdict(review) for review in reviews])
    print(
        json.dumps(
            {
                "reviews": len(reviews),
                "markdown": str(latest_path),
                "markdown_history": str(history_path),
                "json": str(json_path),
                "json_history": str(json_history_path),
            },
            indent=2,
        )
    )


def run_weekly_review(args: argparse.Namespace, workspace: Path, config: GrowthConfig) -> None:
    default_inventory, _, _ = default_data_paths(workspace)
    inventory = Path(args.inventory) if args.inventory else default_inventory
    ledger = Path(args.ledger) if args.ledger else first_existing([workspace / "data" / "experiments.csv", workspace / "data" / "experiments.example.csv"])
    review = build_weekly_review(
        inventory,
        ledger,
        config.schema_aliases,
        stale_planned_days=config.thresholds.stale_planned_days,
        stale_shipped_days=config.thresholds.stale_shipped_days,
    )
    out_path = workspace / "outbox" / "weekly-review.md"
    latest_path, history_path = write_text_report(out_path, render_weekly_review(review))
    json_path, json_history_path = write_json_report(workspace / "outbox" / "weekly-review.json", asdict(review))
    print(
        json.dumps(
            {
                "markdown": str(latest_path),
                "markdown_history": str(history_path),
                "json": str(json_path),
                "json_history": str(json_history_path),
                "ready_for_review": len(review.ready_for_review),
                "waiting_for_artifact": len(review.waiting_for_artifact),
                "stale_work": len(review.stale_work),
            },
            indent=2,
        )
    )


def run_privacy_scan(args: argparse.Namespace, workspace: Path) -> None:
    result = scan_privacy(workspace, include_tests=args.include_tests)
    out_path = workspace / "outbox" / "privacy-scan.md"
    latest_path, history_path = write_text_report(out_path, render_privacy_scan_markdown(result))
    json_path, json_history_path = write_json_report(workspace / "outbox" / "privacy-scan.json", asdict(result))
    print(
        json.dumps(
            {
                "ok": result.ok,
                "checked_files": result.checked_files,
                "findings": len(result.findings),
                "markdown": str(latest_path),
                "markdown_history": str(history_path),
                "json": str(json_path),
                "json_history": str(json_history_path),
            },
            indent=2,
        )
    )
    if not result.ok:
        raise SystemExit(1)


def run_prompt(args: argparse.Namespace, workspace: Path) -> None:
    plan_json = Path(args.plan_json) if args.plan_json else workspace / "outbox" / "plans" / "latest-plan.json"
    from .planner import DailyPlan

    plan = DailyPlan(**read_json(plan_json))
    prompt = render_codex_prompt(plan)
    out_path = workspace / "outbox" / "prompts" / "latest-prompt.md"
    latest_path, history_path = write_text_report(out_path, prompt)
    print(json.dumps({"prompt": str(latest_path), "prompt_history": str(history_path)}, indent=2))


def run_issue_drafts(args: argparse.Namespace, workspace: Path) -> None:
    plan_json = Path(args.plan_json) if args.plan_json else workspace / "outbox" / "plans" / "latest-plan.json"
    if not plan_json.exists():
        raise SystemExit(f"Plan JSON not found: {plan_json}. Run `ogl plan --workspace {workspace}` first.")
    plan = DailyPlan(**read_json(plan_json))
    latest_path, history_path = write_issue_draft(plan, workspace / "outbox" / "issues")
    print(
        json.dumps(
            {
                "title": issue_title(plan),
                "issue_draft": str(latest_path),
                "issue_draft_history": str(history_path),
            },
            indent=2,
        )
    )


def run_release_brief(args: argparse.Namespace, workspace: Path, config: GrowthConfig) -> None:
    brief = build_release_brief(workspace, config, include_tests=args.include_tests)
    md_path, md_history, json_path, json_history = write_release_brief_reports(brief, workspace / "outbox" / "release-brief")
    print(
        json.dumps(
            {
                "ready": brief.ready,
                "warnings": len(brief.warnings),
                "markdown": str(md_path),
                "markdown_history": str(md_history),
                "json": str(json_path),
                "json_history": str(json_history),
            },
            indent=2,
        )
    )


def run_report_index(workspace: Path) -> None:
    index = build_report_index(workspace)
    latest_path, history_path = write_report_index(index, workspace / "outbox")
    print(
        json.dumps(
            {
                "reports": len(index.reports),
                "available": index.available_count,
                "index": str(latest_path),
                "index_history": str(history_path),
            },
            indent=2,
        )
    )


def run_demo(args: argparse.Namespace, workspace: Path, config: GrowthConfig) -> None:
    print(json.dumps(generate_demo_reports(workspace, config, include_tests=args.include_tests), indent=2))


def generate_demo_reports(workspace: Path, config: GrowthConfig, include_tests: bool = False) -> dict[str, object]:
    inventory, search_rows, events = default_data_paths(workspace)
    data_dir = workspace / "data"
    ledger = first_existing([data_dir / "experiments.csv", data_dir / "experiments.example.csv"])
    memory = default_memory_path(workspace)

    validation = validate_workspace(workspace, config)

    freshness = build_freshness_report(
        {
            "content_inventory": inventory,
            "search_rows": search_rows,
            "events": events,
            "experiments": ledger,
        },
        config.schema_aliases,
        warn_after_days=config.thresholds.freshness_warn_days,
    )
    freshness_md, _, freshness_json, _ = write_freshness_reports(freshness, workspace / "outbox" / "freshness")

    candidates = build_candidates(
        inventory,
        search_rows,
        events,
        minimum_impressions=config.thresholds.minimum_impressions,
        minimum_views=config.thresholds.minimum_views,
        weak_cta_rate=config.thresholds.weak_cta_rate,
        memory_path=memory,
        aliases=config.schema_aliases,
    )
    candidates_md, _ = write_text_report(workspace / "outbox" / "candidates" / "latest-candidates.md", render_candidates_markdown(candidates))
    candidates_json, _ = write_json_report(workspace / "outbox" / "candidates" / "latest-candidates.json", [asdict(candidate) for candidate in candidates])

    opportunities = build_query_backlog(search_rows, config.thresholds.minimum_impressions, config.aliases_for("search_rows"))
    query_backlog_md, _ = write_text_report(workspace / "outbox" / "query-backlog.md", render_query_backlog(opportunities))

    plan = build_daily_plan(
        inventory,
        search_rows,
        events,
        minimum_impressions=config.thresholds.minimum_impressions,
        minimum_views=config.thresholds.minimum_views,
        weak_cta_rate=config.thresholds.weak_cta_rate,
        memory_path=memory,
        aliases=config.schema_aliases,
        freshness_warn_days=config.thresholds.freshness_warn_days,
    )
    plan_md, plan_json = write_plan_reports(plan, workspace / "outbox" / "plans")

    prompt_md, _ = write_text_report(workspace / "outbox" / "prompts" / "latest-prompt.md", render_codex_prompt(plan))
    issue_md, _ = write_issue_draft(plan, workspace / "outbox" / "issues")

    reviews = review_experiments(
        ledger,
        search_rows,
        events,
        config.thresholds.minimum_impressions,
        config.thresholds.minimum_views,
        config.schema_aliases,
    )
    experiment_review_md, _ = write_text_report(workspace / "outbox" / "experiment-review.md", render_reviews_markdown(reviews))
    experiment_review_json, _ = write_json_report(workspace / "outbox" / "experiment-review.json", [asdict(review) for review in reviews])

    weekly = build_weekly_review(
        inventory,
        ledger,
        config.schema_aliases,
        stale_planned_days=config.thresholds.stale_planned_days,
        stale_shipped_days=config.thresholds.stale_shipped_days,
    )
    weekly_md, _ = write_text_report(workspace / "outbox" / "weekly-review.md", render_weekly_review(weekly))
    weekly_json, _ = write_json_report(workspace / "outbox" / "weekly-review.json", asdict(weekly))

    privacy = scan_privacy(workspace, include_tests=include_tests)
    privacy_md, _ = write_text_report(workspace / "outbox" / "privacy-scan.md", render_privacy_scan_markdown(privacy))
    privacy_json, _ = write_json_report(workspace / "outbox" / "privacy-scan.json", asdict(privacy))

    release = build_release_brief(workspace, config, include_tests=include_tests)
    release_md, _, release_json, _ = write_release_brief_reports(release, workspace / "outbox" / "release-brief")

    report_index = build_report_index(workspace)
    index_md, _ = write_report_index(report_index, workspace / "outbox")

    return {
        "validation_ok": validation.ok,
        "validation_errors": validation.errors,
        "privacy_ok": privacy.ok,
        "privacy_findings": len(privacy.findings),
        "release_ready": release.ready,
        "release_warnings": len(release.warnings),
        "candidates": len(candidates),
        "opportunities": len(opportunities),
        "experiment_reviews": len(reviews),
        "report_index_available": report_index.available_count,
        "reports": {
            "freshness": str(freshness_md),
            "freshness_json": str(freshness_json),
            "candidates": str(candidates_md),
            "candidates_json": str(candidates_json),
            "query_backlog": str(query_backlog_md),
            "plan": str(plan_md),
            "plan_json": str(plan_json),
            "prompt": str(prompt_md),
            "issue_draft": str(issue_md),
            "experiment_review": str(experiment_review_md),
            "experiment_review_json": str(experiment_review_json),
            "weekly_review": str(weekly_md),
            "weekly_review_json": str(weekly_json),
            "privacy_scan": str(privacy_md),
            "privacy_scan_json": str(privacy_json),
            "release_brief": str(release_md),
            "release_brief_json": str(release_json),
            "report_index": str(index_md),
        },
    }
