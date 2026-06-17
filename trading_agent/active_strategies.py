from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import tomllib

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
                summary=f"No active strategies file found at {path}. Copy state/active_strategies.example.toml when you manually create a grid bot.",
            )

        bots = self._load_grid_bots(path)
        prices = {snapshot.symbol: snapshot.price for snapshot in snapshots}
        evaluations = tuple(self._evaluate_bot(bot, prices.get(bot.symbol)) for bot in bots if bot.status.upper() == "ACTIVE")
        if not evaluations:
            summary = "No active grid bots are marked ACTIVE."
        else:
            out_of_range = [item for item in evaluations if item.state in {"BELOW_RANGE", "ABOVE_RANGE"}]
            if out_of_range:
                summary = f"{len(out_of_range)} active grid bot(s) are outside configured range and need review."
            else:
                summary = f"{len(evaluations)} active grid bot(s) are being tracked."
        return ActiveStrategiesReport(enabled=True, grid_bots=evaluations, summary=summary)

    def _load_grid_bots(self, path: Path) -> tuple[ActiveGridBot, ...]:
        with path.open("rb") as handle:
            raw = tomllib.load(handle)
        bots = []
        for row in raw.get("grid_bots", []):
            bots.append(
                ActiveGridBot(
                    name=str(row.get("name", "")),
                    symbol=str(row["symbol"]).upper(),
                    range_low=Decimal(str(row["range_low"])),
                    range_high=Decimal(str(row["range_high"])),
                    investment_usdt=Decimal(str(row.get("investment_usdt", "0"))),
                    created_at=str(row.get("created_at", "")),
                    status=str(row.get("status", "ACTIVE")).upper(),
                    notes=str(row.get("notes", "")),
                )
            )
        return tuple(bots)

    def _evaluate_bot(self, bot: ActiveGridBot, price: Decimal | None) -> ActiveGridEvaluation:
        if price is None:
            return ActiveGridEvaluation(bot, None, "UNKNOWN_PRICE", None, None, "Current symbol price is unavailable; review manually.")

        distance_lower = self._pct(price - bot.range_low, bot.range_low)
        distance_upper = self._pct(bot.range_high - price, bot.range_high)
        warn_pct = Decimal(str(self.config.get("active_strategies", {}).get("warn_near_range_pct", 5)))

        if price < bot.range_low:
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
            recommendation=recommendation,
        )

    def _pct(self, part: Decimal, total: Decimal) -> Decimal:
        if total == 0:
            return Decimal("0")
        return part / total * Decimal("100")

    def _percent(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

