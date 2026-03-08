"""Plotly figure builders - one method per chart type."""

from __future__ import annotations

import plotly.graph_objects as go

from hledger_lit.models import AccountBalance, HistoricalData, SankeyLink
from hledger_lit.transforms import DataTransformer


class ChartBuilder:
    """Builds Plotly figures from structured hledger data."""

    @staticmethod
    def historical_balances_plot(
        data: HistoricalData, commodity: str = ""
    ) -> go.Figure:
        """Line chart of historical balances per account, with a dashed net-worth line."""
        fig = go.Figure()

        for account_name in sorted(data.balances.keys()):
            if account_name != "net_worth":
                fig.add_trace(
                    go.Scatter(
                        x=data.dates,
                        y=[round(v, 2) for v in data.balances[account_name]],
                        mode="lines",
                        name=account_name,
                        hovertemplate=f"%{{y:,.2f}} {commodity}",
                    )
                )

        if "net_worth" in data.balances:
            fig.add_trace(
                go.Scatter(
                    x=data.dates,
                    y=[round(v, 2) for v in data.balances["net_worth"]],
                    mode="lines",
                    name="net_worth",
                    line=dict(width=3, dash="dash"),
                    hovertemplate=f"%{{y:,.2f}} {commodity}",
                )
            )

        fig.update_layout(
            title="Historical Account Balances",
            xaxis_title="Date",
            yaxis_title=f"Balance ({commodity})",
            yaxis_type="log",
            yaxis_tickformat=",.2f",
            yaxis_tickprefix=f"{commodity} ",
            hovermode="x unified",
        )
        return fig

    @staticmethod
    def expenses_treemap_plot(
        balances: list[AccountBalance], commodity: str = ""
    ) -> go.Figure:
        """Treemap of expense accounts."""
        labels = [ab.name for ab in balances]
        values = [round(ab.amount, 2) for ab in balances]
        parents = [DataTransformer.parent(ab.name) for ab in balances]

        fig = go.Figure(
            go.Treemap(
                labels=labels,
                parents=parents,
                values=values,
                branchvalues="total",
                texttemplate="%{label}<br>%{value:,.2f} " + commodity,
                hovertemplate="%{label}<br>%{value:,.2f} "
                + commodity
                + "<extra></extra>",
            )
        )
        return fig

    @staticmethod
    def daily_expenses_plot(data: HistoricalData, commodity: str = "") -> go.Figure:
        """Stacked bar chart of daily expenses by category."""
        fig = go.Figure()

        for account_name in sorted(data.balances.keys()):
            fig.add_trace(
                go.Bar(
                    x=data.dates,
                    y=[round(v, 2) for v in data.balances[account_name]],
                    name=account_name,
                    hovertemplate=f"%{{y:,.2f}} {commodity}",
                )
            )

        fig.update_layout(
            barmode="stack",
            title="Daily Expenses",
            xaxis_title="Date",
            yaxis_title=f"Amount ({commodity})",
            yaxis_tickformat=",.2f",
            yaxis_tickprefix=f"{commodity} ",
            hovermode="x unified",
        )
        return fig

    @staticmethod
    def sankey_plot(sankey_data: list[SankeyLink], commodity: str = "") -> go.Figure:
        """Sankey diagram from a list of directed links."""
        # Sort by (target, source) to keep related accounts together
        sorted_links = sorted(sankey_data, key=lambda lk: (lk.target, lk.source))

        # Unique ordered node list
        nodes: list[str] = list(
            dict.fromkeys(
                [lk.source for lk in sorted_links] + [lk.target for lk in sorted_links]
            )
        )

        fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=25,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=nodes,
                        color="blue",
                        customdata=[commodity] * len(nodes),
                        hovertemplate="%{label}<br>%{value:,.2f} %{customdata}<extra></extra>",
                    ),
                    link=dict(
                        source=[nodes.index(lk.source) for lk in sorted_links],
                        target=[nodes.index(lk.target) for lk in sorted_links],
                        value=[round(lk.value, 2) for lk in sorted_links],
                        customdata=[commodity] * len(sorted_links),
                        hovertemplate="%{source.label} → %{target.label}<br>%{value:,.2f} %{customdata}<extra></extra>",
                    ),
                )
            ]
        )
        return fig
