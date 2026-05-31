# Funnel Dropoff Example

This sample shows an aggregate event workflow. No work is staged, but the getting-started page has enough views and weak downstream movement, so the planner recommends one focused call-to-action improvement.

Expected command sequence:

```bash
python -m open_growth_loop --workspace examples/funnel-dropoff validate
python -m open_growth_loop --workspace examples/funnel-dropoff plan
python -m open_growth_loop --workspace examples/funnel-dropoff track-experiment
```

Expected plan shape:

```json
{
  "action_type": "fix_funnel",
  "asset": "/docs/getting-started"
}
```
