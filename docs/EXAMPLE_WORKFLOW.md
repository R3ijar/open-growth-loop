# Example Workflow

This walkthrough uses the sample CSVs in `data/` to show what Open Growth Loop does for a maintainer.

For additional runnable examples, see `examples/`:

- `examples/staged-release-check`
- `examples/funnel-dropoff`
- `examples/aliased-search-export`

## Scenario

An OSS project has:

- a getting-started page that already receives some traffic
- a staged configuration checklist that needs release verification
- planned examples for CI and local-first analytics
- aggregate event counts from the project website
- Search Console rows showing near-ranking queries

The maintainer wants one conservative next action, not a long speculative content queue.

## 1. Validate The Workspace

```bash
python -m open_growth_loop --workspace . validate
```

Expected shape:

```json
{
  "ok": true,
  "checked": [
    ".../data/content_inventory.example.csv",
    ".../data/search_console_rows.example.csv",
    ".../data/events.example.csv",
    ".../data/experiments.example.csv"
  ],
  "errors": []
}
```

Validation checks required CSV headers and rejects private-looking event columns.

## 2. Build A Query Backlog

```bash
python -m open_growth_loop --workspace . query-backlog
```

This writes:

```text
outbox/query-backlog.md
outbox/history/YYYY-MM-DD-query-backlog.md
```

The backlog ranks Search Console rows that look actionable, such as:

- pages near positions 8-20
- high-impression queries with weak CTR

It is a backlog, not a publishing command.

## 3. Generate One Daily Plan

```bash
python -m open_growth_loop --workspace . plan
```

This writes:

```text
outbox/plans/latest-plan.md
outbox/plans/latest-plan.json
outbox/plans/history/YYYY-MM-DD-plan.md
outbox/plans/history/YYYY-MM-DD-plan.json
```

With the sample data, the planner chooses the staged checklist first:

```json
{
  "action_type": "release_evidence",
  "asset": "/guides/configuration-checklist",
  "confidence": "high"
}
```

That is intentional. Staged work should be verified before starting another speculative docs asset.

## 4. Generate A Codex Prompt

```bash
python -m open_growth_loop --workspace . prompt
```

This writes:

```text
outbox/prompts/latest-prompt.md
outbox/prompts/history/YYYY-MM-DD-prompt.md
```

The prompt asks Codex or another coding assistant to make one focused, reviewable change. It includes the action, asset, reason, confidence, next steps, and evidence, while reminding the assistant not to invent adoption claims or cross privacy boundaries. For staged work, those next steps include a release-evidence checklist: verify the public URL or artifact, confirm discoverability from the expected public surface, avoid unverified adoption claims, and record the artifact before outcome review.

## 5. Track, Ship, And Review Later

After making the public change, record the baseline:

```bash
python -m open_growth_loop --workspace . track-experiment
```

After the change is public, record the artifact:

```bash
python -m open_growth_loop --workspace . ship --asset /guides/configuration-checklist --artifact https://example.org/guides/configuration-checklist
```

After enough time and aggregate data:

```bash
python -m open_growth_loop --workspace . review-experiments
```

The review separates operational state from evidence:

- planned or staged work is not treated as a win
- shipped work without an artifact is not treated as a win
- small samples are marked insufficient
- only observed click or conversion movement becomes directionally positive

## What This Avoids

Open Growth Loop is deliberately conservative. It avoids:

- uploading private analytics to a hosted service
- rewriting many docs pages from a noisy signal
- treating staged work as impact
- claiming success before enough aggregate evidence exists
