"""Tests for ConfigManager (config.py)."""

from __future__ import annotations

from pathlib import Path

import pytest

from hledger_lit.config import ConfigManager
from hledger_lit.models import AppConfig


@pytest.fixture()
def config_manager(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ConfigManager:
    """A ConfigManager that writes to a temp directory."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    return ConfigManager()


# ---------------------------------------------------------------------------
# load() defaults
# ---------------------------------------------------------------------------


class TestLoadDefaults:
    def test_returns_app_config(self, config_manager: ConfigManager):
        cfg = config_manager.load()
        assert isinstance(cfg, AppConfig)

    def test_default_commodity(self, config_manager: ConfigManager):
        cfg = config_manager.load()
        assert cfg.commodity == "£"

    def test_default_regexes(self, config_manager: ConfigManager):
        cfg = config_manager.load()
        assert cfg.income_regex == ConfigManager.INCOME_REGEX
        assert cfg.expense_regex == ConfigManager.EXPENSE_REGEX
        assert cfg.asset_regex == ConfigManager.ASSET_REGEX
        assert cfg.liability_regex == ConfigManager.LIABILITY_REGEX


# ---------------------------------------------------------------------------
# save() / load() round-trip
# ---------------------------------------------------------------------------


class TestSaveLoadRoundTrip:
    def test_round_trip_preserves_all_fields(self, config_manager: ConfigManager):
        original = AppConfig(
            filename="/tmp/test.journal",
            commodity="$",
            income_regex="revenue",
            expense_regex="cost",
            asset_regex="cash",
            liability_regex="debt",
            historical_cmd="hledger bal --historical",
            expenses_cmd="hledger bal expenses",
            income_expenses_cmd="hledger bal inc exp",
            all_flows_cmd="hledger bal all",
        )

        config_manager.save(original)
        loaded = config_manager.load()

        assert loaded.filename == original.filename
        assert loaded.commodity == original.commodity
        assert loaded.income_regex == original.income_regex
        assert loaded.expense_regex == original.expense_regex
        assert loaded.asset_regex == original.asset_regex
        assert loaded.liability_regex == original.liability_regex
        assert loaded.historical_cmd == original.historical_cmd
        assert loaded.expenses_cmd == original.expenses_cmd
        assert loaded.income_expenses_cmd == original.income_expenses_cmd
        assert loaded.all_flows_cmd == original.all_flows_cmd

    def test_save_returns_path(self, config_manager: ConfigManager):
        cfg = config_manager.load()
        path = config_manager.save(cfg)
        assert isinstance(path, Path)
        assert path.exists()


# ---------------------------------------------------------------------------
# reset()
# ---------------------------------------------------------------------------


class TestReset:
    def test_reset_removes_config_file(self, config_manager: ConfigManager):
        cfg = config_manager.load()
        config_manager.save(cfg)
        assert config_manager.config_path.exists()

        config_manager.reset()
        assert not config_manager.config_path.exists()

    def test_reset_when_no_file_exists(self, config_manager: ConfigManager):
        # Should not raise
        config_manager.reset()
        assert not config_manager.config_path.exists()
