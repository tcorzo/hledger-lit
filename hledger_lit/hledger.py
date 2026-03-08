"""Subprocess interaction with the hledger CLI."""

from __future__ import annotations

import json
import shlex
import subprocess
from typing import Any

from hledger_lit.models import AccountBalance, HistoricalData
from hledger_lit.transforms import DataTransformer


class HledgerError(Exception):
    """Raised when an hledger command fails."""


class HledgerRunner:
    """Executes hledger CLI commands and returns structured data."""

    def run_command(self, command: str) -> Any:
        """Execute an hledger command string and return the parsed JSON output.

        Uses ``shlex.split`` so that paths with spaces are handled correctly.
        Captures stderr and raises :class:`HledgerError` on non-zero exit.
        """
        result = subprocess.run(
            shlex.split(command),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise HledgerError(
                f"hledger exited with code {result.returncode}:\n{result.stderr}"
            )
        return json.loads(result.stdout)

    def run_historical_command(
        self,
        command: str,
        commodity: str,
        asset_regex: str,
        liability_regex: str,
    ) -> HistoricalData:
        """Run a historical-balance hledger command and return structured data."""
        data = self.run_command(command)

        # Extract dates from prDates - use the start date of each period
        dates: list[str] = [period[0]["contents"] for period in data["prDates"]]
        num_periods = len(dates)

        asset_pattern = DataTransformer.compile_account_pattern(asset_regex)
        liability_pattern = DataTransformer.compile_account_pattern(liability_regex)

        net_worth = [0.0] * num_periods
        balances: dict[str, list[float]] = {}

        for row in data["prRows"]:
            account_name: str = row["prrName"]
            account_balances = DataTransformer.extract_period_balances(
                row["prrAmounts"], commodity
            )
            balances[account_name] = account_balances

            # Update net worth: add assets, subtract liabilities
            if asset_pattern.search(account_name):
                net_worth = [nw + bal for nw, bal in zip(net_worth, account_balances)]
            elif liability_pattern.search(account_name):
                net_worth = [nw - bal for nw, bal in zip(net_worth, account_balances)]

        balances["net_worth"] = net_worth
        return HistoricalData(dates=dates, balances=balances)

    def run_periodic_command(
        self,
        command: str,
        commodity: str,
    ) -> HistoricalData:
        """Run a periodic-balance hledger command and return structured data.

        Unlike ``run_historical_command`` this does not compute net worth —
        it simply returns each account's per-period change.
        """
        data = self.run_command(command)

        dates: list[str] = [period[0]["contents"] for period in data["prDates"]]
        balances: dict[str, list[float]] = {}

        for row in data["prRows"]:
            account_name: str = row["prrName"]
            account_balances = DataTransformer.extract_period_balances(
                row["prrAmounts"], commodity
            )
            balances[account_name] = account_balances

        return HistoricalData(dates=dates, balances=balances)

    def read_current_balances(self, command: str) -> list[AccountBalance]:
        """Execute a balance command and return ``(account, balance)`` pairs."""
        data = self.run_command(command)

        # First element of the JSON array contains the account entries
        accounts = data[0]

        results: list[AccountBalance] = []
        for entry in accounts:
            account_name: str = entry[0]
            amounts = entry[3]
            balance = amounts[0]["aquantity"]["floatingPoint"] if amounts else 0.0
            results.append(AccountBalance(name=account_name, amount=balance))

        return results
