"""Shared pytest fixtures with realistic hledger mock data."""

from __future__ import annotations

import pytest

from hledger_lit.models import AccountBalance, HistoricalData, SankeyLink


# ---------------------------------------------------------------------------
# Raw hledger JSON fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def historical_balance_json() -> dict:
    """Historical balance report JSON (``hledger balance --historical -O json``)."""
    return {
        "prDates": [
            [{"contents": "2024-01-01"}],
            [{"contents": "2024-02-01"}],
            [{"contents": "2024-03-01"}],
        ],
        "prRows": [
            {
                "prrName": "assets:checking",
                "prrAmounts": [
                    [{"acommodity": "£", "aquantity": {"floatingPoint": 1000.0}}],
                    [{"acommodity": "£", "aquantity": {"floatingPoint": 1200.0}}],
                    [{"acommodity": "£", "aquantity": {"floatingPoint": 1500.0}}],
                ],
            },
            {
                "prrName": "assets:savings",
                "prrAmounts": [
                    [{"acommodity": "£", "aquantity": {"floatingPoint": 5000.0}}],
                    [{"acommodity": "£", "aquantity": {"floatingPoint": 5000.0}}],
                    [{"acommodity": "£", "aquantity": {"floatingPoint": 5200.0}}],
                ],
            },
            {
                "prrName": "liabilities:credit_card",
                "prrAmounts": [
                    [{"acommodity": "£", "aquantity": {"floatingPoint": 200.0}}],
                    [{"acommodity": "£", "aquantity": {"floatingPoint": 150.0}}],
                    [{"acommodity": "£", "aquantity": {"floatingPoint": 100.0}}],
                ],
            },
        ],
    }


@pytest.fixture()
def current_balance_json() -> list:
    """Current balance report JSON (``hledger balance -O json``)."""
    return [
        [
            [
                "expenses",
                0,
                0,
                [{"acommodity": "£", "aquantity": {"floatingPoint": 800.0}}],
            ],
            [
                "expenses:food",
                0,
                0,
                [{"acommodity": "£", "aquantity": {"floatingPoint": 300.0}}],
            ],
            [
                "expenses:food:groceries",
                0,
                0,
                [{"acommodity": "£", "aquantity": {"floatingPoint": 200.0}}],
            ],
            [
                "expenses:food:dining",
                0,
                0,
                [{"acommodity": "£", "aquantity": {"floatingPoint": 100.0}}],
            ],
            [
                "expenses:rent",
                0,
                0,
                [{"acommodity": "£", "aquantity": {"floatingPoint": 500.0}}],
            ],
            [
                "income",
                0,
                0,
                [{"acommodity": "£", "aquantity": {"floatingPoint": -2000.0}}],
            ],
            [
                "income:salary",
                0,
                0,
                [{"acommodity": "£", "aquantity": {"floatingPoint": -1800.0}}],
            ],
            [
                "income:interest",
                0,
                0,
                [{"acommodity": "£", "aquantity": {"floatingPoint": -200.0}}],
            ],
        ]
    ]


# ---------------------------------------------------------------------------
# Pre-parsed model fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def historical_data() -> HistoricalData:
    """Pre-parsed HistoricalData for chart / transform tests."""
    return HistoricalData(
        dates=["2024-01-01", "2024-02-01", "2024-03-01"],
        balances={
            "assets:checking": [1000.0, 1200.0, 1500.0],
            "assets:savings": [5000.0, 5000.0, 5200.0],
            "liabilities:credit_card": [200.0, 150.0, 100.0],
            "net_worth": [5800.0, 6050.0, 6600.0],
        },
    )


@pytest.fixture()
def account_balances() -> list[AccountBalance]:
    """Pre-parsed account balances with a realistic hierarchy."""
    return [
        AccountBalance(name="expenses", amount=800.0),
        AccountBalance(name="expenses:food", amount=300.0),
        AccountBalance(name="expenses:food:groceries", amount=200.0),
        AccountBalance(name="expenses:food:dining", amount=100.0),
        AccountBalance(name="expenses:rent", amount=500.0),
        AccountBalance(name="income", amount=-2000.0),
        AccountBalance(name="income:salary", amount=-1800.0),
        AccountBalance(name="income:interest", amount=-200.0),
    ]


@pytest.fixture()
def sankey_links() -> list[SankeyLink]:
    """Pre-built SankeyLink list for chart tests."""
    return [
        SankeyLink(source="pot", target="expenses", value=800.0),
        SankeyLink(source="expenses", target="expenses:food", value=300.0),
        SankeyLink(
            source="expenses:food", target="expenses:food:groceries", value=200.0
        ),
        SankeyLink(source="expenses:food", target="expenses:food:dining", value=100.0),
        SankeyLink(source="expenses", target="expenses:rent", value=500.0),
        SankeyLink(source="income", target="pot", value=2000.0),
        SankeyLink(source="income:salary", target="income", value=1800.0),
        SankeyLink(source="income:interest", target="income", value=200.0),
    ]
