"""Streamlit UI for hledger-lit."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from datetime import date

import plotly.graph_objects as go
import streamlit as st

from hledger_lit.charts import ChartBuilder
from hledger_lit.config import ConfigManager
from hledger_lit.hledger import HledgerError, HledgerRunner
from hledger_lit.models import AppConfig
from hledger_lit.transforms import DataTransformer


def render_chart(
    label: str,
    session_key: str,
    generate_fn: Callable[[], go.Figure],
    *,
    tip: str | None = None,
) -> None:
    """Render a generate-button → spinner → plotly-chart section."""
    st.header(label)
    if tip:
        st.caption(tip)

    if st.button(f"Generate {label}", key=f"gen_{session_key}"):
        try:
            with st.spinner(f"Generating {label}..."):
                st.session_state[session_key] = generate_fn()
        except HledgerError as e:
            st.error(f"Error running hledger command:\n{e}")
        except subprocess.CalledProcessError as e:
            st.error(f"Error running hledger command: {e}")
        except json.JSONDecodeError as e:
            st.error(f"Error parsing JSON output: {e}")
        except Exception as e:
            st.error(f"Error: {e}")
            st.exception(e)

    if st.session_state.get(session_key) is not None:
        st.plotly_chart(st.session_state[session_key], width="stretch")

    st.divider()


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(page_title="'HLedger is Lit!' Visualizer", layout="wide")
st.title("'HLedger is Lit!' Visualizer")
st.markdown("Generate graphs from hledger balance reports")

# Instantiate service objects
config_manager = ConfigManager()
hledger = HledgerRunner()
charts = ChartBuilder()
transformer = DataTransformer()

# Load persisted config (merged with defaults)
cfg = config_manager.load()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Configuration")

    filename = st.text_input(
        "HLedger Journal File Path",
        value=cfg.filename,
        help="Path to your hledger journal file, defaults to $LEDGER_FILE",
    )

    commodity = st.text_input(
        "Commodity",
        value=cfg.commodity,
        help="Commodity to convert all values to (via -value=then,{commodity})",
    )

    # Date range
    current_year = date.today().year
    start_date = st.date_input(
        "Start Date",
        value=date(current_year, 1, 1),
        help="Beginning date for the report (hledger -b flag)",
    )
    end_date = st.date_input(
        "End Date",
        value=date.today(),
        help="End date for the report (hledger -e flag)",
    )

    save_btn = st.button("Save Config")
    reset_btn = st.button("Reset to Defaults")

    # ---- Account Regex Patterns ----
    st.subheader("Account Regex Patterns")
    st.caption("Regular expressions for matching account categories")

    income_regex = st.text_input(
        "Income Regex",
        value=cfg.income_regex,
        help="Regex to match income accounts. Multiple patterns separated by space or '|'",
    )
    expense_regex = st.text_input(
        "Expense Regex",
        value=cfg.expense_regex,
        help="Regex to match expense accounts. Multiple patterns separated by space or '|'",
    )
    asset_regex = st.text_input(
        "Asset Regex",
        value=cfg.asset_regex,
        help="Regex to match asset accounts. Multiple patterns separated by space or '|'",
    )
    liability_regex = st.text_input(
        "Liability Regex",
        value=cfg.liability_regex,
        help="Regex to match liability accounts. Multiple patterns separated by space or '|'",
    )

    # ---- Command Templates ----
    st.subheader("Command Templates")
    st.caption(
        "Available variables: {filename}, {commodity}, {start_date}, {end_date}, "
        "{income_regex}, {expense_regex}, {asset_regex}, {liability_regex}, {all_accounts}"
    )

    with st.expander("Historical Balances Command", expanded=False):
        historical_cmd = st.text_area(
            "HLedger Command",
            value=cfg.historical_cmd,
            height=100,
            key="historical_cmd_sidebar",
        )

    with st.expander("Expenses Treemap Command", expanded=False):
        expenses_cmd = st.text_area(
            "HLedger Command",
            value=cfg.expenses_cmd,
            height=100,
            key="expenses_cmd_sidebar",
        )

    with st.expander("Income & Expenses Command", expanded=False):
        income_expenses_cmd = st.text_area(
            "HLedger Command",
            value=cfg.income_expenses_cmd,
            height=100,
            key="income_expenses_cmd_sidebar",
        )

    with st.expander("All Flows Command", expanded=False):
        all_flows_cmd = st.text_area(
            "HLedger Command",
            value=cfg.all_flows_cmd,
            height=100,
            key="all_flows_cmd_sidebar",
        )

# ---------------------------------------------------------------------------
# Button handlers
# ---------------------------------------------------------------------------
if save_btn:
    new_cfg = AppConfig(
        filename=filename,
        commodity=commodity,
        income_regex=income_regex,
        expense_regex=expense_regex,
        asset_regex=asset_regex,
        liability_regex=liability_regex,
        historical_cmd=historical_cmd,
        expenses_cmd=expenses_cmd,
        income_expenses_cmd=income_expenses_cmd,
        all_flows_cmd=all_flows_cmd,
    )
    path = config_manager.save(new_cfg)
    st.success(f"Configuration saved to {path}")

if reset_btn:
    config_manager.reset()
    st.success(
        "Configuration reset to defaults. Please refresh the page to see the changes."
    )

# Guard: require a journal file
if not filename:
    st.warning("👈 Please provide a path to your hledger journal file in the sidebar")
    st.stop()

# ---------------------------------------------------------------------------
# Template variables shared by all commands
# ---------------------------------------------------------------------------
all_accounts = f"{income_regex} {expense_regex} {asset_regex} {liability_regex}"
cmd_vars: dict[str, object] = {
    "filename": filename,
    "commodity": commodity,
    "start_date": start_date,
    "end_date": end_date,
    "income_regex": income_regex,
    "expense_regex": expense_regex,
    "asset_regex": asset_regex,
    "liability_regex": liability_regex,
    "all_accounts": all_accounts,
}

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

# 1. Historical Account Balances
render_chart(
    "Historical Account Balances",
    "historical_fig",
    lambda: charts.historical_balances_plot(
        hledger.run_historical_command(
            historical_cmd.format(**cmd_vars),
            commodity,
            asset_regex,
            liability_regex,
        )
    ),
    tip="💡 Tip: Click legend items to show/hide lines, double-click to isolate a single line",
)

# 2. Expenses Treemap
render_chart(
    "Expenses Treemap",
    "expenses_fig",
    lambda: charts.expenses_treemap_plot(
        hledger.read_current_balances(expenses_cmd.format(**cmd_vars))
    ),
)

# 3. Income & Expenses Flows
render_chart(
    "Income & Expenses Flows",
    "income_expenses_fig",
    lambda: charts.sankey_plot(
        transformer.to_sankey_data(
            hledger.read_current_balances(income_expenses_cmd.format(**cmd_vars)),
            income_regex,
            expense_regex,
            asset_regex,
            liability_regex,
        )
    ),
)

# 4. All Cash Flows
render_chart(
    "All Cash Flows",
    "all_balances_fig",
    lambda: charts.sankey_plot(
        transformer.to_sankey_data(
            hledger.read_current_balances(all_flows_cmd.format(**cmd_vars)),
            income_regex,
            expense_regex,
            asset_regex,
            liability_regex,
        )
    ),
)
