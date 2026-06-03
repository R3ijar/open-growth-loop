# Dogfooding Open Growth Loop

Open Growth Loop is maintained with the same local-first workflow it gives to other OSS projects.

The goal is not to prove adoption before adoption exists. The goal is to show a real maintainer loop: validate inputs, inspect evidence, choose one scoped action, draft a reviewable issue or prompt, check release readiness, and avoid private-data leakage before publishing.

## Current Dogfood Loop

From the repository root:

```bash
python -m open_growth_loop --workspace . validate
python -m open_growth_loop --workspace . freshness
python -m open_growth_loop --workspace . candidates
python -m open_growth_loop --workspace . plan
python -m open_growth_loop --workspace . issue-drafts
python -m open_growth_loop --workspace . release-brief
python -m open_growth_loop --workspace . report-index
python -m open_growth_loop --workspace . privacy-scan
```

This produces local reports under `outbox/`:

- candidate ranking across release evidence, funnel dropoff, search opportunities, planned assets, and action memory
- one daily plan with Decision Trace v2 and Data Freshness
- a local GitHub issue draft for review before posting
- a release brief that checks validation, freshness, privacy, changelog state, example coverage, and claim guardrails
- a report index that links generated outbox reports in a recommended reading order
- a privacy scan before public docs or examples are shared

## What We Dogfood

Open Growth Loop currently dogfoods these maintainer workflows:

- **Docs planning:** the planner chooses one scoped action instead of a broad content backlog.
- **Release evidence:** staged work is verified before being treated as shipped.
- **Example coverage:** each runnable sample workspace validates and selects the documented plan.
- **Release readiness:** `ogl release-brief` summarizes whether the repo is ready for a release or public application update.
- **Report review:** `ogl report-index` gives maintainers one local front page for the generated Markdown outputs.
- **Claim discipline:** release briefs explicitly remind maintainers not to claim stars, downloads, adoption, or ecosystem impact unless verified.
- **Privacy boundaries:** public examples use synthetic aggregate data and the privacy scan runs before sharing.

## Public-Safe Boundaries

Dogfooding does not require private analytics, customer data, raw user events, secrets, or hosted service access.

The public repo should contain:

- synthetic example CSVs
- aggregate-only event shapes
- conservative release notes
- transparent limitations
- reproducible CLI commands

The public repo should not contain:

- private product strategy
- customer or user-level data
- raw analytics payloads
- private app names or project-specific specialization
- unverified impact or adoption claims

## How Maintainers Should Use This Pattern

Use Open Growth Loop as a release and maintenance assistant, not as an autopublisher:

1. Run validation and freshness checks.
2. Inspect the candidate list and daily plan.
3. Turn the plan into a local issue draft or Codex prompt.
4. Make one focused change.
5. Record completion, shipped artifact, and later outcome.
6. Run `ogl release-brief` before tagging releases or updating public application text.

This keeps the project useful while staying honest about what has and has not been proven.
