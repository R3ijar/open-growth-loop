# Staged Release Check Example

This sample shows the highest-priority planner path: staged work that needs public release evidence before the maintainer starts another docs task.

Expected command sequence:

```bash
python -m open_growth_loop --workspace examples/staged-release-check validate
python -m open_growth_loop --workspace examples/staged-release-check plan
python -m open_growth_loop --workspace examples/staged-release-check prompt
```

Expected plan shape:

```json
{
  "action_type": "release_evidence",
  "asset": "/docs/configuration-checklist"
}
```
