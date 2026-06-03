# Changelog

All notable changes to Open Growth Loop are documented here.

## Unreleased

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
