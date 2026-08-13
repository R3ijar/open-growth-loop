---
name: repo-steward
description: Audit and maintain an open-source repository through one evidence-backed action at a time. Use when Codex needs to assess repository readiness, triage maintainer work, choose the safest next issue or pull-request action, prepare a release, improve contributor onboarding, generate a maintainer handoff, or run Open Growth Loop's local `ogl steward`, `ogl audit`, and `ogl fix` workflows.
---

# Repo Steward

Produce a maintainer decision from observable repository evidence. Prefer reducing real maintainer load over adding speculative features.

## Workflow

1. Locate the repository root and read its contributor instructions completely.
2. Run `ogl steward --workspace <repo>` when the user authorized report files. For read-only diagnosis or recommendation, run `ogl steward --workspace <repo> --no-write`. From an Open Growth Loop checkout, use `python -m open_growth_loop` with the same arguments.
3. Read `outbox/steward/latest-steward.md` and inspect the files behind its evidence. Treat the report as a lead, not truth.
4. Read remote issues, pull requests, CI runs, and releases when a read-only GitHub capability is available. Do not let local hygiene checks override a blocked user or contributor.
5. Select exactly one bounded action using [references/decision-policy.md](references/decision-policy.md).
6. If the user requested implementation, make the smallest in-scope change, run the relevant checks, and report the evidence. Otherwise, present the recommendation without changing files.
7. Leave a compact handoff: evidence, chosen action, files changed, validation, remaining risk, and any approval-gated next step.

## Safe Fixes

Use `ogl fix --workspace <repo> --dry-run` to preview mechanical scaffolds. Run it without `--dry-run` only when the user asked for the change. Never overwrite an existing file to improve an audit score.

For judgment-heavy work such as README positioning, issue triage, security reports, or release decisions, inspect the underlying context and write a focused change manually.

## Boundaries

- Do not invent users, downloads, impact, vulnerabilities, or ecosystem importance.
- Do not rewrite Git history to alter attribution or improve optics.
- Preserve unrelated and user-owned working-tree changes; do not discard or rewrite them to create a cleaner maintenance slice.
- Do not push, publish, tag, merge, close, label, or comment without explicit authorization.
- Do not expose private issue data, analytics, secrets, or embargoed security details in reports.
- Prefer a truthful "remote evidence unavailable" statement over guessing.
