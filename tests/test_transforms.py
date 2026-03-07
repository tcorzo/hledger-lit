"""Tests for DataTransformer (transforms.py)."""

from __future__ import annotations

import pytest

from hledger_lit.models import AccountBalance
from hledger_lit.transforms import DataTransformer, MissingParentAccountError


# ---------------------------------------------------------------------------
# parent()
# ---------------------------------------------------------------------------


class TestParent:
    def test_hierarchical_name(self):
        assert DataTransformer.parent("a:b:c") == "a:b"

    def test_two_levels(self):
        assert DataTransformer.parent("assets:checking") == "assets"

    def test_top_level_returns_empty(self):
        assert DataTransformer.parent("assets") == ""

    def test_single_component(self):
        assert DataTransformer.parent("expenses") == ""


# ---------------------------------------------------------------------------
# compile_account_pattern()
# ---------------------------------------------------------------------------


class TestCompileAccountPattern:
    def test_space_separated(self):
        pat = DataTransformer.compile_account_pattern("income revenues")
        assert pat.search("income:salary")
        assert pat.search("revenues:other")
        assert not pat.search("expenses:food")

    def test_pipe_separated(self):
        pat = DataTransformer.compile_account_pattern("income|revenues")
        assert pat.search("income:salary")
        assert pat.search("revenues:other")

    def test_single_pattern(self):
        pat = DataTransformer.compile_account_pattern("assets")
        assert pat.search("assets:checking")
        assert not pat.search("liabilities")

    def test_invalid_regex_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            DataTransformer.compile_account_pattern("[invalid")


# ---------------------------------------------------------------------------
# extract_period_balances()
# ---------------------------------------------------------------------------


class TestExtractPeriodBalances:
    def test_matching_commodity(self):
        amounts = [
            [{"acommodity": "£", "aquantity": {"floatingPoint": 100.0}}],
            [{"acommodity": "£", "aquantity": {"floatingPoint": 200.0}}],
        ]
        result = DataTransformer.extract_period_balances(amounts, "£")
        assert result == [100.0, 200.0]

    def test_missing_commodity_returns_zero(self):
        amounts = [
            [{"acommodity": "$", "aquantity": {"floatingPoint": 100.0}}],
        ]
        result = DataTransformer.extract_period_balances(amounts, "£")
        assert result == [0.0]

    def test_empty_amount_list(self):
        amounts: list[list] = [[]]
        result = DataTransformer.extract_period_balances(amounts, "£")
        assert result == [0.0]

    def test_negative_value_returns_absolute(self):
        amounts = [
            [{"acommodity": "£", "aquantity": {"floatingPoint": -500.0}}],
        ]
        result = DataTransformer.extract_period_balances(amounts, "£")
        assert result == [500.0]


# ---------------------------------------------------------------------------
# to_sankey_data()
# ---------------------------------------------------------------------------


class TestToSankeyData:
    def test_income_flows_to_pot(self, account_balances: list[AccountBalance]):
        links = DataTransformer.to_sankey_data(account_balances)
        # Top-level income (negative balance) should flow: income → pot
        income_links = [
            lk for lk in links if lk.source == "income" and lk.target == "pot"
        ]
        assert len(income_links) == 1
        assert income_links[0].value == 2000.0

    def test_expense_flows_from_pot(self, account_balances: list[AccountBalance]):
        links = DataTransformer.to_sankey_data(account_balances)
        expense_links = [
            lk for lk in links if lk.source == "pot" and lk.target == "expenses"
        ]
        assert len(expense_links) == 1
        assert expense_links[0].value == 800.0

    def test_child_income_links_to_parent(self, account_balances: list[AccountBalance]):
        links = DataTransformer.to_sankey_data(account_balances)
        salary_links = [lk for lk in links if lk.source == "income:salary"]
        assert len(salary_links) == 1
        assert salary_links[0].target == "income"

    def test_missing_parent_raises_error(self):
        balances = [
            AccountBalance(name="expenses:food:groceries", amount=200.0),
        ]
        with pytest.raises(MissingParentAccountError, match="--no-elide"):
            DataTransformer.to_sankey_data(balances)

    def test_sign_reversal_expense(self):
        """A negative expense balance reverses the link direction."""
        balances = [
            AccountBalance(name="expenses", amount=-50.0),
        ]
        links = DataTransformer.to_sankey_data(balances)
        assert links[0].source == "expenses"
        assert links[0].target == "pot"
        assert links[0].value == 50.0

    def test_all_links_have_positive_values(
        self, account_balances: list[AccountBalance]
    ):
        links = DataTransformer.to_sankey_data(account_balances)
        for lk in links:
            assert lk.value >= 0
