---
description: "Scaffold a pytest test suite for hledger-lit with fixtures, transform tests, chart tests, and pyproject.toml config"
agent: "agent"
---

Scaffold a complete pytest test suite for this project. No tests exist yet.

## 1. Add pytest to [pyproject.toml](../../pyproject.toml)

Add pytest as an optional dev dependency and a `[tool.pytest.ini_options]` section:

```toml
[project.optional-dependencies]
dev = ["pytest"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

## 2. Create test fixtures in `tests/conftest.py`

Build pytest fixtures with realistic mock data matching hledger's JSON output shapes. The project uses two JSON formats:

**Historical balance report** (used by `HledgerRunner.run_historical_command`):
```python
{
    "prDates": [[{"contents": "2024-01-01"}], [{"contents": "2024-02-01"}]],
    "prRows": [
        {
            "prrName": "assets:checking",
            "prrAmounts": [
                [{"acommodity": "£", "aquantity": {"floatingPoint": 1000.0}}],
                [{"acommodity": "£", "aquantity": {"floatingPoint": 1200.0}}],
            ],
        }
    ],
}
```

**Current balance report** (used by `HledgerRunner.read_current_balances`):
```python
[
    [
        ["expenses", 0, 0, [{"acommodity": "£", "aquantity": {"floatingPoint": 500.0}}]],
        ["expenses:food", 0, 0, [{"acommodity": "£", "aquantity": {"floatingPoint": 300.0}}]],
    ]
]
```

Create fixtures for:
- A historical balance JSON dict with at least 3 accounts across 3 periods
- A current balance JSON list with a realistic account hierarchy (include parent + children for treemap/sankey)
- Pre-parsed `AccountBalance` lists and `HistoricalData` objects for direct use in transform/chart tests
- A fixture that returns `SankeyLink` lists for chart tests

## 3. Test `DataTransformer` ([transforms.py](../../hledger_lit/transforms.py))

Create `tests/test_transforms.py` covering:

- `parent()` — hierarchical names (`"a:b:c"` → `"a:b"`), top-level (`"a"` → `""`)
- `compile_account_pattern()` — space-separated input, pipe-separated input, invalid regex raises `ValueError`
- `extract_period_balances()` — matching commodity, missing commodity returns 0.0, empty amount list
- `to_sankey_data()` — correct link direction for income vs expense accounts, `MissingParentAccountError` when parent missing (no `--no-elide`), sign reversal handling

## 4. Test `ChartBuilder` ([charts.py](../../hledger_lit/charts.py))

Create `tests/test_charts.py` covering:

- `historical_balances_plot()` — returns `go.Figure`, correct number of traces, net_worth trace has dashed line
- `expenses_treemap_plot()` — returns `go.Figure`, labels match input
- `sankey_plot()` — returns `go.Figure`, node labels contain all unique accounts from links

For chart tests, assert on figure structure (trace count, data properties) — don't test visual rendering.

## 5. Test `HledgerRunner` ([hledger.py](../../hledger_lit/hledger.py))

Create `tests/test_hledger.py` covering:

- `run_command()` — mock `subprocess.run`, verify `shlex.split` is used, `HledgerError` on non-zero exit
- `run_historical_command()` — mock `run_command` to return fixture JSON, verify returned `HistoricalData` structure
- `read_current_balances()` — mock `run_command` to return fixture JSON, verify `AccountBalance` list

Use `unittest.mock.patch` to mock subprocess — never call real hledger in tests.

## 6. Test `ConfigManager` ([config.py](../../hledger_lit/config.py))

Create `tests/test_config.py` covering:

- `load()` returns valid `AppConfig` with defaults when no config file exists
- `save()` / `load()` round-trip preserves all fields
- `reset()` removes the config file

Use `tmp_path` fixture for config file isolation.

## Constraints

- Use `from __future__ import annotations` in all test files
- Never call real hledger — always mock subprocess
- Use `@dataclass` model instances directly in assertions
- Keep test files focused: one test file per source module
