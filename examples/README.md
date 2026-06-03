# Example Workspaces

These workspaces use fake aggregate data to show how Open Growth Loop behaves in common OSS maintainer workflows.

Run any example from the repository root:

```bash
python -m open_growth_loop --workspace examples/staged-release-check validate
python -m open_growth_loop --workspace examples/staged-release-check freshness
python -m open_growth_loop --workspace examples/staged-release-check plan
python -m open_growth_loop --workspace examples/staged-release-check prompt
```

Available examples:

| Workspace | Demonstrates | Expected plan |
| --- | --- | --- |
| `staged-release-check` | Staged docs work is prioritized for public release evidence. | `release_evidence` for `/docs/configuration-checklist` |
| `funnel-dropoff` | Aggregate events point to a weak call-to-action path. | `fix_funnel` for `/docs/getting-started` |
| `aliased-search-export` | Nonstandard CSV headers are mapped through `open-growth-loop.toml`. | `search_striking_distance` for `/guides/plugin-migration` |
| `package-page-cta` | A package page gets views but too few install/try clicks. | `fix_funnel` for `/packages/example-cli` |
| `release-notes-search` | Release notes have search demand and sit near page-one visibility. | `search_striking_distance` for `/changelog/v0.1.2` |

All examples use synthetic aggregate data. They are safe to inspect, run, copy, and adapt.
