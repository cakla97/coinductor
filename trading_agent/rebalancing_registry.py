from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from .grid_registry import GridRegistry
from .models import ActiveRebalancingBot
from .strategy_state import read_state, write_state


class RebalancingRegistry:
    def __init__(self, config: dict):
        self.config = config
        self.path = Path(str(config.get("app", {}).get("active_strategies_path", "state/active_strategies.toml")))

    def list_bots(self) -> tuple[ActiveRebalancingBot, ...]:
        raw = read_state(self.path)
        return tuple(self._from_row(row) for row in raw.get("rebalancing_bots", []))

    def validate_new(self, bot: ActiveRebalancingBot) -> tuple[str, ...]:
        issues: list[str] = []
        allowed = {str(item).upper() for item in self.config.get("rebalancing_bot", {}).get("allowed_assets", [])}
        if len(bot.assets) < int(self.config.get("rebalancing_bot", {}).get("min_assets", 2)):
            issues.append("Rebalancing bot has fewer assets than the configured minimum.")
        if len(set(bot.assets)) != len(bot.assets):
            issues.append("Rebalancing bot assets must be unique.")
        outside = sorted(set(bot.assets) - allowed)
        if outside:
            issues.append(f"Assets are outside rebalancing_bot.allowed_assets: {', '.join(outside)}.")
        if not (len(bot.assets) == len(bot.target_weights_pct) == len(bot.entry_prices_usdt)):
            issues.append("Assets, target weights, and entry prices must have equal item counts.")
        if sum(bot.target_weights_pct, Decimal("0")) != Decimal("100"):
            issues.append("Target weights must sum exactly to 100.")
        if any(item <= 0 for item in bot.target_weights_pct):
            issues.append("Every target weight must be greater than zero.")
        if any(item <= 0 for item in bot.entry_prices_usdt):
            issues.append("Every entry price must be greater than zero.")
        if bot.investment_usdt <= 0 or bot.threshold_pct <= 0:
            issues.append("Investment and threshold must be greater than zero.")
        existing = self.list_bots()
        if any(item.name == bot.name for item in existing):
            issues.append(f"Rebalancing bot name {bot.name} already exists.")
        if bot.binance_bot_id and any(item.binance_bot_id == bot.binance_bot_id for item in existing):
            issues.append(f"Binance bot id {bot.binance_bot_id} is already registered.")
        if bot.status == "ACTIVE" and any(item.status == "ACTIVE" for item in existing):
            issues.append("Only one active Rebalancing Bot is allowed.")
        return tuple(issues)

    def register(self, bot: ActiveRebalancingBot, confirm: str) -> bool:
        if confirm != "CONFIRM_REBALANCING_REGISTER":
            return False
        issues = self.validate_new(bot)
        if issues:
            raise ValueError(" ".join(issues))
        bots = list(self.list_bots())
        bots.append(bot)
        self._write(tuple(bots))
        return True

    def set_status(self, name: str, status: str, confirm: str) -> bool:
        if confirm != "CONFIRM_REBALANCING_STATUS":
            return False
        wanted = status.upper()
        if wanted not in {"ACTIVE", "PAUSED", "STOPPED", "CLOSED"}:
            raise ValueError("Rebalancing status must be ACTIVE, PAUSED, STOPPED, or CLOSED.")
        bots = list(self.list_bots())
        index = next((i for i, bot in enumerate(bots) if bot.name == name), None)
        if index is None:
            raise ValueError(f"Rebalancing bot {name} was not found.")
        if wanted == "ACTIVE" and any(i != index and item.status == "ACTIVE" for i, item in enumerate(bots)):
            raise ValueError("Another Rebalancing Bot is already ACTIVE.")
        bots[index] = replace(bots[index], status=wanted)
        self._write(tuple(bots))
        return True

    def _from_row(self, row: dict) -> ActiveRebalancingBot:
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

    def _write(self, bots: tuple[ActiveRebalancingBot, ...]) -> None:
        grids = GridRegistry(self.config).list_bots()
        write_state(self.path, grids, bots)
