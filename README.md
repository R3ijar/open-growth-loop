# Open Growth Loop

Open Growth Loop is a local-first command line tool for maintainers who want a repeatable growth, docs, and content learning loop without sending private project data to a hosted service.

It turns simple CSV exports into a daily action plan:

- Search Console rows: queries, pages, impressions, clicks, CTR, and position.
- First-party aggregate events: date, asset, event, and count.
- Content inventory: planned, staged, and published docs, guides, examples, and landing pages.
- Experiment ledger: what was changed, when it shipped, and when it should be reviewed.

The tool is intentionally generic. It does not know about any one product, private app, customer database, or specialized domain. It is useful for open-source projects that maintain docs, examples, changelogs, educational pages, package pages, or project websites and want to decide what to improve next from public/search signals and privacy-safe event aggregates.

## What It Does

- `ogl init` creates the local `data/` files for a project.
- `ogl validate` checks that CSV inputs are complete and privacy-safe.
- `ogl query-backlog` ranks Search Console rows into maintenance opportunities.
- `ogl plan` chooses one daily action using conservative rules.
- `ogl track-experiment` records the action baseline.
- `ogl review-experiments` avoids premature winner/loser claims from tiny samples.
- `ogl prompt` writes a Codex-ready prompt for the next focused change.

In practice, the tool reads local CSVs and writes reviewable Markdown/JSON files under `outbox/`:

- a ranked query backlog
- one daily action plan
- an experiment review
- a focused prompt for Codex or another coding assistant

Each report keeps the familiar `latest-*` path for daily use and also writes a dated copy under `history/` so maintainers can compare decisions over time.

It does not publish changes, call hosted analytics APIs, or send your project data anywhere.

## Why This Exists

Small maintainers often know they should improve docs, examples, release notes, onboarding pages, or project websites, but the work gets scattered:

- Search queries live in one export.
- Website events live somewhere else.
- Content ideas sit in notes.
- Release status is remembered in chat.
- Experiments get changed before they have enough data.

Open Growth Loop creates one boring, reviewable loop:

1. Import only aggregate data.
2. Pick one daily action.
3. Track the action as an experiment.
4. Wait for enough evidence.
5. Review outcome without rewriting everything from noise.

## Privacy Boundary

Open Growth Loop is designed around aggregate inputs. The event importer accepts only:

```text
date,asset,event,count
```

It rejects private-looking columns such as email, user, session, ip, payload, token, key, secret, sku, or file. This keeps the public tool reusable while project-specific private data stays in your own repo or analytics system.

## Install

From a local checkout:

```bash
python -m venv .venv
.\.venv\Scripts\python -m pip install -e .
```

On macOS/Linux, use:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

## Quickstart

Initialize data files in a project:

```bash
ogl init --workspace .
```

Validate the local workspace:

```bash
ogl validate --workspace .
```

Run the sample planner:

```bash
ogl plan --workspace .
```

Write a query backlog:

```bash
ogl query-backlog --workspace .
```

Import aggregate events:

```bash
ogl import-events --source data/events.example.csv --output outbox/events.imported.csv
```

Track the latest daily plan as an experiment:

```bash
ogl track-experiment --workspace .
```

Review experiments after enough data has accumulated:

```bash
ogl review-experiments --workspace .
```

Generate a Codex-ready maintenance prompt from the latest plan:

```bash
ogl prompt --workspace .
```

Run tests:

```bash
python -m unittest discover -s tests
```

## Data Files

The default files live under `data/`:

- `content_inventory.example.csv`
- `search_console_rows.example.csv`
- `events.example.csv`
- `experiments.example.csv`

For real use, copy them without `.example`:

```bash
copy data\content_inventory.example.csv data\content_inventory.csv
copy data\search_console_rows.example.csv data\search_console_rows.csv
copy data\events.example.csv data\events.csv
copy data\experiments.example.csv data\experiments.csv
```

If your aggregate exports use different column names, add local schema aliases in `open-growth-loop.toml`:

```toml
[schema_aliases.search_rows]
search_term = "query"
url = "page"
shown = "impressions"
rank = "position"

[schema_aliases.events]
day = "date"
path = "asset"
kind = "event"
total = "count"
```

Aliases only rename local CSV headers into the expected schema. They do not add credentials, call hosted APIs, or relax private-column validation.

## Daily Loop

Recommended maintainer workflow:

```bash
ogl import-events --source path\to\aggregate-events.csv --output data\events.csv
ogl query-backlog --workspace .
ogl plan --workspace .
ogl track-experiment --workspace .
```

Then give `outbox/prompts/latest-prompt.md` or the plan output to Codex and work on one concrete change.

For a full walkthrough using the bundled sample CSVs, see [docs/EXAMPLE_WORKFLOW.md](docs/EXAMPLE_WORKFLOW.md).
For the initial public backlog, see [docs/NEXT_ISSUES.md](docs/NEXT_ISSUES.md).

## Decision Rules

The planner prioritizes:

1. Staged work that needs public release evidence.
2. Funnel dropoffs with enough aggregate views.
3. Search opportunities with impressions and near-ranking positions.
4. Planned content/docs assets from the inventory.
5. Waiting for more data.

These rules are deliberately conservative. The tool should reduce thrash, not create a content treadmill.

## Project Status

This is an early open-source extraction of a local growth-operations loop. It is ready for small CSV-driven workflows and intended to grow through issues, examples, and maintainer feedback.

## License

Apache-2.0.
