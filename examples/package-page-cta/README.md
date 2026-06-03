# Package Page CTA Example

This sample shows a package-page workflow. The package page has enough aggregate views, but very few visitors click through to install or try the project, so the planner recommends one focused CTA-path improvement.

Expected command sequence:

```bash
python -m open_growth_loop --workspace examples/package-page-cta validate
python -m open_growth_loop --workspace examples/package-page-cta freshness
python -m open_growth_loop --workspace examples/package-page-cta plan
python -m open_growth_loop --workspace examples/package-page-cta prompt
python -m open_growth_loop --workspace examples/package-page-cta issue-drafts
```

Expected plan shape:

```json
{
  "action_type": "fix_funnel",
  "asset": "/packages/example-cli",
  "source": "fix_funnel"
}
```

Why this happens:

- `/packages/example-cli` has 520 aggregate views.
- Only 12 CTA clicks and 1 conversion were observed.
- The CTA rate is below the default `weak_cta_rate` threshold.
- Search rows also contain future content opportunities, but the measured package-page funnel issue has stronger conservative priority.
