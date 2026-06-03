# Report Gallery

Open Growth Loop writes local Markdown and JSON reports under `outbox/`. This gallery shows the shape of the Markdown outputs using the bundled synthetic sample data.

The examples below are intentionally generic. They do not use private analytics, customer data, hosted-service credentials, or product-specific strategy.

## Reader Path

For a normal maintainer run, review reports in this order:

| Step | Report | Why it matters |
| --- | --- | --- |
| 1 | Data Freshness | Confirm local CSV inputs are recent enough to trust. |
| 2 | Candidates | See every action the engine considered before selecting one. |
| 3 | Daily Plan | Take one conservative action with an auditable decision trace. |
| 4 | Issue Draft or Prompt | Turn the plan into reviewable maintainer work. |
| 5 | Release Brief | Check validation, examples, privacy, changelog, and public-claim guardrails. |
| 6 | Report Index | Keep a local front page for the generated outbox reports. |

## Report Index

`ogl report-index` creates a local front page for generated reports.

```markdown
# Open Growth Loop Report Index

## Summary

| Field | Value |
| --- | --- |
| Workspace | open-growth-loop |
| Reports available | 10 |
| Reports missing | 0 |

## Report Map

| Report | Status | Updated | Link | What to review |
| --- | --- | --- | --- | --- |
| Plan | PASS | 2026-06-03T02:14:34 | [plans/latest-plan.md](plans/latest-plan.md) | The selected daily maintainer action and decision trace. |
| Candidates | PASS | 2026-06-03T02:14:34 | [candidates/latest-candidates.md](candidates/latest-candidates.md) | All ranked actions considered by the conservative engine. |
| Release Brief | PASS | 2026-06-03T02:14:46 | [release-brief/latest-release-brief.md](release-brief/latest-release-brief.md) | Release-readiness checks and public claim guardrails. |
```

Why this exists: maintainers usually generate several reports at once. The index gives them one place to start without publishing anything.

## Daily Plan

`ogl plan` selects one action and explains why it won.

```markdown
# Daily Growth Loop Plan

## Summary

| Field | Value |
| --- | --- |
| Recommended action | release_evidence |
| Asset | /guides/configuration-checklist |
| Confidence | high |
| Selected rule | release_evidence |
| Data freshness | PASS |

## Recommended Action

**Verify staged release for /guides/configuration-checklist**

Staged work should be proven public before creating another asset.
```

The plan includes an action checklist, data freshness table, and collapsible raw JSON evidence for audit.

## Candidate Ranking

`ogl candidates` shows what the engine considered before the final plan.

```markdown
# Growth Loop Candidates

## Ranking

| Rank | Action | Asset | Rule | Confidence | Priority | Score | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | release_evidence | /guides/configuration-checklist | release_evidence | high | 10 | 1000.000 | available |
| 2 | fix_funnel | /guides/configuration-checklist | fix_funnel | medium | 20 | 89.000 | available |
| 3 | search_striking_distance | /guides/local-first-analytics | search_opportunity | medium | 30 | 89.600 | available |
```

Why this exists: the selected action should be reviewable. A maintainer can see if a stronger release-evidence or outcome-memory rule intentionally outranked a higher raw score.

## Data Freshness

`ogl freshness` prevents stale exports from silently driving recommendations.

```markdown
# Data Freshness

## Summary

| Field | Value |
| --- | --- |
| Status | PASS |
| Warning window | 21 days |
| Inputs checked | 4 |
| Warnings | 0 |

## Input Checks

| Input | Status | Source | Latest | Age | Reason |
| --- | --- | --- | --- | --- | --- |
| content_inventory | PASS | sample_file | n/a | n/a | Sample data is bundled for demos; freshness is evaluated after copying to real data files. |
```

Sample `.example.csv` files are marked as sample data. Real local CSVs are checked by latest date or file modification time.

## GitHub Issue Draft

`ogl issue-drafts` turns the latest plan into a local issue draft without creating anything on GitHub.

```markdown
# GitHub Issue Draft

Generated locally by Open Growth Loop. Review before posting publicly.

## Recommended Title

Verify staged release for /guides/configuration-checklist

## Draft Snapshot

| Field | Value |
| --- | --- |
| Action | release_evidence |
| Asset | /guides/configuration-checklist |
| Confidence | high |
| Review state | local draft only |
```

Why this exists: maintainers can inspect and edit public wording before posting. The draft includes guardrails against private data and unverified impact claims.

## Release Brief

`ogl release-brief` checks whether the workspace is ready for a public release or application update.

```markdown
# Release Brief

## Summary

| Field | Value |
| --- | --- |
| Project | open-growth-loop 0.1.5 |
| Release status | ready with manual review |
| Workspace validation | PASS |
| Data freshness | PASS |
| Privacy scan | PASS |
| Example workspaces | 5 checked, PASS |
| Manual review | required before public release or application claims |

## Release Checklist

| Check | Status | Detail |
| --- | --- | --- |
| Workspace validates | PASS | All required CSV schemas validate. |
| Privacy scan clean | PASS | No private-looking CSV headers, emails, or secret assignments found. |
| Adoption and impact claims reviewed | MANUAL | Do not claim stars, downloads, users, or ecosystem impact unless those metrics are public and verified. |
```

The manual review line is deliberate. Open Growth Loop should help maintainers move faster without overstating adoption or impact.

## Weekly Review

`ogl weekly-review` summarizes operating state across inventory and experiments.

```markdown
# Weekly Growth Loop Review

## Summary

| Field | Value |
| --- | --- |
| Staged assets | 1 |
| Waiting for artifact | 0 |
| Ready for review | 0 |
| Waiting for more data | 0 |
| Stale work | 0 |
```

Why this exists: growth and docs work often gets stuck between planned, staged, shipped, and reviewed. The weekly review makes those states visible without treating unshipped work as outcome evidence.

## Privacy And Claim Boundaries

Generated reports are designed for review, not automatic publishing.

- Reports use aggregate and inventory-level fields only.
- The privacy scan checks for private-looking CSV headers, emails, and secret-like assignments.
- Release briefs explicitly require manual review before public adoption or impact claims.
- `outbox/` is ignored by default so local generated reports do not get committed accidentally.

For the full command walkthrough, see [EXAMPLE_WORKFLOW.md](EXAMPLE_WORKFLOW.md).
