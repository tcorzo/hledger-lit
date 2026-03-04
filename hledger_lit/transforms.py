"""Pure data-transformation functions (no I/O, no UI)."""

from __future__ import annotations

import re
from typing import Any

from hledger_lit.config import (
    ASSET_REGEX,
    EXPENSE_REGEX,
    INCOME_REGEX,
    LIABILITY_REGEX,
)
from hledger_lit.models import AccountBalance, SankeyLink


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def parent(account_name: str) -> str:
    """Return the parent account name (``assets:cash`` → ``assets``)."""
    return ":".join(account_name.split(":")[:-1])


def compile_account_pattern(regex_str: str) -> re.Pattern[str]:
    """Compile a space-or-pipe separated regex string into a single pattern.

    Raises a user-friendly ``ValueError`` if the pattern is invalid.
    """
    combined = "|".join(regex_str.split())
    try:
        return re.compile(combined)
    except re.error as exc:
        raise ValueError(f"Invalid regex pattern '{regex_str}': {exc}") from exc


def extract_period_balances(
    amount_rows: list[list[dict[str, Any]]], commodity: str
) -> list[float]:
    """Extract ``abs(balance)`` for *commodity* from each period's amount list."""
    result: list[float] = []
    for amount_list in amount_rows:
        balance = 0.0
        if amount_list:
            for amount in amount_list:
                if amount["acommodity"] == commodity:
                    balance = abs(amount["aquantity"]["floatingPoint"])
                    break
        result.append(balance)
    return result


# ---------------------------------------------------------------------------
# Sankey conversion
# ---------------------------------------------------------------------------
class MissingParentAccountError(Exception):
    """Raised when a child account's parent is not present in the balance report."""


def to_sankey_data(
    balances: list[AccountBalance],
    income_regex: str = INCOME_REGEX,
    expense_regex: str = EXPENSE_REGEX,
    asset_regex: str = ASSET_REGEX,
    liability_regex: str = LIABILITY_REGEX,
) -> list[SankeyLink]:
    """Convert an hledger balance report into Sankey links.

    Assumptions
    -----------
    1. The balance report has top-level categories matching the four regex
       patterns (assets, income, expenses, liabilities).
    2. Income accounts flow *into* a central ``"pot"`` node; all other
       categories draw *from* it.
    3. Sign reversals (positive income, negative expenses) are treated as
       counter-flows.
    """
    sankey_data: list[SankeyLink] = []

    # Set of all accounts present, used to verify parent existence
    accounts = {ab.name for ab in balances}

    income_pattern = compile_account_pattern(income_regex)

    for ab in balances:
        account_name = ab.name
        balance = ab.amount

        # Top-level accounts connect to the special "pot" bucket
        if ":" not in account_name:
            parent_acc = "pot"
        else:
            parent_acc = parent(account_name)
            if parent_acc not in accounts:
                raise MissingParentAccountError(
                    f"For account {account_name}, parent account {parent_acc} "
                    "not found – have you forgotten --no-elide?"
                )

        # Income accounts flow "up" (towards the pot)
        if income_pattern.search(account_name):
            if balance < 0:
                source, target = account_name, parent_acc
            else:
                source, target = parent_acc, account_name
        else:
            if balance >= 0:
                source, target = parent_acc, account_name
            else:
                source, target = account_name, parent_acc

        sankey_data.append(SankeyLink(source=source, target=target, value=abs(balance)))

    return sankey_data
