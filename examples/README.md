# Examples

## Repository audit context

- **Repository purpose profile** ([`repository-purpose-profile`](repository-purpose-profile/README.md)): a runnable audit fixture showing how explicit example-repository context qualifies an Install warning without turning it into a pass or inflating the score.

## Planner workspaces

These workspaces use fake aggregate data to show how Open Growth Loop behaves in common OSS maintainer workflows.

Run any example from the repository root:

```bash
python -m open_growth_loop --workspace examples/staged-release-check validate
python -m open_growth_loop --workspace examples/staged-release-check freshness
python -m open_growth_loop --workspace examples/staged-release-check plan
python -m open_growth_loop --workspace examples/staged-release-check prompt
```

Available examples:

- **Staged release check** (`staged-release-check`): staged docs work is prioritized for public release evidence. Expected: `release_evidence` for `/docs/configuration-checklist`.
- **Funnel dropoff** (`funnel-dropoff`): aggregate events point to a weak call-to-action path. Expected: `fix_funnel` for `/docs/getting-started`.
- **Aliased search export** (`aliased-search-export`): nonstandard CSV headers are mapped through `open-growth-loop.toml`. Expected: `search_striking_distance` for `/guides/plugin-migration`.
- **Package page CTA** (`package-page-cta`): a package page gets views but too few install/try clicks. Expected: `fix_funnel` for `/packages/example-cli`.
- **Release notes search** (`release-notes-search`): release notes have search demand and sit near page-one visibility. Expected: `search_striking_distance` for `/changelog/v0.1.2`.

All examples use synthetic aggregate data. They are safe to inspect, run, copy, and adapt.
