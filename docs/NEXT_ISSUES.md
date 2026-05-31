# Next Issues

This is the initial public backlog for Open Growth Loop. Each item is small enough to become a focused GitHub issue.

## Add Config Support For Schema Aliases

Different maintainers export aggregate CSVs with slightly different column names. Today Open Growth Loop expects the default schema names exactly.

Acceptance criteria:

- Core defaults keep working with no config.
- Config aliases are local-only and do not require secrets.
- Validation reports which aliases were applied.
- Tests cover at least one alias per input type.

## Write Dated Report History

The CLI currently writes `latest-*` report files under `outbox/`, which is useful for daily use but not enough for comparing work over time.

Acceptance criteria:

- Existing `latest-*` paths continue to work.
- Dated reports are deterministic and easy to diff.
- Tests or smoke coverage verify the new paths.

## Add A Release Evidence Checklist

The planner can identify staged work that needs release evidence, but maintainers still need concrete checks for verifying that a docs page, example, package page, or project site update is actually public.

Acceptance criteria:

- Checklist stays generic for OSS projects.
- No hosted crawling or private credentials are required.
- The generated prompt includes the checklist when action type is `release_evidence`.

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

