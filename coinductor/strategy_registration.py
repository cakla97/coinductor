from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from trading_agent.config import default_config_path, load_config
from trading_agent.grid_registry import GridRegistry
from trading_agent.models import ActiveGridBot, ActiveRebalancingBot
from trading_agent.rebalancing_registry import RebalancingRegistry


@dataclass(frozen=True)
class StrategyRegistrationResult:
    success: bool
    message: str


class StrategyRegistrationService:
    def __init__(self, config_path: Path | str | None = None):
        self.config_path = Path(config_path or default_config_path())

    def grid_symbols(self) -> tuple[str, ...]:
        if not self.config_path.exists():
            return ()
        config = self._config()
        return tuple(str(item).upper() for item in config.get("grid_bot", {}).get("allowed_symbols", []))

    def rebalancing_assets(self) -> tuple[str, ...]:
        if not self.config_path.exists():
            return ()
        config = self._config()
        return tuple(str(item).upper() for item in config.get("rebalancing_bot", {}).get("allowed_assets", []))

    def registered_count(self) -> int:
        if not self.config_path.exists():
            return 0
        config = self._config()
        grids = GridRegistry(config).list_bots()
        rebalancing = RebalancingRegistry(config).list_bots()
        return sum(bot.status == "ACTIVE" for bot in grids) + sum(bot.status == "ACTIVE" for bot in rebalancing)

    def update_status(
        self,
        *,
        strategy_type: str,
        name: str,
        status: str,
        verified: bool,
    ) -> StrategyRegistrationResult:
        if not verified:
            return StrategyRegistrationResult(False, "Confirm that you already changed the bot status in Binance.")
        wanted = status.strip().upper()
        if wanted not in {"PAUSED", "STOPPED", "CLOSED"}:
            return StrategyRegistrationResult(False, "Choose Paused, Stopped, or Closed for the local monitoring record.")
        try:
            config = self._config()
            if strategy_type == "Spot Grid":
                GridRegistry(config).set_status(name, wanted, "CONFIRM_GRID_STATUS")
            elif strategy_type == "Rebalancing":
                RebalancingRegistry(config).set_status(name, wanted, "CONFIRM_REBALANCING_STATUS")
            else:
                return StrategyRegistrationResult(False, "This strategy type cannot be updated.")
        except ValueError as exc:
            return StrategyRegistrationResult(False, self._friendly_error(exc))
        label = wanted.title()
        return StrategyRegistrationResult(
            True,
            f"'{name}' is now {label} in Coinductor. This did not change anything in Binance.",
        )

    def register_grid(
        self,
        *,
        name: str,
        binance_bot_id: str,
        symbol: str,
        range_low: str,
        range_high: str,
        grid_count: str,
        grid_type: str,
        investment: str,
        entry_price: str,
        stop_loss: str,
        take_profit: str,
        created_at: str,
        notes: str,
        verified: bool,
    ) -> StrategyRegistrationResult:
        if not verified:
            return StrategyRegistrationResult(False, "Confirm that every value matches the active bot in Binance.")
        if not name.strip():
            return StrategyRegistrationResult(False, "Enter a local strategy name.")
        try:
            bot = ActiveGridBot(
                name=name.strip(),
                binance_bot_id=binance_bot_id.strip(),
                symbol=symbol.strip().upper(),
                range_low=self._decimal(range_low),
                range_high=self._decimal(range_high),
                grid_count=int(grid_count.strip()),
                grid_type=grid_type.strip().upper(),
                investment_usdt=self._decimal(investment),
                entry_price=self._decimal(entry_price),
                stop_loss_price=self._decimal(stop_loss),
                take_profit_price=self._decimal(take_profit),
                created_at=self._created_at(created_at),
                status="ACTIVE",
                notes=notes.strip(),
            )
            config = self._config()
            GridRegistry(config).register(bot, "CONFIRM_GRID_REGISTER")
        except (ValueError, ArithmeticError) as exc:
            return StrategyRegistrationResult(False, self._friendly_error(exc))
        return StrategyRegistrationResult(True, f"Spot Grid '{bot.name}' was registered locally. Monitoring is refreshing.")

    def register_rebalancing(
        self,
        *,
        name: str,
        binance_bot_id: str,
        assets: str,
        target_weights: str,
        entry_prices: str,
        investment: str,
        threshold: str,
        created_at: str,
        notes: str,
        verified: bool,
    ) -> StrategyRegistrationResult:
        if not verified:
            return StrategyRegistrationResult(False, "Confirm that every value matches the active bot in Binance.")
        if not name.strip():
            return StrategyRegistrationResult(False, "Enter a local strategy name.")
        try:
            bot = ActiveRebalancingBot(
                name=name.strip(),
                binance_bot_id=binance_bot_id.strip(),
                assets=self._items(assets, upper=True),
                target_weights_pct=self._decimals(target_weights),
                entry_prices_usdt=self._decimals(entry_prices),
                investment_usdt=self._decimal(investment),
                threshold_pct=self._decimal(threshold),
                created_at=self._created_at(created_at),
                status="ACTIVE",
                notes=notes.strip(),
            )
            config = self._config()
            RebalancingRegistry(config).register(bot, "CONFIRM_REBALANCING_REGISTER")
        except (ValueError, ArithmeticError) as exc:
            return StrategyRegistrationResult(False, self._friendly_error(exc))
        return StrategyRegistrationResult(True, f"Rebalancing Bot '{bot.name}' was registered locally. Monitoring is refreshing.")

    def _config(self) -> dict:
        return load_config(self.config_path).raw

    def _decimal(self, value: str) -> Decimal:
        cleaned = value.strip().replace(" ", "").replace(",", ".")
        if not cleaned:
            raise ValueError("Complete every required numeric field.")
        return Decimal(cleaned)

    def _decimals(self, value: str) -> tuple[Decimal, ...]:
        return tuple(self._decimal(item) for item in value.split(",") if item.strip())

    def _items(self, value: str, *, upper: bool = False) -> tuple[str, ...]:
        items = tuple(item.strip() for item in value.split(",") if item.strip())
        return tuple(item.upper() for item in items) if upper else items

    def _created_at(self, value: str) -> str:
        if not value.strip():
            return datetime.now(timezone.utc).isoformat(timespec="seconds")
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.isoformat(timespec="seconds")

    def _friendly_error(self, error: Exception) -> str:
        message = str(error).replace("grid_bot.allowed_symbols", "the configured Grid symbol list")
        message = message.replace("rebalancing_bot.allowed_assets", "the configured Rebalancing asset list")
        message = message.replace("range_low", "lower range").replace("range_high", "upper range")
        message = message.replace("entry_price", "entry price").replace("grid_count", "grid count")
        message = message.replace("investment_usdt", "investment")
        message = message.replace("stop_loss_price", "stop loss").replace("take_profit_price", "take profit")
        return message or "The strategy parameters could not be registered."
