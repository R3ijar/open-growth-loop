# Release Notes Search Example

This sample shows a release-note workflow. The changelog page has enough impressions and sits within striking distance, so the planner recommends improving search fit for the release notes instead of creating another page.

Expected command sequence:

```bash
python -m open_growth_loop --workspace examples/release-notes-search validate
python -m open_growth_loop --workspace examples/release-notes-search freshness
python -m open_growth_loop --workspace examples/release-notes-search query-backlog
python -m open_growth_loop --workspace examples/release-notes-search plan
python -m open_growth_loop --workspace examples/release-notes-search prompt
```

Expected plan shape:

```json
{
  "action_type": "search_striking_distance",
  "asset": "/changelog/v0.1.2",
  "source": "search_opportunity"
}
```

Why this happens:

- `/changelog/v0.1.2` has 180 impressions for a feature-release query.
- The page is ranking at position 11.4, inside the striking-distance window.
- Aggregate events do not show a weak funnel path.
- A planned release-note checklist exists, but measured search demand wins before speculative new content.
