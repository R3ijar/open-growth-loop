# Applying To Codex For Open Source

Notes for applying to OpenAI's [Codex for Open Source](https://openai.com/form/codex-for-oss/) program. Kept in the repository so the application stays consistent with this project's claim guardrails: nothing below should ever say more than what is publicly verifiable.

## What the program selects for

The program supports maintainers of **widely used public projects** or projects that play **an important role in the ecosystem**. Selected maintainers receive six months of ChatGPT Pro with Codex, conditional Codex Security access, and API credits for projects using Codex in pull request review, maintainer automation, or release workflows.

Two implications:

1. **Adoption is the main signal.** Code quality alone does not qualify a project. Build real usage before or while applying, and expect that a first application from a small project may not be selected.
2. **Codex-in-the-workflow is a concrete fit.** Projects that use Codex for maintainer automation are explicitly what the API credits are for.

## How this project fits, truthfully

- Open Growth Loop is **maintainer tooling for the OSS ecosystem**: the audit and the planner exist to help other maintainers ship better docs, examples, and releases.
- The workflow is **built around Codex**: `ogl plan` and `ogl audit` end in a Codex-ready prompt, `ogl prompt` renders it, and `docs/DOGFOODING.md` documents using that loop to maintain this repository. API credits would go directly into that loop: Codex executing the audited, planned, single-action maintenance tasks the tool generates.
- The project is **early**. Say so. Do not claim stars, downloads, users, or ecosystem importance unless the number is public and verifiable at application time (`ogl release-brief` includes this guardrail for a reason).

## Before applying: make adoption possible

The v0.2.0 changes removed the biggest friction (no more CSV setup before first value). What remains is distribution work only a maintainer can do:

1. **Tag and publish v0.2.0.** Push the tag, let the release workflow publish to PyPI (one-time trusted-publisher setup in `docs/RELEASING.md`), and publish the GitHub Action to the Marketplace from the release page.
2. **Use it in public.** Run the audit action in this repository (already wired) and in any other repositories you maintain, so real job summaries exist to point at.
3. **Announce it once, well.** A Show HN / r/opensource / dev.to post works better when it leads with the zero-config action ("add one workflow file, get a scored maintainer audit") than with the CSV loop.
4. **Leave the door open.** Keep `docs/NEXT_ISSUES.md` issues labeled `good first issue` so arriving visitors can become contributors.
5. **Wait for real numbers, then apply** with whatever is verifiable: Marketplace installs, PyPI downloads, repositories running the action, contributors. Small but real beats large but claimed.

## Application draft points

- One-sentence description: "Open Growth Loop is a local-first CLI and GitHub Action that audits an open-source repository's maintainer readiness and turns local usage signals into one conservative, Codex-ready maintenance action per day."
- How the project uses Codex: every plan and audit ends in a generated, single-action Codex prompt; the repository dogfoods this loop for its own maintenance (`docs/DOGFOODING.md`).
- What API credits would be used for: running Codex on the generated maintenance actions (docs fixes, release evidence, changelog updates) across this and adopting repositories, and building the planned GitHub issue creation from reviewed drafts (`ROADMAP.md` 0.3).
- Scope honesty: state current adoption numbers exactly as they are on the day of application.
