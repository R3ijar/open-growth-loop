# Contributing

Thanks for considering a contribution to Open Growth Loop.

## Project Values

- Local-first workflows over hosted lock-in.
- Aggregate data over private event payloads.
- One reviewable action over noisy growth automation.
- Conservative experiment reviews over premature conclusions.

## Development

```bash
python -m venv .venv
.\.venv\Scripts\python -m pip install -e .
python -m unittest discover -s tests
```

On macOS/Linux:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests
```

## Pull Requests

Please keep changes focused. A good PR usually does one of these:

- adds a small command or planner rule
- improves a CSV schema or validation path
- adds tests for a maintainer workflow
- improves docs with a reproducible example

Avoid adding hosted services, tracking SDKs, or private analytics assumptions to the core package.
