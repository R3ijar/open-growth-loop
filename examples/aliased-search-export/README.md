# Aliased Search Export Example

This sample shows how maintainers can use `open-growth-loop.toml` when an aggregate export uses different column names. The source CSV uses headers such as `search_term`, `url`, `shown`, and `rank`, then maps them into the canonical search schema.

Expected command sequence:

```bash
python -m open_growth_loop --workspace examples/aliased-search-export validate
python -m open_growth_loop --workspace examples/aliased-search-export query-backlog
python -m open_growth_loop --workspace examples/aliased-search-export plan
```

Expected plan shape:

```json
{
  "action_type": "search_striking_distance",
  "asset": "/guides/plugin-migration"
}
```
