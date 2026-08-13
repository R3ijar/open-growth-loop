# Next Issues

This is the initial public backlog for Open Growth Loop. Each open item is small enough to become a focused GitHub issue.

## Completed in v0.2.0

The read-only GitHub evidence adapter is now available through `ogl steward --github owner/repo`. Local-only behavior remains the default; remote failures are explicit; selected items retain their source URLs; and the adapter issues only bounded `gh` read commands.

## Add Maintainer Brief Fixtures

Create small synthetic repositories that exercise dirty-worktree, release-backlog, repository-gap, and remote-review decisions.

Acceptance criteria:

- Each fixture documents the expected selected action and why alternatives lose.
- Tests run without network access or global Git configuration.
- Reports contain no personal names, emails, or unverifiable adoption claims.

## Field-Test the Repo Steward Skill

Collect public feedback from independent maintainers using the workflow in `docs/ADOPTION.md`.

Acceptance criteria:

- Each recorded adopter links to a public repository or public feedback issue.
- Feedback that changes a decision rule ships with a regression test.
- Targets remain clearly labeled as targets until the evidence exists.

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

### Add Data Freshness V1

Implemented `ogl freshness` and embedded plan freshness checks so real local CSV inputs can warn when they are stale, empty, missing, future-dated, or still sample data.

### Add Package Page And Release Note Sample Data Shapes

Implemented runnable synthetic examples for a package-page CTA dropoff and release-note search opportunity, with documented expected `ogl plan` outputs.

### Add One-Command Demo Report Generation

Implemented `ogl demo` so maintainers and reviewers can generate the main local report set in one command.
