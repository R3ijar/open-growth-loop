# Example Workspaces

These workspaces use fake aggregate data to show how Open Growth Loop behaves in common OSS maintainer workflows.

Run any example from the repository root:

```bash
python -m open_growth_loop --workspace examples/staged-release-check validate
python -m open_growth_loop --workspace examples/staged-release-check plan
python -m open_growth_loop --workspace examples/staged-release-check prompt
```

Available examples:

- `staged-release-check`: staged docs work is prioritized for public release evidence.
- `funnel-dropoff`: aggregate events point to a weak call-to-action path.
- `aliased-search-export`: nonstandard CSV headers are mapped through `open-growth-loop.toml`.
