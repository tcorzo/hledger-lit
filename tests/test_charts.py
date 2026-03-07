"""Tests for ChartBuilder (charts.py)."""

from __future__ import annotations

import plotly.graph_objects as go

from hledger_lit.models import AccountBalance, HistoricalData, SankeyLink
from hledger_lit.charts import ChartBuilder


# ---------------------------------------------------------------------------
# historical_balances_plot()
# ---------------------------------------------------------------------------


class TestHistoricalBalancesPlot:
    def test_returns_figure(self, historical_data: HistoricalData):
        fig = ChartBuilder.historical_balances_plot(historical_data)
        assert isinstance(fig, go.Figure)

    def test_correct_trace_count(self, historical_data: HistoricalData):
        fig = ChartBuilder.historical_balances_plot(historical_data)
        # 3 account traces + 1 net_worth trace = 4
        assert len(fig.data) == 4

    def test_net_worth_trace_is_dashed(self, historical_data: HistoricalData):
        fig = ChartBuilder.historical_balances_plot(historical_data)
        nw_traces = [t for t in fig.data if t.name == "net_worth"]
        assert len(nw_traces) == 1
        assert nw_traces[0].line.dash == "dash"

    def test_non_net_worth_traces_are_solid(self, historical_data: HistoricalData):
        fig = ChartBuilder.historical_balances_plot(historical_data)
        other_traces = [t for t in fig.data if t.name != "net_worth"]
        for t in other_traces:
            assert t.line.dash is None


# ---------------------------------------------------------------------------
# expenses_treemap_plot()
# ---------------------------------------------------------------------------


class TestExpensesTreemapPlot:
    def test_returns_figure(self):
        balances = [
            AccountBalance(name="expenses", amount=800.0),
            AccountBalance(name="expenses:food", amount=300.0),
            AccountBalance(name="expenses:rent", amount=500.0),
        ]
        fig = ChartBuilder.expenses_treemap_plot(balances)
        assert isinstance(fig, go.Figure)

    def test_labels_match_input(self):
        balances = [
            AccountBalance(name="expenses", amount=800.0),
            AccountBalance(name="expenses:food", amount=300.0),
            AccountBalance(name="expenses:rent", amount=500.0),
        ]
        fig = ChartBuilder.expenses_treemap_plot(balances)
        treemap_trace = fig.data[0]
        assert list(treemap_trace.labels) == [
            "expenses",
            "expenses:food",
            "expenses:rent",
        ]


# ---------------------------------------------------------------------------
# sankey_plot()
# ---------------------------------------------------------------------------


class TestSankeyPlot:
    def test_returns_figure(self, sankey_links: list[SankeyLink]):
        fig = ChartBuilder.sankey_plot(sankey_links)
        assert isinstance(fig, go.Figure)

    def test_node_labels_contain_all_accounts(self, sankey_links: list[SankeyLink]):
        fig = ChartBuilder.sankey_plot(sankey_links)
        sankey_trace = fig.data[0]
        node_labels = set(sankey_trace.node.label)

        all_accounts: set[str] = set()
        for lk in sankey_links:
            all_accounts.add(lk.source)
            all_accounts.add(lk.target)

        assert all_accounts == node_labels
