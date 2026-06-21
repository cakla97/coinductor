from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .models import GridRecommendation, MarketSnapshot


class GridBotAdvisor:
    def __init__(self, config: dict):
        self.config = config

    def recommend(self, snapshots: list[MarketSnapshot]) -> GridRecommendation:
        grid_config = self.config.get("grid_bot", {})
        if not grid_config.get("enabled", False):
            return self._empty("Grid bot advisor is disabled.")

        allowed_symbols = {str(symbol).upper() for symbol in grid_config.get("allowed_symbols", [])}
        preferred_symbols = [str(symbol).upper() for symbol in grid_config.get("preferred_symbols", grid_config.get("allowed_symbols", []))]
        priority = {symbol: index for index, symbol in enumerate(preferred_symbols)}
        candidates = [
            snapshot
            for snapshot in snapshots
            if snapshot.symbol.upper() in allowed_symbols
            and snapshot.trend_regime in {"NEUTRAL", "RISK_ON"}
            and Decimal("45") <= snapshot.rsi14 <= Decimal("65")
        ]
        if not candidates:
            return self._empty(self._no_candidate_reason(snapshots, allowed_symbols))

        selected = sorted(candidates, key=lambda snapshot: priority.get(snapshot.symbol.upper(), len(priority)))[0]
        range_width_pct = self._bounded_range_width(selected)
        half_width = range_width_pct / Decimal("2") / Decimal("100")
        range_low = self._money(selected.price * (Decimal("1") - half_width))
        range_high = self._money(selected.price * (Decimal("1") + half_width))
        stop_loss_price = self._money(range_low * Decimal("0.97"))
        take_profit_price = self._money(range_high * Decimal("1.03"))
        grid_count = int(grid_config.get("preferred_grid_count", 20))
        grid_count = max(int(grid_config["min_grid_count"]), min(int(grid_config["max_grid_count"]), grid_count))
        investment = Decimal(str(grid_config["default_investment_usdt"]))
        investment = min(investment, Decimal(str(grid_config["max_grid_capital_usdt"])))
        quote_asset = self._quote_asset(selected.symbol)

        steps = (
            "Open Binance Trade-X / Trading Bots and choose Spot Grid.",
            f"Select pair {selected.symbol}.",
            "Use manual parameters rather than AI/auto mode.",
            f"Set lower price to {range_low} and upper price to {range_high}.",
            f"Set grid count to {grid_count} and grid type to arithmetic.",
            f"Allocate {investment} {quote_asset} or less, according to available trading capital.",
            f"Set stop loss around {stop_loss_price} and take profit around {take_profit_price}.",
            f"Do not add extra capital or create another grid while max_active_grid_bots is {grid_config.get('max_active_grid_bots', 1)}.",
            "After creating the bot, run this assistant again to record the new baseline.",
        )

        return GridRecommendation(
            recommended=True,
            symbol=selected.symbol,
            reason=(
                f"{selected.symbol} is liquid, RSI is {selected.rsi14}, trend regime is "
                f"{selected.trend_regime}, and the proposed range width is {range_width_pct}%."
            ),
            range_low=range_low,
            range_high=range_high,
            grid_count=grid_count,
            grid_type="arithmetic",
            investment_usdt=investment,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            manual_steps=steps,
        )

    def _bounded_range_width(self, snapshot: MarketSnapshot) -> Decimal:
        grid_config = self.config["grid_bot"]
        atr_width_pct = (snapshot.atr14 / snapshot.price * Decimal("100") * Decimal("4")).quantize(Decimal("0.1"))
        minimum = Decimal(str(grid_config["min_range_width_pct"]))
        maximum = Decimal(str(grid_config["max_range_width_pct"]))
        return max(minimum, min(maximum, atr_width_pct))

    def _empty(self, reason: str) -> GridRecommendation:
        return GridRecommendation(
            recommended=False,
            symbol=None,
            reason=reason,
            range_low=Decimal("0"),
            range_high=Decimal("0"),
            grid_count=0,
            grid_type="",
            investment_usdt=Decimal("0"),
            stop_loss_price=Decimal("0"),
            take_profit_price=Decimal("0"),
            manual_steps=(),
        )

    def _no_candidate_reason(self, snapshots: list[MarketSnapshot], allowed_symbols: set[str]) -> str:
        observed = [snapshot for snapshot in snapshots if snapshot.symbol.upper() in allowed_symbols]
        if not observed:
            return "No grid-allowed symbols are present in the current market snapshot."
        details = []
        for snapshot in observed:
            details.append(f"{snapshot.symbol}: trend={snapshot.trend_regime}, RSI={snapshot.rsi14}")
        return (
            "No allowed symbol currently has a range-friendly market profile. Grid requires "
            "NEUTRAL/RISK_ON trend and RSI between 45 and 65. Observed: "
            + "; ".join(details)
        )

    def _money(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _quote_asset(self, symbol: str) -> str:
        symbol = symbol.upper()
        for quote in ("USDC", "USDT", "FDUSD", "BTC", "ETH", "BNB"):
            if symbol.endswith(quote):
                return quote
        return "USDT"
