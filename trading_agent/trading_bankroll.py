from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .models import Balance, TradingBankrollReport


class TradingBankrollAdvisor:
    def __init__(self, config: dict):
        self.config = config

    def analyze(self, balances: list[Balance], required_amount: Decimal) -> TradingBankrollReport:
        bankroll = self.config.get("trading_bankroll", {})
        quote_asset = str(
            bankroll.get("quote_asset", self.config.get("live_confirm", {}).get("quote_asset", self.config.get("app", {}).get("base_currency", "USDT")))
        ).upper()
        enabled = bool(bankroll.get("enabled", False))
        seed = Decimal(str(bankroll.get("initial_seed_usdc", "0")))
        allow_seed = bool(bankroll.get("allow_seed_bootstrap", True))
        max_flexible_draw = Decimal(str(bankroll.get("max_flexible_earn_draw_usdc_per_run", "0")))

        balance = next((item for item in balances if item.asset.upper() == quote_asset), None)
        spot_free = balance.spot_free if balance else Decimal("0")
        flexible_amount = balance.flexible_amount if balance else Decimal("0")
        total_quote = spot_free + flexible_amount
        realized_pnl = total_quote - seed
        profit_available = max(Decimal("0"), realized_pnl)
        seed_capital_at_risk = min(max(total_quote, Decimal("0")), seed)
        max_profit_trade_amount = min(spot_free, profit_available)

        if not enabled:
            preferred_source = "DISABLED"
            summary = "Trading bankroll tracking is disabled."
            flexible_draw_needed = Decimal("0")
        elif required_amount <= 0:
            preferred_source = "NONE"
            summary = f"No approved trade currently needs {quote_asset} bankroll."
            flexible_draw_needed = Decimal("0")
        elif max_profit_trade_amount >= required_amount:
            preferred_source = "PROFIT_SPOT"
            summary = f"Trade can be funded from realized {quote_asset} profit already available in Spot."
            flexible_draw_needed = Decimal("0")
        elif spot_free >= required_amount and allow_seed:
            preferred_source = "SEEDED_SPOT"
            summary = (
                f"Trade can be funded from seeded {quote_asset} Spot capital. "
                "This is bootstrap capital, not realized profit yet."
            )
            flexible_draw_needed = Decimal("0")
        elif total_quote >= required_amount and max_flexible_draw > 0:
            needed = max(Decimal("0"), required_amount - spot_free)
            flexible_draw_needed = min(needed, flexible_amount, max_flexible_draw)
            preferred_source = "FLEXIBLE_EARN_REDEEM_REQUIRED" if flexible_draw_needed > 0 else "SPOT_AVAILABLE"
            summary = (
                f"Spot {quote_asset} is insufficient. Redeem up to {self._money(flexible_draw_needed)} {quote_asset} "
                "from Flexible Earn only if the run remains approved."
            )
        else:
            preferred_source = "INSUFFICIENT"
            flexible_draw_needed = Decimal("0")
            summary = f"Not enough tracked {quote_asset} bankroll is available for the required amount."

        return TradingBankrollReport(
            enabled=enabled,
            quote_asset=quote_asset,
            initial_seed=self._money(seed),
            spot_free=self._money(spot_free),
            flexible_amount=self._money(flexible_amount),
            total_quote=self._money(total_quote),
            realized_pnl=self._money(realized_pnl),
            profit_available=self._money(profit_available),
            seed_capital_at_risk=self._money(seed_capital_at_risk),
            required_amount=self._money(required_amount),
            preferred_source=preferred_source,
            max_profit_trade_amount=self._money(max_profit_trade_amount),
            flexible_draw_needed=self._money(flexible_draw_needed),
            summary=summary,
        )

    def _money(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
