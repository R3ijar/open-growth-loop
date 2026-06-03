# Maintainer Loop

Open Growth Loop is built around a conservative daily loop.

## 1. Import Aggregate Signals

Use aggregate search rows and aggregate events only. Do not import raw user payloads.

```bash
ogl import-events --source exports/events.csv --output data/events.csv
```

## 2. Validate Inputs

```bash
ogl validate --workspace .
```

Validation should pass before the planner is trusted.

## 3. Generate One Plan

```bash
ogl query-backlog --workspace .
ogl candidates --workspace .
ogl plan --workspace .
```

The candidate report shows all ranked actions considered by the planner. The planner still chooses one action. That is intentional. Maintainers need less thrash, not a queue of speculative rewrites.

The plan includes Decision Trace v2 under `evidence.decision`. Use it to audit the selected winner, competing alternatives, why alternatives lost, threshold notes, blocked follow-ups, and action-memory adjustments before doing the work.

If the plan is `release_evidence`, verify the staged asset before creating another page or example:

- open the public URL or release artifact
- confirm it is reachable from the expected public surface
- confirm it avoids unverified adoption or impact claims
- record the artifact URL before reviewing outcomes

## 4. Track The Baseline And Completion

```bash
ogl track-experiment --workspace .
ogl complete --workspace .
```

The experiment ledger records impressions, clicks, views, and conversions before the change. Action memory records that the recommendation was actually completed, so future candidate ranking can avoid repeating finished work without an outcome.

## 5. Let Codex Help With The Change

```bash
ogl prompt --workspace .
```

Use the generated prompt with Codex to make one focused, reviewable change.

To turn the same plan into a reviewable local GitHub issue draft:

```bash
ogl issue-drafts --workspace .
```

This writes Markdown under `outbox/issues/`. Review the draft before posting publicly.

## 6. Record The Shipped Artifact

```bash
ogl ship --workspace . --asset /docs/setup --artifact https://example.org/docs/setup
```

This marks the experiment as `shipped`, records `shipped_on`, and stores the public artifact URL or path. Work without a shipped artifact is not treated as outcome evidence.

## 7. Record The Outcome

```bash
ogl outcome --workspace . --asset /docs/setup --outcome directionally_positive --confidence medium
```

Outcomes are local ranking context. They should be conservative labels from aggregate signals, maintainer review, or issue evidence. Use `insufficient_sample` when there is not enough evidence yet.

## 8. Weekly Operating Review

```bash
ogl weekly-review --workspace .
```

Use this to see staged assets, stale planned work, experiments waiting for artifact evidence, shipped experiments ready for review, and shipped experiments still waiting for data.

## 9. Scan Before Sharing

```bash
ogl privacy-scan --workspace .
```

Run this before publishing sample workspaces, docs examples, or issue attachments. It checks CSV headers for private-looking columns and scans text files for email addresses or secret-like assignments.

## 10. Review Later

```bash
ogl review-experiments --workspace .
```

Reviews separate three states:

- not publicly applied
- insufficient sample
- directionally positive or needs iteration

This keeps maintainers from rewriting docs based on tiny or stale evidence.
