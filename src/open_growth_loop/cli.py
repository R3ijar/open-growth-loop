from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .events import import_aggregate_events
from .experiments import render_reviews_markdown, review_experiments, track_plan
from .io_utils import ensure_parent, first_existing, read_json, write_json
from .planner import build_daily_plan, default_data_paths, write_plan_reports
from .prompts import render_codex_prompt
from .query_backlog import build_query_backlog, render_query_backlog
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
    plan.add_argument("--minimum-impressions", type=int, default=25)
    plan.add_argument("--minimum-views", type=int, default=25)

    query_backlog = subparsers.add_parser("query-backlog", help="Write ranked query opportunities.")
    add_workspace_argument(query_backlog)
    query_backlog.add_argument("--search-rows", default="", help="Search Console rows CSV.")
    query_backlog.add_argument("--minimum-impressions", type=int, default=25)

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
    track.add_argument("--review-days", type=int, default=14)
    track.add_argument("--artifact", default="")
    track.add_argument("--note", default="")

    review = subparsers.add_parser("review-experiments", help="Review experiment outcomes conservatively.")
    add_workspace_argument(review)
    review.add_argument("--ledger", default="", help="Experiment ledger CSV.")
    review.add_argument("--search-rows", default="", help="Search Console rows CSV.")
    review.add_argument("--events", default="", help="Aggregate events CSV.")
    review.add_argument("--minimum-impressions", type=int, default=25)
    review.add_argument("--minimum-views", type=int, default=25)

    prompt = subparsers.add_parser("prompt", help="Write a Codex-ready prompt from the latest plan.")
    add_workspace_argument(prompt)
    prompt.add_argument("--plan-json", default="", help="Plan JSON. Defaults to outbox/plans/latest-plan.json.")

    args = parser.parse_args()
    workspace = Path(args.workspace or args.global_workspace or ".").resolve()

    if args.command == "status":
        run_status(workspace)
    elif args.command == "init":
        run_init(args, workspace)
    elif args.command == "validate":
        run_validate(workspace)
    elif args.command == "plan":
        run_plan(args, workspace)
    elif args.command == "query-backlog":
        run_query_backlog(args, workspace)
    elif args.command == "import-events":
        count = import_aggregate_events(Path(args.source), Path(args.output))
        print(json.dumps({"rows_written": count, "output": args.output}, indent=2))
    elif args.command == "track-experiment":
        run_track_experiment(args, workspace)
    elif args.command == "review-experiments":
        run_review_experiments(args, workspace)
    elif args.command == "prompt":
        run_prompt(args, workspace)


def add_workspace_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", default="", help="Project workspace containing data/ and outbox/.")


def run_status(workspace: Path) -> None:
    inventory, search_rows, events = default_data_paths(workspace)
    ledger = first_existing([workspace / "data" / "experiments.csv", workspace / "data" / "experiments.example.csv"])
    payload = {
        "workspace": str(workspace),
        "inventory": str(inventory),
        "search_rows": str(search_rows),
        "events": str(events),
        "experiments": str(ledger),
        "latest_plan": str(workspace / "outbox" / "plans" / "latest-plan.json"),
    }
    print(json.dumps(payload, indent=2))


def run_init(args: argparse.Namespace, workspace: Path) -> None:
    result = init_workspace(workspace, overwrite=args.overwrite)
    print(json.dumps(asdict(result), indent=2))


def run_validate(workspace: Path) -> None:
    result = validate_workspace(workspace)
    print(json.dumps(asdict(result), indent=2))
    if not result.ok:
        raise SystemExit(1)


def run_plan(args: argparse.Namespace, workspace: Path) -> None:
    default_inventory, default_search_rows, default_events = default_data_paths(workspace)
    inventory = Path(args.inventory) if args.inventory else default_inventory
    search_rows = Path(args.search_rows) if args.search_rows else default_search_rows
    events = Path(args.events) if args.events else default_events
    plan = build_daily_plan(
        inventory,
        search_rows,
        events,
        minimum_impressions=args.minimum_impressions,
        minimum_views=args.minimum_views,
    )
    md_path, json_path = write_plan_reports(plan, workspace / "outbox" / "plans")
    print(json.dumps({"plan": asdict(plan), "markdown": str(md_path), "json": str(json_path)}, indent=2))


def run_query_backlog(args: argparse.Namespace, workspace: Path) -> None:
    _, default_search_rows, _ = default_data_paths(workspace)
    search_rows = Path(args.search_rows) if args.search_rows else default_search_rows
    opportunities = build_query_backlog(search_rows, args.minimum_impressions)
    out_path = workspace / "outbox" / "query-backlog.md"
    ensure_parent(out_path)
    out_path.write_text(render_query_backlog(opportunities), encoding="utf-8")
    print(json.dumps({"opportunities": len(opportunities), "markdown": str(out_path)}, indent=2))


def run_track_experiment(args: argparse.Namespace, workspace: Path) -> None:
    _, default_search_rows, default_events = default_data_paths(workspace)
    ledger = Path(args.ledger) if args.ledger else workspace / "data" / "experiments.csv"
    search_rows = Path(args.search_rows) if args.search_rows else default_search_rows
    events = Path(args.events) if args.events else default_events
    plan_json = Path(args.plan_json) if args.plan_json else workspace / "outbox" / "plans" / "latest-plan.json"
    payload = read_json(plan_json)
    from .planner import DailyPlan

    plan = DailyPlan(**payload)
    row = track_plan(plan, ledger, search_rows, events, args.review_days, args.artifact, args.note)
    print(json.dumps(row, indent=2))


def run_review_experiments(args: argparse.Namespace, workspace: Path) -> None:
    _, default_search_rows, default_events = default_data_paths(workspace)
    ledger = Path(args.ledger) if args.ledger else first_existing([workspace / "data" / "experiments.csv", workspace / "data" / "experiments.example.csv"])
    search_rows = Path(args.search_rows) if args.search_rows else default_search_rows
    events = Path(args.events) if args.events else default_events
    reviews = review_experiments(ledger, search_rows, events, args.minimum_impressions, args.minimum_views)
    out_path = workspace / "outbox" / "experiment-review.md"
    ensure_parent(out_path)
    out_path.write_text(render_reviews_markdown(reviews), encoding="utf-8")
    write_json(workspace / "outbox" / "experiment-review.json", [asdict(review) for review in reviews])
    print(json.dumps({"reviews": len(reviews), "markdown": str(out_path)}, indent=2))


def run_prompt(args: argparse.Namespace, workspace: Path) -> None:
    plan_json = Path(args.plan_json) if args.plan_json else workspace / "outbox" / "plans" / "latest-plan.json"
    from .planner import DailyPlan

    plan = DailyPlan(**read_json(plan_json))
    prompt = render_codex_prompt(plan)
    out_path = workspace / "outbox" / "prompts" / "latest-prompt.md"
    ensure_parent(out_path)
    out_path.write_text(prompt, encoding="utf-8")
    print(json.dumps({"prompt": str(out_path)}, indent=2))
