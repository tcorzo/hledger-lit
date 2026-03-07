---
description: "Add a new chart type to hledger-lit: model, transform, Plotly builder, config, and UI wiring"
agent: "agent"
argument-hint: "Describe the chart (e.g., bar chart of monthly income)"
---

Add a new chart visualization to the hledger-lit app. The user will describe the chart they want.

Follow these steps in order, matching the project's existing patterns exactly:

## 1. Data model ([models.py](../../hledger_lit/models.py))

If the new chart needs a data shape not already covered by `HistoricalData`, `AccountBalance`, or `SankeyLink`, add a new `@dataclass` to `models.py`. Keep it minimal — only fields the chart actually needs.

## 2. Data transform ([transforms.py](../../hledger_lit/transforms.py))

If the chart requires data manipulation beyond what `DataTransformer` already offers, add a new `@staticmethod` or `@classmethod` to `DataTransformer`. This must be a pure function — no I/O, no Streamlit, no subprocess calls.

## 3. Plotly figure builder ([charts.py](../../hledger_lit/charts.py))

Add a new `@staticmethod` method to `ChartBuilder` that takes the structured data and returns a `go.Figure`. Follow the existing pattern:
- Accept typed model objects (not raw dicts)
- Return `go.Figure`
- Set layout title, axis labels, and hover mode

## 4. hledger command ([hledger.py](../../hledger_lit/hledger.py))

If the chart needs a new type of hledger query (not historical balances or current balances), add a method to `HledgerRunner`. Use `shlex.split()` before `subprocess.run()` and parse JSON output with `-O json`.

## 5. Config integration ([config.py](../../hledger_lit/config.py))

Add a default command template constant (`DEFAULT_<NAME>_CMD`) to `ConfigManager`. Add the new field to:
- The `[commands]` INI section handling in `_read_ini()` / `_write_ini()`
- The `AppConfig` dataclass in `models.py`

## 6. UI wiring ([app.py](../../hledger_lit/app.py))

Wire everything together in `app.py`:
1. Add a sidebar expander for the new command template (under "Command Templates")
2. Include the new command in the `AppConfig` construction for save/load
3. Add a `render_chart()` call at the bottom, following the numbered comment pattern:

```python
# N. <Chart Name>
render_chart(
    "<Chart Name>",
    "<session_key>_fig",
    lambda: charts.<new_method>(
        # compose hledger runner + transformer + chart builder
    ),
)
```

## Constraints

- Use `from __future__ import annotations` in every modified file
- Use `@dataclass` for models, never Pydantic
- Keep subprocess calls in `hledger.py` only
- Keep Plotly code in `charts.py` only
- Keep pure transforms in `transforms.py` only
- Validate any new regex patterns with `DataTransformer.compile_account_pattern()`
