# Project Guidelines

## Overview

hledger-lit is a Streamlit + Plotly app that visualizes [hledger](https://hledger.org/) financial data. It shells out to the `hledger` CLI for JSON balance reports and renders four chart types: historical balances (line), expenses treemap, income/expense Sankey, and full cash-flow Sankey.

## Architecture

```
hledger CLI (JSON)  →  HledgerRunner  →  DataTransformer  →  ChartBuilder  →  Streamlit UI
```

| Module | Responsibility |
|--------|---------------|
| `app.py` | Streamlit entry point, sidebar config, chart rendering pipeline |
| `hledger.py` | Subprocess calls to hledger CLI, JSON parsing, `HledgerError` |
| `transforms.py` | Pure data transformations: regex matching, period extraction, Sankey conversion |
| `charts.py` | Plotly figure builders (line, treemap, sankey) |
| `config.py` | INI config persistence to `$XDG_CONFIG_HOME/hledger-lit.conf` |
| `models.py` | Dataclasses: `AppConfig`, `HistoricalData`, `SankeyLink`, `AccountBalance` |

Keep this separation clean — UI logic stays in `app.py`, data transformation in `transforms.py`, chart construction in `charts.py`. Don't mix subprocess calls into chart or transform code.

## Build and Run

```bash
# Run the app
uv run streamlit run hledger_lit/app.py

# Install in development mode
uv pip install -e .
```

Requires: Python ≥ 3.10, `hledger` CLI on PATH. No test suite exists yet.

## Conventions

- **Dataclasses over Pydantic** — models use `@dataclass`, not Pydantic
- **`from __future__ import annotations`** — every module uses this for forward-declared types
- **Regex patterns** — account-matching patterns are space-or-pipe separated strings compiled via `DataTransformer.compile_account_pattern()`
- **Command templates** — hledger commands use `str.format()` with variables like `{filename}`, `{commodity}`, `{start_date}`, `{end_date}`
- **Default commodity is `£`** — defined in `ConfigManager` constants
- **Subprocess safety** — commands go through `shlex.split()` before `subprocess.run()`
- **`--no-elide` is required** for Sankey charts; missing parent accounts raise `MissingParentAccountError`

## Key Pitfalls

- hledger must be installed and in PATH — no graceful fallback
- All hledger output is expected as JSON (`-O json`) with specific keys like `prDates`/`prRows`
- `main.py` at the root is legacy/deprecated — `app.py` is the active entry point
- Invalid regex from user input raises `ValueError` — always validate patterns before compiling
