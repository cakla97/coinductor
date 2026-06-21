from __future__ import annotations

from decimal import Decimal

from .models import ConfigIssue, ConfigValidationResult


class ConfigValidator:
    def validate(self, config: dict) -> ConfigValidationResult:
        issues: list[ConfigIssue] = []
        self._validate_portfolio(config, issues)
        self._validate_risk(config, issues)
        self._validate_rebalancing(config, issues)
        self._validate_universes(config, issues)
        self._validate_capital_sourcing(config, issues)
        self._validate_modes(config, issues)
        self._validate_earn(config, issues)
        self._validate_binance(config, issues)
        self._validate_testnet_execution(config, issues)
        self._validate_live_confirm(config, issues)
        self._validate_trading_bankroll(config, issues)
        self._validate_retention(config, issues)
        return ConfigValidationResult(tuple(issues))

    def _validate_portfolio(self, config: dict, issues: list[ConfigIssue]) -> None:
        tracked = set(self._upper_list(config.get("portfolio", {}).get("tracked_assets", [])))
        roles = {asset.upper(): str(role).upper() for asset, role in config.get("portfolio", {}).get("asset_roles", {}).items()}
        for asset in tracked:
            if asset not in roles:
                issues.append(ConfigIssue("WARNING", "portfolio.asset_roles", f"{asset} has no configured role."))
        for asset in roles:
            if asset not in tracked:
                issues.append(ConfigIssue("WARNING", "portfolio.asset_roles", f"{asset} has a role but is not in tracked_assets."))

    def _validate_risk(self, config: dict, issues: list[ConfigIssue]) -> None:
        risk = config.get("risk", {})
        for key in [
            "max_trades_per_day",
            "max_daily_loss_pct",
            "max_weekly_loss_pct",
            "max_position_pct_per_asset",
            "max_total_trading_capital_pct",
            "max_risk_per_trade_pct",
        ]:
            if Decimal(str(risk.get(key, 0))) <= 0:
                issues.append(ConfigIssue("ERROR", f"risk.{key}", "Value must be greater than zero."))

    def _validate_rebalancing(self, config: dict, issues: list[ConfigIssue]) -> None:
        rebalancing = config.get("rebalancing", {})
        allocation = rebalancing.get("target_allocation", {})
        total = sum((Decimal(str(value)) for value in allocation.values()), Decimal("0"))
        if total != Decimal("100"):
            issues.append(ConfigIssue("WARNING", "rebalancing.target_allocation", f"Target allocation sums to {total}%, not 100%."))
        for key in ("min_trade_value_usdt", "max_trade_value_usdt_per_step"):
            if Decimal(str(rebalancing.get(key, 0))) <= 0:
                issues.append(ConfigIssue("ERROR", f"rebalancing.{key}", "Value must be greater than zero."))

    def _validate_universes(self, config: dict, issues: list[ConfigIssue]) -> None:
        tracked = set(self._upper_list(config.get("portfolio", {}).get("tracked_assets", [])))
        strategy_assets = {self._base_asset(symbol) for symbol in config.get("strategy", {}).get("allowed_symbols", [])}
        grid_assets = {self._base_asset(symbol) for symbol in config.get("grid_bot", {}).get("allowed_symbols", [])}
        for asset in sorted(strategy_assets | grid_assets):
            if asset and asset not in tracked:
                issues.append(ConfigIssue("WARNING", "portfolio.tracked_assets", f"{asset} is tradable/grid-enabled but not tracked."))

    def _validate_capital_sourcing(self, config: dict, issues: list[ConfigIssue]) -> None:
        capital = config.get("capital_sourcing", {})
        sources = set(self._upper_list(capital.get("allowed_source_assets", [])))
        protected = set(self._upper_list(capital.get("protected_assets", [])))
        overlap = sorted(sources & protected)
        if overlap:
            issues.append(ConfigIssue("ERROR", "capital_sourcing", f"Assets cannot be both source and protected: {', '.join(overlap)}."))
        if Decimal(str(capital.get("max_source_value_usdt_per_run", 0))) <= 0:
            issues.append(ConfigIssue("ERROR", "capital_sourcing.max_source_value_usdt_per_run", "Value must be greater than zero."))

    def _validate_modes(self, config: dict, issues: list[ConfigIssue]) -> None:
        mode = str(config.get("app", {}).get("mode", "")).upper()
        if mode == "LIVE_AUTO":
            issues.append(ConfigIssue("ERROR", "app.mode", "LIVE_AUTO is outside the current MVP safety envelope."))
        if config.get("earn", {}).get("allow_locked_redeem", False):
            issues.append(ConfigIssue("ERROR", "earn.allow_locked_redeem", "Locked Earn redeem must remain disabled."))

    def _validate_earn(self, config: dict, issues: list[ConfigIssue]) -> None:
        earn = config.get("earn", {})
        allowed = set(self._upper_list(earn.get("allowed_redeem_assets", [])))
        auto = set(self._upper_list(earn.get("auto_redeem_assets", [])))
        invalid_auto = sorted(auto - allowed)
        if invalid_auto:
            issues.append(ConfigIssue("ERROR", "earn.auto_redeem_assets", f"Auto redeem assets must also be in allowed_redeem_assets: {', '.join(invalid_auto)}."))
        for key in ("max_redeem_per_run_usdt", "max_redeem_per_day_usdt", "max_auto_redeem_usdc_per_run", "min_auto_redeem_reserve_usdc"):
            if Decimal(str(earn.get(key, 0))) < 0:
                issues.append(ConfigIssue("ERROR", f"earn.{key}", "Value must be zero or greater."))
        if str(earn.get("redeem_type", "FAST")).upper() not in {"FAST", "NORMAL"}:
            issues.append(ConfigIssue("ERROR", "earn.redeem_type", "Value must be FAST or NORMAL."))

    def _validate_binance(self, config: dict, issues: list[ConfigIssue]) -> None:
        binance = config.get("binance", {})
        for key in ("api_base_url", "testnet_api_base_url"):
            value = str(binance.get(key, ""))
            if not value.startswith("https://"):
                issues.append(ConfigIssue("ERROR", f"binance.{key}", "URL must start with https://."))

    def _validate_testnet_execution(self, config: dict, issues: list[ConfigIssue]) -> None:
        testnet = config.get("testnet_execution", {})
        if Decimal(str(testnet.get("max_quote_amount_usdt", 0))) <= 0:
            issues.append(ConfigIssue("ERROR", "testnet_execution.max_quote_amount_usdt", "Value must be greater than zero."))

    def _validate_live_confirm(self, config: dict, issues: list[ConfigIssue]) -> None:
        live = config.get("live_confirm", {})
        quote_asset = str(live.get("quote_asset", config.get("app", {}).get("base_currency", "USDT"))).upper()
        if quote_asset not in {"USDC", "USDT", "FDUSD"}:
            issues.append(ConfigIssue("ERROR", "live_confirm.quote_asset", "Value must be one of USDC, USDT, or FDUSD."))
        for symbol in self._upper_list(config.get("strategy", {}).get("allowed_symbols", [])):
            if not symbol.endswith(quote_asset):
                issues.append(ConfigIssue("WARNING", "strategy.allowed_symbols", f"{symbol} does not use live_confirm.quote_asset {quote_asset}."))
        if Decimal(str(live.get("max_quote_amount_usdt", 0))) <= 0:
            issues.append(ConfigIssue("ERROR", "live_confirm.max_quote_amount_usdt", "Value must be greater than zero."))
        if Decimal(str(live.get("funding_buffer_usdt", 0))) < 0:
            issues.append(ConfigIssue("ERROR", "live_confirm.funding_buffer_usdt", "Value must be zero or greater."))
        if not live.get("preview_only", True):
            issues.append(ConfigIssue("ERROR", "live_confirm.preview_only", "LIVE_CONFIRM must remain preview-only in this implementation step."))

    def _validate_trading_bankroll(self, config: dict, issues: list[ConfigIssue]) -> None:
        bankroll = config.get("trading_bankroll", {})
        if not bankroll:
            return
        quote_asset = str(bankroll.get("quote_asset", config.get("live_confirm", {}).get("quote_asset", "USDT"))).upper()
        live_quote = str(config.get("live_confirm", {}).get("quote_asset", quote_asset)).upper()
        if quote_asset != live_quote:
            issues.append(ConfigIssue("WARNING", "trading_bankroll.quote_asset", f"Bankroll quote {quote_asset} differs from live_confirm.quote_asset {live_quote}."))
        for key in ("initial_seed_usdc", "max_flexible_earn_draw_usdc_per_run"):
            if Decimal(str(bankroll.get(key, 0))) < 0:
                issues.append(ConfigIssue("ERROR", f"trading_bankroll.{key}", "Value must be zero or greater."))

    def _validate_retention(self, config: dict, issues: list[ConfigIssue]) -> None:
        retention = config.get("retention", {})
        for key in ("keep_database_runs", "keep_research_requests"):
            if int(retention.get(key, 1)) <= 0:
                issues.append(ConfigIssue("ERROR", f"retention.{key}", "Value must be greater than zero."))

    def _upper_list(self, values: list[str]) -> list[str]:
        return [str(value).upper() for value in values]

    def _base_asset(self, symbol: str) -> str:
        symbol = str(symbol).upper()
        for quote in ("USDT", "USDC", "FDUSD", "BTC", "ETH", "BNB"):
            if symbol.endswith(quote):
                return symbol[: -len(quote)]
        return symbol
