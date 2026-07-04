# GitHub Action

Open Growth Loop ships a reusable composite action at the repository root (`action.yml`). It installs the CLI on the runner, audits the checked-out repository, and appends the full Markdown report to the Actions job summary. Everything runs on the runner; no project data leaves it.

## Minimal usage

```yaml
name: Repository Audit
on:
  push:
    branches: [main]
  pull_request:

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0   # lets the audit read tag history for release-hygiene checks
      - uses: R3ijar/open-growth-loop@v0.2.0
```

Open the run in the Actions tab and the audit report is in the job summary.

## Inputs

| Input | Default | Purpose |
| --- | --- | --- |
| `path` | `.` | Directory of the repository to audit, relative to the workflow workspace. |
| `strict` | `"false"` | When `"true"`, the step fails if an essential check (README, LICENSE) fails. |
| `python-version` | `"3.12"` | Python version used to run the audit. |

## Outputs

| Output | Meaning |
| --- | --- |
| `ok` | `true` when no essential check failed. |
| `score-percent` | Percentage of audit checks that pass. |

Example of using the outputs:

```yaml
      - uses: R3ijar/open-growth-loop@v0.2.0
        id: audit
      - name: Comment on low scores
        if: ${{ steps.audit.outputs.score-percent < 70 }}
        run: echo "Audit score is ${{ steps.audit.outputs.score-percent }}%. See the job summary."
```

## What the audit checks

Fourteen checks across five categories:

- **Essentials:** README present and substantial; license file present.
- **Onboarding:** install instructions, quickstart with a copy-pasteable example, documentation, examples.
- **Community:** contributing guide, code of conduct, security policy, issue templates, pull request template.
- **Release:** changelog present; tagged releases keeping pace with commits (requires git history, hence `fetch-depth: 0`).
- **Automation:** CI configuration present.

The report ends with one recommended next action, ordered by how much each gap hurts a new visitor, plus a Codex-ready prompt for that action.

## Scheduled audits

Run weekly so drift shows up without anyone remembering to check:

```yaml
on:
  schedule:
    - cron: "0 7 * * 1"
```

## Versioning

Pin a tag (`@v0.2.0`) for stability. `@main` tracks the latest development state.
