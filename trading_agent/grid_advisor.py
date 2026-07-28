from __future__ import annotations

from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

from .decimal_utils import money
from .manual_steps import ManualStep, render_manual_steps
from .models import (
    ActiveStrategiesReport,
    GridCandidateAssessment,
    GridRecommendation,
    LiveRiskState,
    MarketResearchReport,
    MarketSnapshot,
    SymbolMarketResearch,
)


class GridBotAdvisor:
    def __init__(self, config: dict):
        self.config = config

    def recommend(
        self,
        snapshots: list[MarketSnapshot],
        market_research: MarketResearchReport,
        active_strategies: ActiveStrategiesReport,
        risk_state: LiveRiskState,
        portfolio_value_usdt: Decimal,
    ) -> GridRecommendation:
        grid_config = self.config.get("grid_bot", {})
        if not grid_config.get("enabled", False):
            return self._empty("DISABLED", "Grid bot advisor is disabled.")

        allowed = {str(symbol).upper() for symbol in grid_config.get("allowed_symbols", [])}
        research_by_symbol = {item.symbol.upper(): item for item in market_research.symbols}
        candidates = [
            self._candidate(snapshot, research_by_symbol.get(snapshot.symbol.upper()))
            for snapshot in snapshots
            if snapshot.symbol.upper() in allowed
        ]
        if not candidates:
            return self._empty("REJECTED", "No grid-allowed symbols are present in the current market snapshot.")

        selected_snapshot, selected_research, score, market_status, reasons = max(
            candidates,
            key=lambda item: (item[2], self._preference_score(item[0].symbol)),
        )
        investment = self._investment(portfolio_value_usdt)
        range_low, range_high, range_width_pct = self._range(selected_snapshot, selected_research)
        grid_count = self._grid_count(investment)
        spacing_pct = range_width_pct / Decimal(grid_count) if grid_count > 0 else Decimal("0")
        quote_per_grid = investment / Decimal(grid_count) if grid_count > 0 else Decimal("0")
        stop_buffer_pct = Decimal(str(grid_config.get("stop_loss_buffer_pct", "3"))) / Decimal("100")
        take_buffer_pct = Decimal(str(grid_config.get("take_profit_buffer_pct", "3"))) / Decimal("100")
        stop_loss = self._money(range_low * (Decimal("1") - stop_buffer_pct))
        take_profit = self._money(range_high * (Decimal("1") + take_buffer_pct))

        blockers = self._deployment_blockers(
            market_status=market_status,
            active_strategies=active_strategies,
            risk_state=risk_state,
            quote_per_grid=quote_per_grid,
        )
        deployment_allowed = not blockers
        recommended = market_status == "SUITABLE" and deployment_allowed
        reason = (
            f"{selected_snapshot.symbol} scored {score:.1f}/100 for a range strategy: "
            + "; ".join(reasons)
            + "."
        )
        if blockers:
            reason += " Deployment blockers: " + "; ".join(blockers) + "."

        quote_asset = self._quote_asset(selected_snapshot.symbol)
        assessments = tuple(
            GridCandidateAssessment(
                symbol=snapshot.symbol,
                score=self._one_decimal(candidate_score),
                market_status=status,
                reason="; ".join(candidate_reasons),
            )
            for snapshot, _, candidate_score, status, candidate_reasons in sorted(
                candidates,
                key=lambda item: item[2],
                reverse=True,
            )
        )
        steps = self._manual_steps(
            selected_snapshot.symbol,
            range_low,
            range_high,
            grid_count,
            investment,
            quote_asset,
            stop_loss,
            take_profit,
            deployment_allowed,
        )
        return GridRecommendation(
            recommended=recommended,
            market_status=market_status,
            deployment_allowed=deployment_allowed,
            symbol=selected_snapshot.symbol,
            reason=reason,
            score=self._one_decimal(score),
            range_low=range_low,
            range_high=range_high,
            range_width_pct=self._one_decimal(range_width_pct),
            grid_count=grid_count,
            grid_type="arithmetic",
            estimated_quote_per_grid=self._money(quote_per_grid),
            estimated_grid_spacing_pct=self._two_decimals(spacing_pct),
            investment_usdt=self._money(investment),
            stop_loss_price=stop_loss,
            take_profit_price=take_profit,
            blockers=tuple(blockers),
            candidate_assessments=assessments,
            manual_steps=render_manual_steps(steps),
            manual_step_specs=steps,
        )

    def _candidate(
        self,
        snapshot: MarketSnapshot,
        research: SymbolMarketResearch | None,
    ) -> tuple[MarketSnapshot, SymbolMarketResearch | None, Decimal, str, list[str]]:
        config = self.config["grid_bot"]
        score = Decimal("0")
        reasons: list[str] = []
        if snapshot.trend_regime == "NEUTRAL":
            score += Decimal("35")
            reasons.append("neutral trend")
        elif snapshot.trend_regime == "RISK_ON":
            score += Decimal("20")
            reasons.append("controlled risk-on trend")
        else:
            reasons.append("risk-off trend")

        target_rsi = Decimal(str(config.get("target_rsi14", "52")))
        rsi_distance = abs(snapshot.rsi14 - target_rsi)
        score += max(Decimal("0"), Decimal("25") - rsi_distance * Decimal("1.5"))
        reasons.append(f"RSI14 {snapshot.rsi14:.1f}")

        atr_pct = snapshot.atr14 / snapshot.price * Decimal("100") if snapshot.price > 0 else Decimal("0")
        min_atr = Decimal(str(config.get("min_atr_pct", "1.0")))
        max_atr = Decimal(str(config.get("max_atr_pct", "6.0")))
        if min_atr <= atr_pct <= max_atr:
            score += Decimal("20")
            reasons.append(f"ATR {atr_pct:.2f}% is tradable")
        else:
            reasons.append(f"ATR {atr_pct:.2f}% is outside preferred range")

        ema_distance = abs(snapshot.price - snapshot.ema200) / snapshot.ema200 * Decimal("100") if snapshot.ema200 else Decimal("100")
        max_ema_distance = Decimal(str(config.get("max_abs_ema200_distance_pct", "12")))
        if ema_distance <= max_ema_distance:
            score += Decimal("10")
            reasons.append(f"price is {ema_distance:.2f}% from EMA200")
        else:
            reasons.append(f"price is {ema_distance:.2f}% from EMA200")

        if research is not None:
            max_trend = Decimal(str(config.get("max_abs_7d_return_pct", "10")))
            if research.return_7d_pct is not None and abs(research.return_7d_pct) <= max_trend:
                score += Decimal("10")
                reasons.append(f"7d move {research.return_7d_pct:+.2f}% is range-compatible")
            elif research.return_7d_pct is not None:
                reasons.append(f"7d move {research.return_7d_pct:+.2f}% is strongly directional")
        else:
            reasons.append("multi-timeframe research unavailable")

        suitable_score = Decimal(str(config.get("suitable_score", "70")))
        watch_score = Decimal(str(config.get("watch_score", "45")))
        hard_reject = (
            snapshot.trend_regime == "RISK_OFF"
            or snapshot.rsi14 < Decimal(str(config.get("min_rsi14", "40")))
            or snapshot.rsi14 > Decimal(str(config.get("max_rsi14", "65")))
            or ema_distance > max_ema_distance
        )
        if not hard_reject and score >= suitable_score:
            status = "SUITABLE"
        elif score >= watch_score:
            status = "WATCH"
        else:
            status = "REJECTED"
        return snapshot, research, min(score, Decimal("100")), status, reasons

    def _range(
        self,
        snapshot: MarketSnapshot,
        research: SymbolMarketResearch | None,
    ) -> tuple[Decimal, Decimal, Decimal]:
        config = self.config["grid_bot"]
        atr_pct = snapshot.atr14 / snapshot.price * Decimal("100") if snapshot.price else Decimal("0")
        width = atr_pct * Decimal(str(config.get("atr_range_multiplier", "4")))
        width = max(Decimal(str(config["min_range_width_pct"])), min(Decimal(str(config["max_range_width_pct"])), width))
        half = width / Decimal("200")
        volatility_low = snapshot.price * (Decimal("1") - half)
        volatility_high = snapshot.price * (Decimal("1") + half)
        max_half = Decimal(str(config["max_range_width_pct"])) / Decimal("200")
        absolute_low = snapshot.price * (Decimal("1") - max_half)
        absolute_high = snapshot.price * (Decimal("1") + max_half)

        lower_candidates = [volatility_low, snapshot.ema50]
        upper_candidates = [volatility_high, snapshot.ema20]
        if research is not None and research.support_30d is not None:
            lower_candidates.append(research.support_30d)
        if research is not None and research.resistance_30d is not None:
            upper_candidates.append(research.resistance_30d)
        range_low = max(absolute_low, min(lower_candidates))
        range_high = min(absolute_high, max(upper_candidates))
        if range_low >= snapshot.price:
            range_low = volatility_low
        if range_high <= snapshot.price:
            range_high = volatility_high
        actual_width = (range_high - range_low) / snapshot.price * Decimal("100")
        return self._money(range_low), self._money(range_high), actual_width

    def _investment(self, portfolio_value_usdt: Decimal) -> Decimal:
        config = self.config["grid_bot"]
        default = Decimal(str(config["default_investment_usdt"]))
        max_absolute = Decimal(str(config["max_grid_capital_usdt"]))
        max_portfolio = portfolio_value_usdt * Decimal(str(config.get("max_grid_capital_pct", "100"))) / Decimal("100")
        return max(Decimal("0"), min(default, max_absolute, max_portfolio))

    def _grid_count(self, investment: Decimal) -> int:
        config = self.config["grid_bot"]
        minimum = int(config["min_grid_count"])
        maximum = int(config["max_grid_count"])
        preferred = int(config.get("preferred_grid_count", minimum))
        min_quote = Decimal(str(config.get("min_quote_per_grid_usdt", "2.5")))
        capital_cap = int((investment / min_quote).to_integral_value(rounding=ROUND_DOWN)) if min_quote > 0 else maximum
        return max(minimum, min(maximum, preferred, capital_cap))

    def _deployment_blockers(
        self,
        market_status: str,
        active_strategies: ActiveStrategiesReport,
        risk_state: LiveRiskState,
        quote_per_grid: Decimal,
    ) -> list[str]:
        config = self.config["grid_bot"]
        blockers: list[str] = []
        if market_status != "SUITABLE":
            blockers.append(f"market status is {market_status}, not SUITABLE")
        if len(active_strategies.grid_bots) >= int(config.get("max_active_grid_bots", 1)):
            blockers.append("maximum active grid bot count is already reached")
        if risk_state.kill_switch_active:
            blockers.append("live risk kill switch is active")
        if risk_state.cooldown_active:
            blockers.append("loss cooldown is active")
        min_quote = Decimal(str(config.get("min_quote_per_grid_usdt", "2.5")))
        if quote_per_grid < min_quote:
            blockers.append(f"estimated quote per grid {quote_per_grid:.2f} is below configured {min_quote:.2f}")
        return blockers

    def _manual_steps(
        self,
        symbol: str,
        range_low: Decimal,
        range_high: Decimal,
        grid_count: int,
        investment: Decimal,
        quote_asset: str,
        stop_loss: Decimal,
        take_profit: Decimal,
        deployment_allowed: bool,
    ) -> tuple[ManualStep, ...]:
        # A blocked grid deliberately loses its parameters. Its blockers are
        # market conditions the reader cannot clear, and the range is derived
        # from today's prices - by the time the market turns SUITABLE those
        # numbers would be wrong, so offering them would be a trap.
        if not deployment_allowed:
            return (
                ManualStep("grid_blocked_do_not_create"),
                ManualStep("grid_blocked_rerun"),
            )
        return (
            ManualStep("bots_manual_because_no_api"),
            ManualStep("grid_open_menu"),
            ManualStep("grid_select_symbol", {"symbol": symbol}),
            ManualStep("grid_set_range", {"low": str(range_low), "high": str(range_high)}),
            ManualStep("grid_set_count", {"count": str(grid_count)}),
            ManualStep(
                "grid_set_investment",
                {"quote": quote_asset, "investment": str(investment)},
            ),
            ManualStep("grid_trading_up_off"),
            ManualStep(
                "grid_set_tpsl",
                {"stop_loss": str(stop_loss), "take_profit": str(take_profit)},
            ),
            ManualStep("grid_sell_all_base"),
            ManualStep("grid_review_before_confirm"),
            ManualStep("grid_register_locally"),
            ManualStep("grid_rerun_to_monitor"),
        )

    def _preference_score(self, symbol: str) -> int:
        preferred = [str(item).upper() for item in self.config["grid_bot"].get("preferred_symbols", [])]
        try:
            return len(preferred) - preferred.index(symbol.upper())
        except ValueError:
            return 0

    def _empty(self, market_status: str, reason: str) -> GridRecommendation:
        return GridRecommendation(
            recommended=False,
            market_status=market_status,
            deployment_allowed=False,
            symbol=None,
            reason=reason,
            score=Decimal("0"),
            range_low=Decimal("0"),
            range_high=Decimal("0"),
            range_width_pct=Decimal("0"),
            grid_count=0,
            grid_type="",
            estimated_quote_per_grid=Decimal("0"),
            estimated_grid_spacing_pct=Decimal("0"),
            investment_usdt=Decimal("0"),
            stop_loss_price=Decimal("0"),
            take_profit_price=Decimal("0"),
            blockers=(reason,),
            candidate_assessments=(),
            manual_steps=(),
            manual_step_specs=(),
        )

    def _money(self, value: Decimal) -> Decimal:
        return money(value)

    def _one_decimal(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    def _two_decimals(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _quote_asset(self, symbol: str) -> str:
        symbol = symbol.upper()
        for quote in ("USDC", "USDT", "FDUSD", "BTC", "ETH", "BNB"):
            if symbol.endswith(quote):
                return quote
        return "USDT"
