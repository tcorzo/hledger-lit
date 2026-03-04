"""Configuration loading, saving, and defaults for hledger-lit."""

from __future__ import annotations

import configparser
import os
from pathlib import Path

from hledger_lit.models import AppConfig


class ConfigManager:
    """Manages loading, saving, and resetting hledger-lit configuration."""

    # Default account-matching regex patterns
    ASSET_REGEX = "assets"
    LIABILITY_REGEX = "liabilities"
    INCOME_REGEX = "income|virtual|revenues"
    EXPENSE_REGEX = "expenses"

    # Default hledger command templates
    DEFAULT_HISTORICAL_CMD = (
        "hledger -f {filename} balance {all_accounts} not:tag:clopen "
        "--depth 1 --period daily --historical "
        "--value=then,{commodity} --infer-value -O json "
        "-b {start_date} -e {end_date}"
    )
    DEFAULT_EXPENSES_CMD = (
        "hledger -f {filename} balance {expense_regex} not:tag:clopen "
        "--cost --value=then,{commodity} --infer-value "
        "--no-total --tree --no-elide -O json "
        "-b {start_date} -e {end_date}"
    )
    DEFAULT_INCOME_EXPENSES_CMD = (
        "hledger -f {filename} balance {income_regex} {expense_regex} not:tag:clopen "
        "--cost --value=then,{commodity} --infer-value "
        "--no-total --tree --no-elide -O json "
        "-b {start_date} -e {end_date}"
    )
    DEFAULT_ALL_FLOWS_CMD = (
        "hledger -f {filename} balance {all_accounts} not:tag:clopen "
        "--cost --value=then,{commodity} --infer-value "
        "--no-total --tree --no-elide -O json "
        "-b {start_date} -e {end_date}"
    )

    def __init__(self) -> None:
        self._config_path = self._resolve_config_path()

    @staticmethod
    def _resolve_config_path() -> Path:
        """Return the path to the INI config file, creating the directory if needed."""
        config_home = os.environ.get("XDG_CONFIG_HOME")
        if not config_home:
            config_home = os.path.join(os.path.expanduser("~"), ".config")
        config_dir = Path(config_home)
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "hledger-lit.conf"

    @property
    def config_path(self) -> Path:
        """The path to the INI config file."""
        return self._config_path

    def _read_ini(self) -> configparser.ConfigParser:
        """Read the INI config file (if it exists) and return the parser."""
        config = configparser.ConfigParser()
        if self._config_path.exists():
            config.read(self._config_path)
        return config

    @staticmethod
    def _get(
        config: configparser.ConfigParser, section: str, key: str, default: str
    ) -> str:
        """Return a config value with a fallback default."""
        try:
            return config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def load(self) -> AppConfig:
        """Load persisted configuration, falling back to built-in defaults."""
        ini = self._read_ini()
        return AppConfig(
            filename=self._get(
                ini, "settings", "filename", os.environ.get("LEDGER_FILE", "")
            ),
            commodity=self._get(ini, "settings", "commodity", "£"),
            income_regex=self._get(ini, "regex", "income", self.INCOME_REGEX),
            expense_regex=self._get(ini, "regex", "expense", self.EXPENSE_REGEX),
            asset_regex=self._get(ini, "regex", "asset", self.ASSET_REGEX),
            liability_regex=self._get(ini, "regex", "liability", self.LIABILITY_REGEX),
            historical_cmd=self._get(
                ini, "commands", "historical", self.DEFAULT_HISTORICAL_CMD
            ),
            expenses_cmd=self._get(
                ini, "commands", "expenses_treemap", self.DEFAULT_EXPENSES_CMD
            ),
            income_expenses_cmd=self._get(
                ini, "commands", "income_expenses", self.DEFAULT_INCOME_EXPENSES_CMD
            ),
            all_flows_cmd=self._get(
                ini, "commands", "all_flows", self.DEFAULT_ALL_FLOWS_CMD
            ),
        )

    def save(self, cfg: AppConfig) -> Path:
        """Persist an AppConfig to the INI file. Returns the path written."""
        ini = configparser.ConfigParser()

        ini["settings"] = {
            "filename": cfg.filename,
            "commodity": cfg.commodity,
        }
        ini["regex"] = {
            "income": cfg.income_regex,
            "expense": cfg.expense_regex,
            "asset": cfg.asset_regex,
            "liability": cfg.liability_regex,
        }
        ini["commands"] = {
            "historical": cfg.historical_cmd,
            "expenses_treemap": cfg.expenses_cmd,
            "income_expenses": cfg.income_expenses_cmd,
            "all_flows": cfg.all_flows_cmd,
        }

        with open(self._config_path, "w", encoding="utf-8") as fh:
            ini.write(fh)
        return self._config_path

    def reset(self) -> None:
        """Delete the INI config file so the next load returns defaults."""
        if self._config_path.exists():
            self._config_path.unlink()
