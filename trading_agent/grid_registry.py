from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from .models import ActiveGridBot, ActiveRebalancingBot
from .strategy_state import read_state, write_state


class GridRegistry:
    def __init__(self, config: dict):
        self.config = config
        self.path = Path(str(config.get("app", {}).get("active_strategies_path", "state/active_strategies.toml")))

    def list_bots(self) -> tuple[ActiveGridBot, ...]:
        raw = read_state(self.path)
        return tuple(self._from_row(row) for row in raw.get("grid_bots", []))

    def validate_new(self, bot: ActiveGridBot) -> tuple[str, ...]:
        issues: list[str] = []
        allowed = {str(item).upper() for item in self.config.get("grid_bot", {}).get("allowed_symbols", [])}
        if bot.symbol not in allowed:
            issues.append(f"{bot.symbol} is not in grid_bot.allowed_symbols.")
        if bot.range_low <= 0 or bot.range_high <= bot.range_low:
            issues.append("Grid range must satisfy 0 < range_low < range_high.")
        if not bot.range_low < bot.entry_price < bot.range_high:
            issues.append("entry_price must be inside the grid range.")
        if bot.grid_count < int(self.config.get("grid_bot", {}).get("min_grid_count", 1)):
            issues.append("grid_count is below the configured minimum.")
        if bot.grid_count > int(self.config.get("grid_bot", {}).get("max_grid_count", 1000)):
            issues.append("grid_count is above the configured maximum.")
        if bot.investment_usdt <= 0:
            issues.append("investment_usdt must be greater than zero.")
        if bot.stop_loss_price <= 0 or bot.stop_loss_price >= bot.range_low:
            issues.append("stop_loss_price must be positive and below range_low.")
        if bot.take_profit_price <= bot.range_high:
            issues.append("take_profit_price must be above range_high.")
        existing = self.list_bots()
        if any(item.name == bot.name for item in existing):
            issues.append(f"Grid name {bot.name} already exists.")
        if bot.binance_bot_id and any(item.binance_bot_id == bot.binance_bot_id for item in existing):
            issues.append(f"Binance bot id {bot.binance_bot_id} is already registered.")
        active_count = sum(1 for item in existing if item.status == "ACTIVE")
        max_active = int(self.config.get("grid_bot", {}).get("max_active_grid_bots", 1))
        if bot.status == "ACTIVE" and active_count >= max_active:
            issues.append(f"Active grid limit {max_active} is already reached.")
        return tuple(issues)

    def register(self, bot: ActiveGridBot, confirm: str) -> bool:
        if confirm != "CONFIRM_GRID_REGISTER":
            return False
        issues = self.validate_new(bot)
        if issues:
            raise ValueError(" ".join(issues))
        bots = list(self.list_bots())
        bots.append(bot)
        self._write(tuple(bots))
        return True

    def set_status(self, name: str, status: str, confirm: str) -> bool:
        if confirm != "CONFIRM_GRID_STATUS":
            return False
        wanted = status.upper()
        if wanted not in {"ACTIVE", "PAUSED", "STOPPED", "CLOSED"}:
            raise ValueError("Grid status must be ACTIVE, PAUSED, STOPPED, or CLOSED.")
        bots = list(self.list_bots())
        index = next((i for i, bot in enumerate(bots) if bot.name == name), None)
        if index is None:
            raise ValueError(f"Grid {name} was not found.")
        if wanted == "ACTIVE":
            active_others = sum(1 for i, bot in enumerate(bots) if i != index and bot.status == "ACTIVE")
            maximum = int(self.config.get("grid_bot", {}).get("max_active_grid_bots", 1))
            if active_others >= maximum:
                raise ValueError(f"Cannot activate {name}; active grid limit {maximum} is reached.")
        bots[index] = replace(bots[index], status=wanted)
        self._write(tuple(bots))
        return True

    def _from_row(self, row: dict) -> ActiveGridBot:
        return ActiveGridBot(
            name=str(row.get("name", "")),
            binance_bot_id=str(row.get("binance_bot_id", "")),
            symbol=str(row["symbol"]).upper(),
            range_low=Decimal(str(row["range_low"])),
            range_high=Decimal(str(row["range_high"])),
            grid_count=int(row.get("grid_count", 0)),
            grid_type=str(row.get("grid_type", "ARITHMETIC")).upper(),
            investment_usdt=Decimal(str(row.get("investment_usdt", "0"))),
            entry_price=Decimal(str(row.get("entry_price", "0"))),
            stop_loss_price=Decimal(str(row.get("stop_loss_price", "0"))),
            take_profit_price=Decimal(str(row.get("take_profit_price", "0"))),
            created_at=str(row.get("created_at", "")),
            status=str(row.get("status", "ACTIVE")).upper(),
            notes=str(row.get("notes", "")),
        )

    def _write(self, bots: tuple[ActiveGridBot, ...]) -> None:
        raw = read_state(self.path)
        rebalancing = tuple(self._rebalancing_from_row(row) for row in raw.get("rebalancing_bots", []))
        write_state(self.path, bots, rebalancing)

    def _rebalancing_from_row(self, row: dict) -> ActiveRebalancingBot:
        return ActiveRebalancingBot(
            name=str(row.get("name", "")),
            binance_bot_id=str(row.get("binance_bot_id", "")),
            assets=tuple(str(item).upper() for item in row.get("assets", [])),
            target_weights_pct=tuple(Decimal(str(item)) for item in row.get("target_weights_pct", [])),
            entry_prices_usdt=tuple(Decimal(str(item)) for item in row.get("entry_prices_usdt", [])),
            investment_usdt=Decimal(str(row.get("investment_usdt", "0"))),
            threshold_pct=Decimal(str(row.get("threshold_pct", "0"))),
            created_at=str(row.get("created_at", "")),
            status=str(row.get("status", "ACTIVE")).upper(),
            notes=str(row.get("notes", "")),
        )
