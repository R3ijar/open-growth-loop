# Changelog

All notable changes to Open Growth Loop are documented here.

## 0.3.0 - 2026-09-01

### Added

- Optional repository-owned audit purpose profiles for `standard`, `example`, `template`, and `monorepo` repositories. Maintainers can qualify or explicitly skip context-sensitive warnings with bounded human-readable reasons; dispositions remain visible in Markdown and JSON, stay in the score denominator, and never count as passes. README and license checks cannot be overridden.
- A runnable repository-purpose fixture modeled on editable packaging-tutorial material, plus documentation for profile validation, trust boundaries, and score integrity.
- Three repository-specific decision-quality case studies with exact SHAs, raw recommendations, counterevidence, verdicts, and explicit non-adoption limits.

### Fixed

- Default-branch CI evidence now reports only workflows whose latest completed run failed, so a later success clears a recovered historical failure.
- README sections with explicit vulnerability-reporting guidance now satisfy the security-policy audit instead of requiring a specific filename.

## 0.2.1 - 2026-08-12

### Changed

- Shortened the reusable Action description to satisfy GitHub Marketplace metadata requirements.
- Identified the Action author as Jesus (R3ijar) in its public Marketplace metadata.
- Updated official GitHub Actions dependencies to their current Node.js 24-compatible major releases.

## 0.2.0 - 2026-08-12

### Added

- `ogl steward` combines the repository audit and local Git state into one evidence-backed maintainer brief with a conservative agent handoff.
- Optional `ogl steward --github owner/repo` evidence adapter that reads bounded issue, pull-request, default-branch CI, and release metadata through `gh` without mutating GitHub; unavailable remote evidence is explicit rather than treated as an empty queue.
- Installable `repo-steward` Codex skill for audit, triage, safe fixes, release preparation, and maintainer handoffs.
- Public adoption and design-partner guide with explicit evidence rules and targets that are not presented as achievements.
- Public ten-repository compatibility study across Python, Go, Rust, and Node.js, with exact inspected commits, raw heuristic outputs, defects found, and explicit non-adoption limitations.
- Structured maintainer field-test issue form, CODEOWNERS, and a low-contact outreach playbook.
- `ogl fix` scaffolds the audit's recommended action when it is mechanical: license (with an explicit `--license mit` or `--license apache-2.0` choice), README skeleton, changelog, contributing guide, code of conduct, security policy, issue and pull request templates, and a starter CI workflow detected from the project ecosystem (Python, Node, Rust, Go). Existing files are never overwritten, `--dry-run` previews the writes, `--list` shows which checks have scaffolds, and gaps that need real judgment hand off a Codex-ready prompt instead.
- `ogl audit` zero-config repository audit: scores README quality, license, onboarding, community files, changelog, CI, and release-tag hygiene for any repository, then recommends one conservative next action with a Codex-ready prompt. No CSV data required.
- Reusable GitHub Action (`action.yml`) so any repository can run the audit from a workflow and read the report in the job summary, with `ok` and `score-percent` outputs and an optional `strict` mode.
- Repository audit workflow that dogfoods the action on this repository on push, pull request, and a weekly schedule.
- Release workflow that builds distributions and publishes to PyPI through trusted publishing when a `v*` tag is pushed.
- Ruff lint job in CI with a pinned rule set, and Python 3.13 added to the test matrix.
- The audit report is included in `ogl demo` output and listed on the report index front page.

### Changed

- Repositioned the project around repository stewardship and real maintainer demand instead of application-facing claims.
- Updated package license metadata to the SPDX form supported by current setuptools releases.
- Declared `@R3ijar` as package maintainer and final repository reviewer.

### Fixed

- Git author names are decoded as UTF-8 with replacement fallback, preventing Windows locale errors on repositories with international contributor names.
- Root-level dual-license files such as `LICENSE-APACHE` and `LICENSE-MIT` now satisfy the repository audit instead of producing a false missing-license failure.
- Freshness checks no longer flag mtime-based inputs as `future_dated` when the file was modified after a historical check date; that status is now reserved for dates parsed from data rows.
- `[schema_aliases.action_memory]` config sections are accepted; previously the documented alias path raised `unknown schema alias section`.
- `ogl prompt`, `ogl complete`, and `ogl track-experiment` now explain how to regenerate a missing or malformed `latest-plan.json` instead of crashing with a traceback.

### Removed

- Dead `best_funnel_dropoff` helper in the planner; funnel logic lives in the candidate engine.

## 0.1.7 - 2026-06-03

### Added

- `ogl doctor` command that composes validation, freshness, privacy scanning, candidate ranking, planning, and release-readiness into one local maintainer readiness report.
- Report index JSON output at `outbox/index.json`, including readiness summary, missing reports, and per-report metadata for automation-friendly reviews.

## 0.1.6 - 2026-06-03

### Added

- `ogl demo` command that generates the main local report set in one reviewable run: freshness, candidates, query backlog, plan, prompt, issue draft, experiment review, weekly review, privacy scan, release brief, and report index.

## 0.1.5 - 2026-06-03

### Added

- Public report gallery with sanitized examples of the report index, daily plan, candidate ranking, freshness report, issue draft, release brief, and weekly review.

## 0.1.4 - 2026-06-03

### Added

- Report Design v1 for generated Markdown outputs, including reader-first scorecards, ranking tables, freshness tables, release-readiness tables, and collapsible plan audit evidence.
- `ogl report-index` command that writes a local `outbox/index.md` front page linking generated reports with status, timestamps, and recommended reading order.
- README landing-page polish with a stronger first-screen message, maintainer workflow visual, release badge, at-a-glance project signals, and clearer output map.

### Fixed

- README workflow visual helper labels now wrap cleanly inside their boxes on GitHub.

## 0.1.3 - 2026-06-03

### Added

- `ogl release-brief` command that writes Markdown and JSON release-readiness reports covering validation, freshness, privacy scan status, latest plan, example coverage, changelog state, README planner coverage, and manual adoption-claim guardrails.
- Dogfooding documentation for using Open Growth Loop to maintain this repository.
- Release-readiness documentation for interpreting `ready with manual review` reports.
- Runnable synthetic package-page and release-note sample workspaces, including documented expected `ogl plan` outputs.
- README planner-engine coverage section that explains the public maintainer surfaces supported by the generic rules.

## 0.1.2 - 2026-06-03

### Added

- Data Freshness v1 with `ogl freshness` and embedded plan freshness warnings for stale, empty, missing, future-dated, or sample local CSV inputs.
- Local `ogl issue-drafts` command that turns the latest plan into a reviewable Markdown GitHub issue draft without requiring GitHub auth.
- Decision Trace v2 in generated plans, including winner metadata, ranked alternatives, losing reasons, thresholds, blocked state, and memory notes.
- README landing-page polish for a clearer maintainer-tool presentation.

### Fixed

- Aligned package `__version__` and project metadata with the published `0.1.2` release.

## 0.1.1 - 2026-06-03

### Added

- Stale work detection in weekly reviews for planned work waiting too long, shipped work missing artifacts, shipped work ready for review, and shipped work waiting too long for review readiness.
- Configurable stale-work windows through `stale_planned_days` and `stale_shipped_days`.
- Unified action candidate engine with `ogl candidates` for ranked planner alternatives.
- Local action memory with `ogl complete`, `ogl outcome`, pending-outcome candidates, and conservative score adjustments from recorded outcomes.
- README polish, including a GitHub-rendered workflow diagram instead of Mermaid.

## 0.1.0 - 2026-05-30

Initial public Apache-2.0 release.

### Added

- Local-first CLI for OSS maintainer growth loops.
- Workspace initialization and validation commands.
- CSV readers for content inventory, Search Console rows, aggregate events, and experiment ledgers.
- Conservative daily planner with release evidence, funnel, search, planned asset, and wait-for-data rules.
- Decision explanations in generated plans, including selected rule, skipped rules, and thresholds used.
- Configurable local thresholds in `open-growth-loop.toml`.
- Local schema aliases for CSV exports with nonstandard headers.
- Query backlog generation.
- Codex-ready prompt generation.
- Experiment tracking, shipped artifact recording, and outcome review.
- Dated report history while preserving `latest-*` paths.
- Weekly operating review for inventory and experiment state.
- Local privacy scan command for CSV headers and secret-like text.
- Runnable sample workspaces for release evidence, funnel dropoff, and aliased search exports.
- Apache-2.0 license, governance docs, CI, issue templates, and contribution guidance.
