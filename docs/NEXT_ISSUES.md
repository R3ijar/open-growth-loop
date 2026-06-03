# Next Issues

This is the initial public backlog for Open Growth Loop. Each open item is small enough to become a focused GitHub issue.

## Add Optional GitHub Issue Creation

Maintainers may eventually want reviewed drafts to become GitHub issues, but the core should not require GitHub auth.

Acceptance criteria:

- Default behavior remains file-only.
- Any GitHub API integration is optional and never sends private analytics.
- Issue creation is explicit and can be disabled in local policy.

## Completed Recently

### Add A Release Evidence Checklist

Implemented in the planner, generated prompt, docs, and tests.

### Write Dated Report History

Implemented for plans, prompts, query backlogs, and experiment reviews while preserving existing `latest-*` paths.

### Add Config Support For Schema Aliases

Implemented local `open-growth-loop.toml` schema aliases for CSV readers and validation.

### Add More Sample Workspaces

Implemented runnable fake workspaces for release evidence, funnel dropoff, and aliased search exports.

### Add Shipped Artifact Tracking

Implemented `ogl ship` so tracked experiments can move from planned/staged state to shipped evidence before review.

### Add Configurable Thresholds And Plan Explanations

Implemented local threshold settings and decision traces in generated plans.

### Add Weekly Operating Review

Implemented `ogl weekly-review` for inventory and experiment state.

### Add Local Privacy Scan

Implemented `ogl privacy-scan` for private-looking CSV headers and secret-like text.

### Add Stale Work Detection

Implemented stale planned/shipped work detection in `ogl weekly-review` with configurable stale windows.

### Add Unified Candidate Engine

Implemented shared action candidates and `ogl candidates` so the planner can select one action while exposing alternatives.

### Add Outcome Memory Loop

Implemented `ogl complete`, `ogl outcome`, and local action-memory ranking adjustments so completed work can influence future candidates without sending data to a hosted service.

### Add Local Issue Draft Export

Implemented `ogl issue-drafts` so the latest daily plan can become a reviewable Markdown GitHub issue draft without requiring GitHub auth or posting anything automatically.

### Add Decision Trace V2

Implemented richer plan traces with selected winner metadata, ranked alternatives, losing reasons, threshold notes, blocked follow-ups, and local action-memory notes.
