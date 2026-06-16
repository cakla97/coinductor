from __future__ import annotations

from decimal import Decimal

from .models import Balance, LiquidityDecision


class EarnLiquidityManager:
    def __init__(self, config: dict):
        self.config = config

    def ensure_quote_liquidity(self, balances: list[Balance], quote_asset: str, required_amount: Decimal) -> LiquidityDecision:
        spot = self._balance_for(balances, quote_asset).spot_free
        if spot >= required_amount:
            return LiquidityDecision(True, "Sufficient Spot balance.", None, Decimal("0"))

        earn = self.config["earn"]
        if not earn["allow_flexible_redeem"]:
            return LiquidityDecision(False, "Flexible redeem is disabled.", None, Decimal("0"))
        if quote_asset not in set(earn["allowed_redeem_assets"]):
            return LiquidityDecision(False, f"{quote_asset} is not allowed for Flexible redeem.", None, Decimal("0"))

        balance = self._balance_for(balances, quote_asset)
        missing = required_amount - spot
        reserve = Decimal(str(earn["min_flexible_reserve_usdt"]))
        max_per_run = Decimal(str(earn["max_redeem_per_run_usdt"]))
        available_after_reserve = max(Decimal("0"), balance.flexible_amount - reserve)
        redeem_amount = min(missing, max_per_run, available_after_reserve)

        if redeem_amount <= 0:
            return LiquidityDecision(False, "No redeemable Flexible balance after reserve.", quote_asset, Decimal("0"))
        if spot + redeem_amount < required_amount:
            return LiquidityDecision(False, "Redeem limits are not enough for the requested trade.", quote_asset, redeem_amount)
        return LiquidityDecision(True, "Flexible redeem would satisfy missing Spot liquidity.", quote_asset, redeem_amount)

    def _balance_for(self, balances: list[Balance], asset: str) -> Balance:
        return next((balance for balance in balances if balance.asset == asset), Balance(asset=asset, spot_free=Decimal("0")))

