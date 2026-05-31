from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .config import GrowthConfig, load_config
from .events import import_aggregate_events
from .experiments import render_reviews_markdown, review_experiments, ship_experiment, track_plan
from .io_utils import dated_report_path, first_existing, read_json, write_json_report, write_text_report
from .planner import build_daily_plan, default_data_paths, write_plan_reports
from .privacy import render_privacy_scan_markdown, scan_privacy
from .prompts import render_codex_prompt
from .query_backlog import build_query_backlog, render_query_backlog
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

    plan = subparsers.add_parser("plan", help="Build the next daily growth-loop plan.")
    add_workspace_argument(plan)
    plan.add_argument("--inventory", default="", help="Content inventory CSV.")
    plan.add_argument("--search-rows", default="", help="Search Console rows CSV.")
    plan.add_argument("--events", default="", help="Aggregate events CSV.")
    plan.add_argument("--minimum-impressions", type=int, default=None)
    plan.add_argument("--minimum-views", type=int, default=None)
    plan.add_argument("--weak-cta-rate", type=float, default=None)

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
    elif args.command == "plan":
        run_plan(args, workspace, config)
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
        aliases=config.schema_aliases,
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
