from __future__ import annotations

from decimal import Decimal

from .models import ConfigIssue, ConfigValidationResult


class ConfigValidator:
    def validate(self, config: dict) -> ConfigValidationResult:
        issues: list[ConfigIssue] = []
        self._validate_portfolio(config, issues)
        self._validate_risk(config, issues)
        self._validate_consensus(config, issues)
        self._validate_rebalancing(config, issues)
        self._validate_rebalancing_bot(config, issues)
        self._validate_universes(config, issues)
        self._validate_grid_bot(config, issues)
        self._validate_capital_sourcing(config, issues)
        self._validate_dust_sourcing(config, issues)
        self._validate_modes(config, issues)
        self._validate_earn(config, issues)
        self._validate_binance(config, issues)
        self._validate_testnet_execution(config, issues)
        self._validate_live_confirm(config, issues)
        self._validate_trading_bankroll(config, issues)
        self._validate_ai_memory(config, issues)
        self._validate_market_research(config, issues)
        self._validate_shadow_evaluation(config, issues)
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

    def _validate_consensus(self, config: dict, issues: list[ConfigIssue]) -> None:
        consensus = config.get("consensus", {})
        if not consensus:
            return
        min_rsi = Decimal(str(consensus.get("min_rsi14", 0)))
        max_rsi = Decimal(str(consensus.get("max_rsi14", 0)))
        if min_rsi < 0 or max_rsi > 100 or min_rsi >= max_rsi:
            issues.append(
                ConfigIssue(
                    "ERROR",
                    "consensus",
                    "RSI bounds must satisfy 0 <= min_rsi14 < max_rsi14 <= 100.",
                )
            )

    def _validate_rebalancing(self, config: dict, issues: list[ConfigIssue]) -> None:
        rebalancing = config.get("rebalancing", {})
        target_mode = str(rebalancing.get("target_mode", "static")).lower()
        if target_mode not in {"static", "baseline_current"}:
            issues.append(ConfigIssue("ERROR", "rebalancing.target_mode", "Value must be static or baseline_current."))
        allocation = rebalancing.get("target_allocation", {})
        total = sum((Decimal(str(value)) for value in allocation.values()), Decimal("0"))
        if target_mode == "static" and total != Decimal("100"):
            issues.append(ConfigIssue("WARNING", "rebalancing.target_allocation", f"Target allocation sums to {total}%, not 100%."))
        for key in ("threshold_pct", "drift_threshold_pct", "min_trade_value_usdt", "max_trade_value_usdt_per_step"):
            if Decimal(str(rebalancing.get(key, 0))) <= 0:
                issues.append(ConfigIssue("ERROR", f"rebalancing.{key}", "Value must be greater than zero."))
        for key in ("max_trade_pct_per_asset", "min_remaining_pct_per_asset"):
            value = Decimal(str(rebalancing.get(key, 0)))
            if value <= 0 or value > 100:
                issues.append(ConfigIssue("ERROR", f"rebalancing.{key}", "Value must be greater than zero and at most 100."))
        if Decimal(str(rebalancing.get("min_remaining_value_usdt_per_asset", 0))) < 0:
            issues.append(ConfigIssue("ERROR", "rebalancing.min_remaining_value_usdt_per_asset", "Value must be zero or greater."))

    def _validate_rebalancing_bot(self, config: dict, issues: list[ConfigIssue]) -> None:
        bot = config.get("rebalancing_bot", {})
        if not bot:
            return
        if str(bot.get("mode", "")).upper() not in {"THRESHOLD", "PERIODIC"}:
            issues.append(ConfigIssue("ERROR", "rebalancing_bot.mode", "Value must be THRESHOLD or PERIODIC."))
        allowed = self._upper_list(bot.get("allowed_assets", []))
        if len(set(allowed)) < 2:
            issues.append(ConfigIssue("ERROR", "rebalancing_bot.allowed_assets", "At least two unique assets are required."))
        for key in ("threshold_pct", "min_asset_value_usdt", "min_investment_usdt", "max_investment_usdt", "max_portfolio_pct"):
            if Decimal(str(bot.get(key, 0))) <= 0:
                issues.append(ConfigIssue("ERROR", f"rebalancing_bot.{key}", "Value must be greater than zero."))
        if Decimal(str(bot.get("min_investment_usdt", 0))) > Decimal(str(bot.get("max_investment_usdt", 0))):
            issues.append(ConfigIssue("ERROR", "rebalancing_bot", "min_investment_usdt cannot exceed max_investment_usdt."))

    def _validate_universes(self, config: dict, issues: list[ConfigIssue]) -> None:
        tracked = set(self._upper_list(config.get("portfolio", {}).get("tracked_assets", [])))
        strategy_assets = {self._base_asset(symbol) for symbol in config.get("strategy", {}).get("allowed_symbols", [])}
        grid_assets = {self._base_asset(symbol) for symbol in config.get("grid_bot", {}).get("allowed_symbols", [])}
        for asset in sorted(strategy_assets | grid_assets):
            if asset and asset not in tracked:
                issues.append(ConfigIssue("WARNING", "portfolio.tracked_assets", f"{asset} is tradable/grid-enabled but not tracked."))

    def _validate_grid_bot(self, config: dict, issues: list[ConfigIssue]) -> None:
        grid = config.get("grid_bot", {})
        allowed = set(self._upper_list(grid.get("allowed_symbols", [])))
        preferred = set(self._upper_list(grid.get("preferred_symbols", [])))
        outside_allowed = sorted(preferred - allowed)
        if outside_allowed:
            issues.append(ConfigIssue("ERROR", "grid_bot.preferred_symbols", f"Preferred symbols must also be allowed: {', '.join(outside_allowed)}."))
        for key in ("max_grid_capital_usdt", "max_grid_capital_pct", "default_investment_usdt"):
            if Decimal(str(grid.get(key, 0))) <= 0:
                issues.append(ConfigIssue("ERROR", f"grid_bot.{key}", "Value must be greater than zero."))
        for key in (
            "min_quote_per_grid_usdt",
            "min_atr_pct",
            "max_atr_pct",
            "max_abs_ema200_distance_pct",
            "max_abs_7d_return_pct",
            "suitable_score",
            "watch_score",
            "atr_range_multiplier",
        ):
            if Decimal(str(grid.get(key, 0))) <= 0:
                issues.append(ConfigIssue("ERROR", f"grid_bot.{key}", "Value must be greater than zero."))
        min_rsi = Decimal(str(grid.get("min_rsi14", 0)))
        target_rsi = Decimal(str(grid.get("target_rsi14", 0)))
        max_rsi = Decimal(str(grid.get("max_rsi14", 0)))
        if not Decimal("0") <= min_rsi < target_rsi < max_rsi <= Decimal("100"):
            issues.append(
                ConfigIssue(
                    "ERROR",
                    "grid_bot",
                    "RSI values must satisfy 0 <= min_rsi14 < target_rsi14 < max_rsi14 <= 100.",
                )
            )
        if Decimal(str(grid.get("watch_score", 0))) >= Decimal(str(grid.get("suitable_score", 0))):
            issues.append(ConfigIssue("ERROR", "grid_bot.watch_score", "Value must be below suitable_score."))

    def _validate_capital_sourcing(self, config: dict, issues: list[ConfigIssue]) -> None:
        capital = config.get("capital_sourcing", {})
        sources = set(self._upper_list(capital.get("allowed_source_assets", [])))
        protected = set(self._upper_list(capital.get("protected_assets", [])))
        overlap = sorted(sources & protected)
        if overlap:
            issues.append(ConfigIssue("ERROR", "capital_sourcing", f"Assets cannot be both source and protected: {', '.join(overlap)}."))
        if Decimal(str(capital.get("max_source_value_usdt_per_run", 0))) <= 0:
            issues.append(ConfigIssue("ERROR", "capital_sourcing.max_source_value_usdt_per_run", "Value must be greater than zero."))
        for key in ("max_source_pct_per_asset", "max_total_source_pct_per_run", "min_remaining_pct_per_asset"):
            value = Decimal(str(capital.get(key, 0)))
            if value <= 0 or value > 100:
                issues.append(ConfigIssue("ERROR", f"capital_sourcing.{key}", "Value must be greater than zero and at most 100."))
        if Decimal(str(capital.get("min_remaining_value_usdt_per_asset", 0))) < 0:
            issues.append(ConfigIssue("ERROR", "capital_sourcing.min_remaining_value_usdt_per_asset", "Value must be zero or greater."))

    def _validate_dust_sourcing(self, config: dict, issues: list[ConfigIssue]) -> None:
        dust = config.get("dust_sourcing", {})
        if not dust:
            return
        for key in ("max_convert_value_usdt_per_run", "min_convert_value_usdt_per_asset"):
            if Decimal(str(dust.get(key, 0))) < 0:
                issues.append(ConfigIssue("ERROR", f"dust_sourcing.{key}", "Value must be zero or greater."))
        max_pct = Decimal(str(dust.get("max_convert_pct_per_asset", 0)))
        if max_pct <= 0 or max_pct > 100:
            issues.append(ConfigIssue("ERROR", "dust_sourcing.max_convert_pct_per_asset", "Value must be greater than zero and at most 100."))

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

    def _validate_ai_memory(self, config: dict, issues: list[ConfigIssue]) -> None:
        memory = config.get("ai_memory", {})
        if not memory:
            return
        max_cycles = int(memory.get("max_closed_cycles", 0))
        if max_cycles <= 0 or max_cycles > 50:
            issues.append(ConfigIssue("ERROR", "ai_memory.max_closed_cycles", "Value must be between 1 and 50."))
        min_patterns = int(memory.get("min_cycles_for_pattern_inference", 3))
        if min_patterns <= 0 or min_patterns > max_cycles:
            issues.append(
                ConfigIssue(
                    "ERROR",
                    "ai_memory.min_cycles_for_pattern_inference",
                    "Value must be greater than zero and at most max_closed_cycles.",
                )
            )

    def _validate_market_research(self, config: dict, issues: list[ConfigIssue]) -> None:
        research = config.get("market_research", {})
        if not research:
            return
        quote_asset = str(research.get("breadth_quote_asset", "")).upper()
        if quote_asset not in {"USDC", "USDT", "FDUSD"}:
            issues.append(
                ConfigIssue(
                    "ERROR",
                    "market_research.breadth_quote_asset",
                    "Value must be one of USDC, USDT, or FDUSD.",
                )
            )
        if Decimal(str(research.get("min_quote_volume_24h", 0))) < 0:
            issues.append(
                ConfigIssue(
                    "ERROR",
                    "market_research.min_quote_volume_24h",
                    "Value must be zero or greater.",
                )
            )
        max_movers = int(research.get("max_movers", 0))
        if max_movers <= 0 or max_movers > 20:
            issues.append(ConfigIssue("ERROR", "market_research.max_movers", "Value must be between 1 and 20."))
        interval = str(research.get("multi_timeframe_interval", ""))
        if interval not in {"1h", "2h", "4h", "6h", "8h", "12h", "1d"}:
            issues.append(
                ConfigIssue(
                    "ERROR",
                    "market_research.multi_timeframe_interval",
                    "Use a supported Binance interval between 1h and 1d.",
                )
            )
        kline_limit = int(research.get("kline_limit", 0))
        if kline_limit < 180 or kline_limit > 1000:
            issues.append(
                ConfigIssue(
                    "ERROR",
                    "market_research.kline_limit",
                    "Value must be between 180 and 1000 to cover the configured 30-day context.",
                )
            )

    def _validate_shadow_evaluation(self, config: dict, issues: list[ConfigIssue]) -> None:
        shadow = config.get("shadow_evaluation", {})
        if not shadow:
            return
        horizon = int(shadow.get("horizon_hours", 0))
        if horizon <= 0 or horizon > 24 * 30:
            issues.append(
                ConfigIssue(
                    "ERROR",
                    "shadow_evaluation.horizon_hours",
                    "Value must be between 1 hour and 30 days.",
                )
            )
        min_interval = int(shadow.get("min_signal_interval_hours", 0))
        if min_interval <= 0 or min_interval > horizon:
            issues.append(
                ConfigIssue(
                    "ERROR",
                    "shadow_evaluation.min_signal_interval_hours",
                    "Value must be greater than zero and at most horizon_hours.",
                )
            )
        threshold = Decimal(str(shadow.get("decision_threshold_pct", 0)))
        if threshold < 0 or threshold > 20:
            issues.append(
                ConfigIssue(
                    "ERROR",
                    "shadow_evaluation.decision_threshold_pct",
                    "Value must be between 0 and 20 percent.",
                )
            )

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
