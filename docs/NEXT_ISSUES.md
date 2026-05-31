# Next Issues

This is the initial public backlog for Open Growth Loop. Each open item is small enough to become a focused GitHub issue.

## Add More Sample Workspaces

The bundled sample data shows one docs workflow, but maintainers may understand the tool faster with more concrete examples.

Acceptance criteria:

- Samples use only aggregate fake data.
- Each sample includes a short README and expected command sequence.
- No private product names, customer data, or raw analytics are included.

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
