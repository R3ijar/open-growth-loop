# AGENTS.md

Guidance for Codex and other coding agents working on Open Growth Loop.

## Project Boundary

Open Growth Loop is generic OSS maintainer tooling. Keep the public project focused on:

- local-first CLI workflows
- repository audits, local Git maintenance signals, and one-action maintainer briefs
- aggregate Search Console rows
- aggregate event CSVs
- docs, examples, onboarding, release notes, package pages, and project websites
- conservative experiment tracking and review

Do not add private product names, customer data, raw analytics payloads, personal data, or project-specific strategy to this repository.

## Development Commands

Run the core checks before proposing or committing changes:

```bash
python -m unittest discover -s tests
python -m ruff check src tests
python -m open_growth_loop --workspace . validate
python -m open_growth_loop --workspace . audit
python -m open_growth_loop --workspace . steward
python -m open_growth_loop --workspace . plan
python -m open_growth_loop --workspace . query-backlog
python -m open_growth_loop --workspace . prompt
```

Use a temporary workspace when testing `init`:

```bash
python -m open_growth_loop init --workspace /tmp/ogl-smoke
```

On Windows PowerShell, use a temp path under `$env:TEMP`.

## Privacy Checks

Before publishing or opening a PR, scan for private terms and accidental sensitive fields:

```bash
rg -n "TODO-private|customer|raw_user|session|token|secret|payload|api_key" . -g "!outbox/**" -g "!.git/**"
```

Not every match is automatically a failure. For example, documentation may mention rejected private column names. Review each match before publishing.

## Change Style

- Prefer deterministic rules before model-generated recommendations.
- Keep the CLI useful without hosted accounts, API keys, or secrets.
- Treat generated reports as review aids, not truth.
- Do not claim adoption, downloads, stars, or ecosystem impact unless it is public and verifiable.
- Add focused tests when changing planner, validation, import, review, or prompt behavior.
