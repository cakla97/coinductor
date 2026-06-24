from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from .grid_registry import GridRegistry
from .models import ActiveGridBot, ActiveGridEvaluation, ActiveStrategiesReport, MarketSnapshot


class ActiveStrategiesTracker:
    def __init__(self, config: dict):
        self.config = config

    def evaluate(self, snapshots: list[MarketSnapshot]) -> ActiveStrategiesReport:
        strategy_config = self.config.get("active_strategies", {})
        if not strategy_config.get("enabled", True):
            return ActiveStrategiesReport(enabled=False, grid_bots=(), summary="Active strategy tracking is disabled.")

        path = Path(str(self.config.get("app", {}).get("active_strategies_path", "state/active_strategies.toml")))
        if not path.exists():
            return ActiveStrategiesReport(
                enabled=True,
                grid_bots=(),
                summary=(
                    f"No active strategies file found at {path}. After manually creating a Binance grid, "
                    "use `python -m trading_agent grid-register` to register its exact values."
                ),
            )

        bots = GridRegistry(self.config).list_bots()
        prices = {snapshot.symbol: snapshot.price for snapshot in snapshots}
        evaluations = tuple(self._evaluate_bot(bot, prices.get(bot.symbol)) for bot in bots if bot.status.upper() == "ACTIVE")
        if not evaluations:
            summary = "No active grid bots are marked ACTIVE."
        else:
            urgent = [
                item
                for item in evaluations
                if item.state in {"STOP_LOSS_BREACH", "TAKE_PROFIT_REACHED", "RUNTIME_EXPIRED", "BELOW_RANGE", "ABOVE_RANGE"}
            ]
            if urgent:
                summary = f"{len(urgent)} active grid bot(s) need lifecycle review."
            else:
                summary = f"{len(evaluations)} active grid bot(s) are being tracked."
        return ActiveStrategiesReport(enabled=True, grid_bots=evaluations, summary=summary)

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
            created = created.replace(tzinfo=timezone.utc)
        seconds = (datetime.now(timezone.utc) - created.astimezone(timezone.utc)).total_seconds()
        return max(Decimal("0"), Decimal(str(seconds)) / Decimal("86400"))
