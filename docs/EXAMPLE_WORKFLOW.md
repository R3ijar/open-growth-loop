# Example Workflow

This walkthrough uses the sample CSVs in `data/` to show what Open Growth Loop does for a maintainer.

For additional runnable examples, see `examples/`:

- `examples/staged-release-check`
- `examples/funnel-dropoff`
- `examples/aliased-search-export`
- `examples/package-page-cta`
- `examples/release-notes-search`

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
python -m open_growth_loop --workspace . freshness
```

Expected shape:

```json
{
  "ok": true,
  "checked": [
    ".../data/content_inventory.example.csv",
    ".../data/search_console_rows.example.csv",
    ".../data/events.example.csv",
    ".../data/experiments.example.csv",
    ".../data/action_memory.example.csv"
  ],
  "errors": []
}
```

Validation checks required CSV headers and rejects private-looking event columns. Freshness reports whether real local CSV inputs are recent enough to trust. The bundled `.example.csv` files are marked as sample data instead of stale real evidence.

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

Inspect all ranked candidates first:

```bash
python -m open_growth_loop --workspace . candidates
```

This writes:

```text
outbox/candidates/latest-candidates.md
outbox/candidates/latest-candidates.json
outbox/candidates/history/YYYY-MM-DD-candidates.md
outbox/candidates/history/YYYY-MM-DD-candidates.json
```

Then generate the single selected plan:

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

The generated plan also includes Decision Trace v2 and Data Freshness. In Markdown, this appears as a candidate comparison and a freshness section. In JSON, `evidence.decision.winner` records the selected action, `evidence.decision.comparison` records ranked alternatives, and `evidence.freshness` records stale-data warnings.

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

## 5. Draft A GitHub Issue Locally

```bash
python -m open_growth_loop --workspace . issue-drafts
```

This writes:

```text
outbox/issues/latest-issue-draft.md
outbox/issues/history/YYYY-MM-DD-issue-draft.md
```

The issue draft turns the latest plan into a public-facing GitHub issue shape: title, context, proposed work, acceptance criteria, summarized evidence, and review notes. It is file-only by default. Review it before posting so project-private details stay out of public issues.

## 6. Check Release Readiness

```bash
python -m open_growth_loop --workspace . release-brief
```

This writes:

```text
outbox/release-brief/latest-release-brief.md
outbox/release-brief/latest-release-brief.json
outbox/release-brief/history/YYYY-MM-DD-release-brief.md
outbox/release-brief/history/YYYY-MM-DD-release-brief.json
```

The release brief summarizes validation, freshness, privacy scan status, latest plan, example coverage, changelog state, README planner coverage, and manual claim guardrails. It is useful before tagging releases, posting issue drafts, or updating public application text.

## 7. Build The Local Report Index

```bash
python -m open_growth_loop --workspace . report-index
```

This writes:

```text
outbox/index.md
outbox/history/YYYY-MM-DD-index.md
```

The index links the generated plan, candidates, freshness report, query backlog, issue draft, prompt, release brief, weekly review, experiment review, and privacy scan when those files exist. It gives maintainers one local front page for reviewing the loop output.

## 8. Track, Ship, And Review Later

After making the public change, record the baseline:

```bash
python -m open_growth_loop --workspace . track-experiment
```

Record that the recommended action was actually completed:

```bash
python -m open_growth_loop --workspace . complete
```

After the change is public, record the artifact:

```bash
python -m open_growth_loop --workspace . ship --asset /guides/configuration-checklist --artifact https://example.org/guides/configuration-checklist
```

After enough time and aggregate signal, record the outcome in local action memory:

```bash
python -m open_growth_loop --workspace . outcome --asset /guides/configuration-checklist --outcome insufficient_sample
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

Action memory then feeds future candidate ranking. Completed actions without outcomes produce a `record_outcome` candidate, exact measured repeats are cooled down, and action types with positive outcomes receive a small local boost for similar future work.

## What This Avoids

Open Growth Loop is deliberately conservative. It avoids:

- uploading private analytics to a hosted service
- rewriting many docs pages from a noisy signal
- treating staged work as impact
- claiming success before enough aggregate evidence exists
