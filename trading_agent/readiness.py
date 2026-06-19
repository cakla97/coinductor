from __future__ import annotations

import os

from .binance_client import BinanceApiError, BinanceClient
from .config import AppConfig
from .config_validator import ConfigValidator
from .models import ReadinessCheck, ReadinessReport
from .storage import Storage


class ReadinessChecker:
    def __init__(self, config: AppConfig):
        self.config = config

    def check(self) -> ReadinessReport:
        checks: list[ReadinessCheck] = []
        checks.extend(self._config_checks())
        checks.extend(self._mainnet_key_checks())
        checks.extend(self._testnet_checks())
        checks.extend(self._execution_guard_checks())
        return ReadinessReport(tuple(checks))

    def _config_checks(self) -> list[ReadinessCheck]:
        validation = ConfigValidator().validate(self.config.raw)
        if validation.has_errors:
            details = "; ".join(f"{issue.path}: {issue.message}" for issue in validation.issues if issue.severity == "ERROR")
            return [ReadinessCheck("BLOCK", "Config validation", details)]
        warnings = [issue for issue in validation.issues if issue.severity == "WARNING"]
        if warnings:
            details = "; ".join(f"{issue.path}: {issue.message}" for issue in warnings)
            return [ReadinessCheck("WARN", "Config validation", details)]
        return [ReadinessCheck("PASS", "Config validation", "No config errors or warnings.")]

    def _mainnet_key_checks(self) -> list[ReadinessCheck]:
        checks: list[ReadinessCheck] = []
        try:
            BinanceClient(self.config.raw).assert_read_only_permissions()
            checks.append(ReadinessCheck("PASS", "Mainnet read-only key", "Current Binance mainnet key is read-only."))
        except BinanceApiError as exc:
            checks.append(ReadinessCheck("BLOCK", "Mainnet read-only key", str(exc)))

        live_key = os.getenv("BINANCE_LIVE_TRADE_API_KEY", "")
        live_secret = os.getenv("BINANCE_LIVE_TRADE_API_SECRET", "")
        if not live_key or not live_secret:
            checks.append(
                ReadinessCheck(
                    "BLOCK",
                    "Separate mainnet trading key",
                    "BINANCE_LIVE_TRADE_API_KEY and BINANCE_LIVE_TRADE_API_SECRET are not configured. This is expected before LIVE_CONFIRM.",
                )
            )
        elif live_key == os.getenv("BINANCE_API_KEY", ""):
            checks.append(ReadinessCheck("BLOCK", "Separate mainnet trading key", "Live trading key must not reuse the read-only key."))
        else:
            checks.append(ReadinessCheck("PASS", "Separate mainnet trading key", "Separate live trading key env vars are present."))
        return checks

    def _testnet_checks(self) -> list[ReadinessCheck]:
        checks: list[ReadinessCheck] = []
        try:
            BinanceClient(self.config.raw, use_testnet=True).testnet_account_ping()
            checks.append(ReadinessCheck("PASS", "Spot Testnet account", "Spot Testnet account is reachable."))
        except BinanceApiError as exc:
            checks.append(ReadinessCheck("BLOCK", "Spot Testnet account", str(exc)))

        summary = Storage(self.config.database_path).get_testnet_position_summary()
        if summary.open_positions:
            checks.append(ReadinessCheck("WARN", "Spot Testnet cycles", summary.summary))
        elif summary.closed_positions:
            checks.append(ReadinessCheck("PASS", "Spot Testnet cycles", summary.summary))
        else:
            checks.append(ReadinessCheck("BLOCK", "Spot Testnet cycles", "No completed Spot Testnet BUY/SELL cycle found."))

        symbol_failures: list[str] = []
        for symbol in self.config.allowed_symbols:
            try:
                rules = BinanceClient(self.config.raw, use_testnet=True).get_symbol_rules(symbol)
            except BinanceApiError as exc:
                symbol_failures.append(f"{symbol}: {exc}")
                continue
            if rules.status != "TRADING":
                symbol_failures.append(f"{symbol}: status {rules.status}")
            elif rules.quote_asset != "USDT":
                symbol_failures.append(f"{symbol}: quote asset {rules.quote_asset}")
        if symbol_failures:
            checks.append(ReadinessCheck("BLOCK", "Spot Testnet symbol filters", "; ".join(symbol_failures)))
        else:
            checks.append(ReadinessCheck("PASS", "Spot Testnet symbol filters", "Allowed symbols are present and TRADING on Spot Testnet."))
        return checks

    def _execution_guard_checks(self) -> list[ReadinessCheck]:
        checks: list[ReadinessCheck] = []
        app_mode = self.config.mode
        if app_mode == "LIVE_AUTO":
            checks.append(ReadinessCheck("BLOCK", "App mode", "LIVE_AUTO is outside the MVP safety envelope."))
        elif app_mode == "LIVE_CONFIRM":
            checks.append(ReadinessCheck("WARN", "App mode", "LIVE_CONFIRM selected, but live execution is not implemented yet."))
        else:
            checks.append(ReadinessCheck("PASS", "App mode", f"{app_mode} is non-live."))

        if not self.config.raw.get("rebalancing", {}).get("preview_only", True):
            checks.append(ReadinessCheck("BLOCK", "Rebalancing guard", "rebalancing.preview_only must remain true before LIVE_CONFIRM."))
        else:
            checks.append(ReadinessCheck("PASS", "Rebalancing guard", "Rebalancing is preview-only."))

        if self.config.raw.get("earn", {}).get("execute_real_redeem", False):
            checks.append(ReadinessCheck("BLOCK", "Earn redeem guard", "execute_real_redeem must remain false before LIVE_CONFIRM."))
        else:
            checks.append(ReadinessCheck("PASS", "Earn redeem guard", "Real Earn redeem is disabled."))

        if int(self.config.raw.get("retention", {}).get("keep_database_runs", 0)) <= 0:
            checks.append(ReadinessCheck("BLOCK", "Retention guard", "Database retention must keep at least one run."))
        else:
            checks.append(ReadinessCheck("PASS", "Retention guard", "Database and report retention are configured."))
        return checks
