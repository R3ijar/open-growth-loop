# Open Growth Loop

**One evidence-backed maintainer action, without another noisy bot.**

[![CI](https://github.com/R3ijar/open-growth-loop/actions/workflows/ci.yml/badge.svg)](https://github.com/R3ijar/open-growth-loop/actions/workflows/ci.yml)
[![Repository Audit](https://github.com/R3ijar/open-growth-loop/actions/workflows/audit.yml/badge.svg)](https://github.com/R3ijar/open-growth-loop/actions/workflows/audit.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](pyproject.toml)
[![GitHub Release](https://img.shields.io/github/v/release/R3ijar/open-growth-loop)](https://github.com/R3ijar/open-growth-loop/releases/latest)

Open Growth Loop answers one question for maintainers: **what deserves attention next, and what evidence supports it?**

Point it at any repository and it combines repository hygiene with local Git state into one maintainer brief. It can preview safe scaffolds for mechanical gaps, hand judgment-heavy work to an agent, and defer to real issue or pull-request demand when the local repository already looks healthy. Everything runs on your machine: no accounts, no API keys, and no project data ever leaves it.

![Open Growth Loop maintainer workflow](docs/assets/open-growth-loop-system-v013.svg)

## Quickstart

```bash
pip install git+https://github.com/R3ijar/open-growth-loop
ogl audit --workspace path/to/your-repo
ogl steward --workspace path/to/your-repo
ogl steward --workspace path/to/your-repo --no-write  # read-only JSON decision
```

Thirty seconds later, `outbox/audit/latest-audit.md` holds a scorecard over 14 hygiene checks — README quality, license, install and quickstart onboarding, docs, examples, community files, changelog, CI, and release-tag cadence:

| Check | Category | Status | Detail |
| --- | --- | --- | --- |
| README | essentials | PASS | README is present with enough content to evaluate the project. |
| License | essentials | PASS | A license file is present. |
| Quickstart | onboarding | WARN | README has no usage section with a copy-pasteable example. |
| Continuous integration | automation | WARN | No CI configuration was found; contributors cannot see whether tests pass. |
| Release tags | release | PASS | Latest tag is v1.3.0. |

*...plus nine more checks, and then the part that matters:*

| Field | Value |
| --- | --- |
| Action | Add a Quickstart section with one runnable example and its expected output. |
| Why now | README has no usage section with a copy-pasteable example. |
| Confidence | medium |

Every audit recommends exactly **one next action**, ordered by how much each gap hurts a new visitor, with a step checklist and a Codex-ready prompt — so the next focused change is one paste away. Reports stay local; add `outbox/` to your `.gitignore` if you don't want to keep them.

And when the gap is mechanical, you don't even have to write the file:

```bash
ogl fix --workspace path/to/your-repo                 # scaffold the recommended action
ogl fix --workspace path/to/your-repo --license mit   # licenses need an explicit choice
```

`ogl fix` scaffolds missing community files, changelogs, licenses, issue/PR templates, and an ecosystem-detected starter CI workflow — with TODO markers, never overwriting anything. Checks that need real judgment (README content, docs, quickstart) hand you the Codex prompt instead. A bare repository typically goes from 0% to ~70% with fixes alone; the rest is writing worth doing yourself.

## Use It With Codex

The repository includes an installable [`repo-steward` skill](skills/repo-steward/SKILL.md). It tells Codex to begin with local evidence, check live maintainer demand when available, choose exactly one bounded action, and keep pushes, releases, merges, comments, and other remote mutations behind explicit approval.

Invoke it with a request such as:

```text
Use $repo-steward to inspect this repository and complete the safest evidence-backed maintainer action.
```

The skill uses `ogl steward` as its local evidence packet; the CLI remains useful without an agent.

## Maintainer Field Test

Open Growth Loop needs counterexamples more than endorsements. If you maintain a public repository, run `ogl steward --no-write` and tell us where its selected action was wrong. The [20-minute field test](docs/ADOPTION.md) has a structured feedback form and does not require a call or ongoing commitment.

## Use It As A GitHub Action

Add one workflow file and the audit runs on every push, straight into the Actions job summary:

```yaml
name: Repository Audit
on:
  push:
    branches: [main]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: R3ijar/open-growth-loop@main
```

The action exposes `ok` and `score-percent` outputs and an optional `strict` gate that fails the job when README or LICENSE is missing. Full reference: [docs/GITHUB_ACTION.md](docs/GITHUB_ACTION.md). This repository [runs it on itself](.github/workflows/audit.yml).

## The Full Loop

The audit covers hygiene; the loop plans from evidence. Drop privacy-safe CSV exports into `data/` — Search Console rows, aggregate event counts (`date,asset,event,count` only), a content inventory, an experiment ledger — and Open Growth Loop turns them into one conservative daily action:

```bash
ogl init --workspace .       # create the data files
ogl validate --workspace .   # schema and privacy-safe header checks
ogl plan --workspace .       # one action, fully explained
```

```json
{
  "action_type": "release_evidence",
  "asset": "/guides/configuration-checklist",
  "confidence": "high",
  "reason": "Staged work should be proven public before creating another asset."
}
```

Each plan ships with a **decision trace** (what won, what lost and why, which thresholds applied) and a **data freshness** report (whether the inputs deserve trust). Completed work and its later outcomes feed back into ranking, so the loop learns locally. Browse real generated reports in the [report gallery](docs/REPORT_GALLERY.md).

### Planner Engine Coverage

Candidates are ranked across the maintainer surfaces that shape OSS adoption, in deliberately conservative priority order:

1. **Release evidence** — prove staged docs, examples, or package pages are actually public before starting anything new.
2. **Outcome memory** — record what happened to completed work before repeating it.
3. **Funnel dropoff** — public pages with enough views but weak install, try, or next-step clicks.
4. **Search opportunities** — near-ranking pages and low-CTR queries from Search Console exports.
5. **Planned assets** — the next queued guide or page, only when stronger signals are absent.

Weak evidence is labeled insufficient instead of being spun into a win. The goal is less thrash, not a content treadmill.

## Commands

| Command | What it does |
| --- | --- |
| `ogl audit` | Zero-config repository readiness scorecard with one recommended action. |
| `ogl steward` | Combine the audit and local Git state into one maintainer brief and handoff. |
| `ogl fix` | Scaffold the recommended action when it is mechanical; hand off a Codex prompt when it is not. |
| `ogl init` / `ogl validate` | Create and check the local data CSVs. |
| `ogl doctor` | One-shot readiness report across validation, freshness, privacy, planning, and release review. |
| `ogl demo` | Generate the complete report set in one run. |
| `ogl freshness` | Warn when local inputs are too stale to trust. |
| `ogl candidates` / `ogl plan` | Rank every considered action; select one with a full decision trace. |
| `ogl prompt` / `ogl issue-drafts` | Turn the plan into a Codex-ready prompt or a reviewable issue draft. |
| `ogl complete` / `ogl outcome` | Record what was done and what happened, so ranking learns locally. |
| `ogl track-experiment` / `ogl ship` / `ogl review-experiments` | Baseline, ship, and conservatively review changes. |
| `ogl weekly-review` / `ogl query-backlog` / `ogl report-index` | Operating summaries and the report front page. |
| `ogl privacy-scan` | Check local files for private-data leakage before sharing. |

Full walkthroughs, data schemas, thresholds, and column aliases live in the [usage guide](docs/USAGE.md).

## Privacy Boundary

Open Growth Loop is designed around aggregate inputs. The event importer accepts only `date,asset,event,count` and rejects private-looking columns such as email, user, session, ip, payload, token, or secret. It never uploads analytics or project files, never calls hosted APIs, never publishes changes automatically, and never claims a change worked from tiny samples or missing artifacts.

## Documentation

- [Usage guide](docs/USAGE.md) — installation, every command, data files, configuration, and decision rules.
- [GitHub Action reference](docs/GITHUB_ACTION.md) — inputs, outputs, strict mode, and scheduled audits.
- [Example workflow](docs/EXAMPLE_WORKFLOW.md) — a full walkthrough with the bundled sample CSVs.
- [Report gallery](docs/REPORT_GALLERY.md) — what the generated reports look like.
- [Runnable examples](examples/README.md) — five synthetic workspaces with documented expected plans.
- [Dogfooding](docs/DOGFOODING.md) — how this repository maintains itself with its own loop.
- [Adoption and design partners](docs/ADOPTION.md) — run a field test and share verifiable feedback.
- [Releasing](docs/RELEASING.md) — the tag-driven PyPI release process.
- [Roadmap](ROADMAP.md) and [Changelog](CHANGELOG.md).

## Project Status

Version on `main`: v0.2.0. See [GitHub Releases](https://github.com/R3ijar/open-growth-loop/releases) for the latest published version. The project is early and is actively seeking maintainer design partners. The zero-config audit, steward brief, fix scaffolds, and GitHub Action are ready for field testing; the CSV-driven loop remains available for small maintainer workflows.

## Contributing

Issues and pull requests are welcome — [CONTRIBUTING.md](CONTRIBUTING.md) covers setup and expectations, and [docs/NEXT_ISSUES.md](docs/NEXT_ISSUES.md) lists good starting points. Please keep private product data and unverifiable adoption claims out of examples and docs; `ogl privacy-scan` and the release-brief guardrails exist for exactly that.

Open Growth Loop is maintained by [@R3ijar](https://github.com/R3ijar), who owns scope, releases, and final review. See the [design-partner outreach playbook](docs/OUTREACH.md) for the public feedback process.

## License

[Apache-2.0](LICENSE)
