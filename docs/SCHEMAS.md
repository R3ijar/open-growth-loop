# Data Schemas

Open Growth Loop uses plain CSV files so maintainers can inspect and version their workflows.

## Content Inventory

Default path: `data/content_inventory.csv`

Current columns:

```text
status,type,asset,primary_query,cta,owner_note
```

Allowed `status` values:

- `planned`
- `staged`
- `published`

## Search Rows

Default path: `data/search_console_rows.csv`

Required columns:

```text
query,page,clicks,impressions,ctr,position
```

These rows can come from Google Search Console exports or any equivalent aggregate search source.

## Events

Default path: `data/events.csv`

Required columns:

```text
date,asset,event,count
```

Supported normalized events:

- `view`
- `cta`
- `conversion`

The importer also maps common aliases such as `page_view`, `cta_click`, and `signup`.

The importer rejects private-looking columns such as email, user, session, ip, payload, token, key, secret, phone, name, sku, and file.

## Local Schema Aliases

If an export uses different aggregate column names, create `open-growth-loop.toml` in the workspace:

```toml
[schema_aliases.search_rows]
search_term = "query"
url = "page"
shown = "impressions"
rank = "position"

[schema_aliases.events]
day = "date"
path = "asset"
kind = "event"
total = "count"
```

The left side is the source CSV header. The right side is the canonical Open Growth Loop field. Aliases are local-only, and validation reports which aliases were applied.

## Local Thresholds

The planner defaults are conservative, but a workspace can tune them in `open-growth-loop.toml`:

```toml
[thresholds]
minimum_impressions = 25
minimum_views = 25
weak_cta_rate = 0.05
review_days = 14
stale_planned_days = 14
stale_shipped_days = 21
freshness_warn_days = 21
```

`weak_cta_rate` controls the funnel-dropoff rule. `freshness_warn_days` controls when real local CSV inputs are treated as stale evidence. The command-line flags still override config values for one-off runs.

## Action Memory

Default path: `data/action_memory.csv`

Current columns:

```text
id,status,asset,action_type,source,completed_on,outcome_on,outcome,impact,confidence,artifact,note
```

Useful `status` values:

- `completed`
- `measured`

Use `ogl complete` to record that a daily plan or manual action was actually done. Use `ogl outcome` later to record the observed result, such as:

- `directionally_positive`
- `needs_iteration`
- `insufficient_sample`
- `no_visible_change`

The candidate engine uses this memory conservatively. Pending completed actions produce a `record_outcome` candidate. Exact asset/action repeats are cooled after measurement. Positive outcomes apply a small action-type boost for similar future work, and weak outcomes apply a small action-type cooldown. Missing or weak outcomes are not treated as failure unless the maintainer records them that way.

## Experiments

Default path: `data/experiments.csv`

Required columns:

```text
id,status,asset,action_type,planned_on,review_after,shipped_on,baseline_impressions,baseline_clicks,baseline_views,baseline_conversions,artifact,note,outcome
```

Useful `status` values:

- `planned`
- `staged`
- `shipped`

`planned` and `staged` experiments are never treated as successful or failed. Use `ogl ship` to mark a row as `shipped` with an artifact URL or path once the change is public. Only shipped rows with an artifact are eligible for outcome review after enough aggregate data exists.

Legacy ledgers without `shipped_on` are still accepted; the column is added the next time Open Growth Loop writes the ledger.
