# Next Issues

This is the initial public backlog for Open Growth Loop. Each open item is small enough to become a focused GitHub issue.

## Add Optional GitHub Issue Export

Maintainers may want to turn daily plans or backlog entries into GitHub issues, but the core should not require GitHub auth.

Acceptance criteria:

- Default behavior remains file-only.
- Exported issue drafts are reviewable Markdown.
- Any future GitHub API integration is optional and never sends private analytics.

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
