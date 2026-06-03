# Changelog

All notable changes to Open Growth Loop are documented here.

## Unreleased

## 0.1.1 - 2026-06-03

### Added

- Stale work detection in weekly reviews for planned work waiting too long, shipped work missing artifacts, shipped work ready for review, and shipped work waiting too long for review readiness.
- Configurable stale-work windows through `stale_planned_days` and `stale_shipped_days`.
- Unified action candidate engine with `ogl candidates` for ranked planner alternatives.
- Local action memory with `ogl complete`, `ogl outcome`, pending-outcome candidates, and conservative score adjustments from recorded outcomes.

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
