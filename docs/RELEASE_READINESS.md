# Release Readiness

`ogl release-brief` generates a local release-readiness report for maintainers.

It is designed for the moment before a maintainer tags a release, posts a public issue, updates an application, or asks Codex to help with release work.

## Command

```bash
python -m open_growth_loop --workspace . release-brief
```

The command writes:

```text
outbox/release-brief/latest-release-brief.md
outbox/release-brief/latest-release-brief.json
outbox/release-brief/history/YYYY-MM-DD-release-brief.md
outbox/release-brief/history/YYYY-MM-DD-release-brief.json
```

## What It Checks

The release brief summarizes:

- workspace validation status
- data freshness status
- privacy scan status
- latest daily plan
- runnable example workspace coverage
- changelog state
- README planner-coverage visibility
- manual adoption-claim review

The report can be `ready with manual review`. That means deterministic checks passed, but a maintainer still needs to review public claims before publishing.

## Current Example Output Shape

```text
# Release Brief

## Summary

| Field | Value |
| --- | --- |
| Project | open-growth-loop 0.1.5 |
| Generated at | 2026-06-03 |
| Release status | ready with manual review |
| Workspace validation | PASS |
| Data freshness | PASS |
| Privacy scan | PASS |
| Example workspaces | 5 checked, PASS |
| Manual review | required before public release or application claims |
```

The final checklist includes a manual item:

```text
| Check | Status | Detail |
| --- | --- | --- |
| Adoption and impact claims reviewed | MANUAL | Do not claim stars, downloads, users, or ecosystem impact unless those metrics are public and verified. |
```

That manual gate is intentional. Open Growth Loop should help maintainers move quickly without overstating impact.

## When To Use It

Run `ogl release-brief` before:

- tagging a release
- submitting or updating public application text
- posting generated issue drafts
- sharing sample workspaces
- asking Codex to help with release notes

If the release brief reports failures, fix those first. If it reports only the manual claim-review item, review the public wording and proceed deliberately.
