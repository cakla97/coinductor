from __future__ import annotations

from pathlib import Path
import os
import tomllib

from .models import ActiveGridBot, ActiveRebalancingBot


def read_state(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def write_state(
    path: Path,
    grid_bots: tuple[ActiveGridBot, ...],
    rebalancing_bots: tuple[ActiveRebalancingBot, ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Managed by trading-agent strategy registries. Edit only while the assistant is stopped.", ""]
    for bot in grid_bots:
        lines.extend(
            [
                "[[grid_bots]]",
                f'name = "{escape(bot.name)}"',
                f'binance_bot_id = "{escape(bot.binance_bot_id)}"',
                f'symbol = "{bot.symbol}"',
                f"range_low = {bot.range_low}",
                f"range_high = {bot.range_high}",
                f"grid_count = {bot.grid_count}",
                f'grid_type = "{bot.grid_type}"',
                f"investment_usdt = {bot.investment_usdt}",
                f"entry_price = {bot.entry_price}",
                f"stop_loss_price = {bot.stop_loss_price}",
                f"take_profit_price = {bot.take_profit_price}",
                f'created_at = "{escape(bot.created_at)}"',
                f'status = "{bot.status}"',
                f'notes = "{escape(bot.notes)}"',
                "",
            ]
        )
    for bot in rebalancing_bots:
        lines.extend(
            [
                "[[rebalancing_bots]]",
                f'name = "{escape(bot.name)}"',
                f'binance_bot_id = "{escape(bot.binance_bot_id)}"',
                f"assets = [{', '.join(quoted(item) for item in bot.assets)}]",
                f"target_weights_pct = [{', '.join(str(item) for item in bot.target_weights_pct)}]",
                f"entry_prices_usdt = [{', '.join(str(item) for item in bot.entry_prices_usdt)}]",
                f"investment_usdt = {bot.investment_usdt}",
                f"threshold_pct = {bot.threshold_pct}",
                f'created_at = "{escape(bot.created_at)}"',
                f'status = "{bot.status}"',
                f'notes = "{escape(bot.notes)}"',
                "",
            ]
        )
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("\n".join(lines), encoding="utf-8")
    os.replace(temporary, path)


def escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def quoted(value: str) -> str:
    return f'"{escape(value)}"'
