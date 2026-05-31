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
