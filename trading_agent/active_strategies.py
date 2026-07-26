from __future__ import annotations

from datetime import datetime, UTC
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from .grid_registry import GridRegistry
from .models import ActiveGridBot, ActiveGridEvaluation, ActiveRebalancingBot, ActiveRebalancingEvaluation, ActiveStrategiesReport, MarketSnapshot
from .rebalancing_registry import RebalancingRegistry


class ActiveStrategiesTracker:
    def __init__(self, config: dict):
        self.config = config

    def evaluate(
        self,
        snapshots: list[MarketSnapshot],
        asset_prices: dict[str, Decimal] | None = None,
    ) -> ActiveStrategiesReport:
        strategy_config = self.config.get("active_strategies", {})
        if not strategy_config.get("enabled", True):
            return ActiveStrategiesReport(enabled=False, grid_bots=(), summary="Active strategy tracking is disabled.", rebalancing_bots=())

        path = Path(str(self.config.get("app", {}).get("active_strategies_path", "state/active_strategies.toml")))
        if not path.exists():
            return ActiveStrategiesReport(
                enabled=True,
                grid_bots=(),
                summary=(
                    f"No active strategies file found at {path}. Register a manually created Binance Grid "
                    "or Rebalancing Bot with the matching CLI registration command."
                ),
                rebalancing_bots=(),
            )

        bots = GridRegistry(self.config).list_bots()
        prices = {snapshot.symbol: snapshot.price for snapshot in snapshots}
        evaluations = tuple(self._evaluate_bot(bot, prices.get(bot.symbol)) for bot in bots if bot.status.upper() == "ACTIVE")
        rebalancing = RebalancingRegistry(self.config).list_bots()
        asset_price_map = {str(asset).upper(): price for asset, price in (asset_prices or {}).items()}
        rebalancing_evaluations = tuple(
            self._evaluate_rebalancing_bot(bot, asset_price_map)
            for bot in rebalancing
            if bot.status.upper() == "ACTIVE"
        )
        urgent_grids = [
            item
            for item in evaluations
            if item.state in {"STOP_LOSS_BREACH", "TAKE_PROFIT_REACHED", "RUNTIME_EXPIRED", "BELOW_RANGE", "ABOVE_RANGE"}
        ]
        urgent_rebalancing = [item for item in rebalancing_evaluations if item.state in {"THRESHOLD_REACHED", "UNKNOWN_PRICE"}]
        if urgent_grids or urgent_rebalancing:
            summary = (
                f"{len(urgent_grids)} grid and {len(urgent_rebalancing)} rebalancing bot(s) need lifecycle review."
            )
        else:
            summary = (
                f"Tracking {len(evaluations)} active grid and "
                f"{len(rebalancing_evaluations)} active rebalancing bot(s)."
            )
        return ActiveStrategiesReport(
            enabled=True,
            grid_bots=evaluations,
            summary=summary,
            rebalancing_bots=rebalancing_evaluations,
        )

    def _evaluate_bot(self, bot: ActiveGridBot, price: Decimal | None) -> ActiveGridEvaluation:
        age_days = self._age_days(bot.created_at)
        if price is None:
            return ActiveGridEvaluation(
                bot,
                None,
                "UNKNOWN_PRICE",
                None,
                None,
                age_days,
                "Current symbol price is unavailable; review manually.",
            )

        distance_lower = self._pct(price - bot.range_low, bot.range_low)
        distance_upper = self._pct(bot.range_high - price, bot.range_high)
        warn_pct = Decimal(str(self.config.get("active_strategies", {}).get("warn_near_range_pct", 5)))
        max_runtime = Decimal(str(self.config.get("grid_bot", {}).get("max_runtime_days", 14)))

        if bot.stop_loss_price > 0 and price <= bot.stop_loss_price:
            state = "STOP_LOSS_BREACH"
            recommendation = "Price reached the registered stop-loss. Review and stop the Binance grid immediately."
        elif bot.take_profit_price > 0 and price >= bot.take_profit_price:
            state = "TAKE_PROFIT_REACHED"
            recommendation = "Price reached the registered take-profit. Review closing the grid and securing proceeds."
        elif age_days is not None and age_days >= max_runtime:
            state = "RUNTIME_EXPIRED"
            recommendation = f"Grid age reached {age_days:.1f} days, above the configured {max_runtime} days. Review closure or recreation."
        elif price < bot.range_low:
            state = "BELOW_RANGE"
            recommendation = "Price is below grid range. Review whether to stop, widen, or recreate the grid."
        elif price > bot.range_high:
            state = "ABOVE_RANGE"
            recommendation = "Price is above grid range. Review whether to take profit, stop, or recreate the grid."
        elif distance_lower <= warn_pct:
            state = "NEAR_LOWER"
            recommendation = "Price is close to the lower grid boundary. Monitor downside and stop conditions."
        elif distance_upper <= warn_pct:
            state = "NEAR_UPPER"
            recommendation = "Price is close to the upper grid boundary. Monitor take-profit or range adjustment."
        else:
            state = "IN_RANGE"
            recommendation = "Grid is inside configured range. Continue monitoring."

        return ActiveGridEvaluation(
            bot=bot,
            current_price=price,
            state=state,
            distance_to_lower_pct=self._percent(distance_lower),
            distance_to_upper_pct=self._percent(distance_upper),
            age_days=self._one_decimal(age_days) if age_days is not None else None,
            recommendation=recommendation,
        )

    def _evaluate_rebalancing_bot(
        self,
        bot: ActiveRebalancingBot,
        prices: dict[str, Decimal],
    ) -> ActiveRebalancingEvaluation:
        age_days = self._age_days(bot.created_at)
        current_values: list[Decimal] = []
        for asset, weight, entry_price in zip(bot.assets, bot.target_weights_pct, bot.entry_prices_usdt):
            current_price = prices.get(asset)
            if current_price is None or current_price <= 0 or entry_price <= 0:
                return ActiveRebalancingEvaluation(
                    bot=bot,
                    current_weights_pct=(),
                    max_drift_pct=None,
                    state="UNKNOWN_PRICE",
                    age_days=self._one_decimal(age_days) if age_days is not None else None,
                    recommendation=f"Current price for {asset} is unavailable; compare the bot directly in Binance.",
                )
            initial_value = bot.investment_usdt * weight / Decimal("100")
            current_values.append(initial_value / entry_price * current_price)
        total = sum(current_values, Decimal("0"))
        current_weights = tuple(self._percent(value / total * Decimal("100")) for value in current_values)
        drifts = tuple(abs(current - target) for current, target in zip(current_weights, bot.target_weights_pct))
        max_drift = max(drifts, default=Decimal("0"))
        if max_drift >= bot.threshold_pct:
            state = "THRESHOLD_REACHED"
            recommendation = (
                f"Theoretical basket drift reached {self._percent(max_drift)}%, at or above the "
                f"registered {bot.threshold_pct}% threshold. Verify Binance bot activity and allocation."
            )
        else:
            state = "WITHIN_THRESHOLD"
            recommendation = (
                f"Theoretical basket drift is {self._percent(max_drift)}%, below the "
                f"registered {bot.threshold_pct}% threshold. Continue monitoring."
            )
        return ActiveRebalancingEvaluation(
            bot=bot,
            current_weights_pct=current_weights,
            max_drift_pct=self._percent(max_drift),
            state=state,
            age_days=self._one_decimal(age_days) if age_days is not None else None,
            recommendation=recommendation,
        )

    def _pct(self, part: Decimal, total: Decimal) -> Decimal:
        if total == 0:
            return Decimal("0")
        return part / total * Decimal("100")

    def _percent(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _one_decimal(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    def _age_days(self, created_at: str) -> Decimal | None:
        if not created_at:
            return None
        try:
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            return None
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        seconds = (datetime.now(UTC) - created.astimezone(UTC)).total_seconds()
        return max(Decimal("0"), Decimal(str(seconds)) / Decimal("86400"))
