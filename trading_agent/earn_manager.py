from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .binance_client import BinanceApiError, BinanceClient
from .models import Balance, EarnRedeemPlan, LiquidityDecision, TradingBankrollReport
from .order_journal import OrderIntentFactory


class EarnLiquidityManager:
    def __init__(self, config: dict):
        self.config = config
        self.client = BinanceClient(config)
        self.live_client = BinanceClient(config, credential_profile="live_trade")

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
        auto_assets = {str(item).upper() for item in earn.get("auto_redeem_assets", [])}
        if quote_asset.upper() in auto_assets:
            reserve = Decimal(str(earn.get("min_auto_redeem_reserve_usdc", "0")))
            max_per_run = Decimal(str(earn.get("max_auto_redeem_usdc_per_run", earn.get("max_redeem_per_run_usdt", "0"))))
        else:
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

    def plan_flexible_redeem(
        self,
        liquidity: LiquidityDecision,
        bankroll: TradingBankrollReport,
        existing_intents: set[str] | None = None,
    ) -> EarnRedeemPlan:
        if liquidity.redeem_amount <= 0 or liquidity.redeem_asset is None:
            return self._empty("No Flexible Earn redeem is needed for this run.")

        asset = liquidity.redeem_asset.upper()
        earn = self.config.get("earn", {})
        if asset not in {str(item).upper() for item in earn.get("auto_redeem_assets", [])}:
            return self._blocked(asset, liquidity.redeem_amount, f"{asset} is not in earn.auto_redeem_assets.")
        if bankroll.preferred_source != "FLEXIBLE_EARN_REDEEM_REQUIRED":
            return self._blocked(asset, liquidity.redeem_amount, f"Bankroll source is {bankroll.preferred_source}, not FLEXIBLE_EARN_REDEEM_REQUIRED.")

        max_auto = Decimal(str(earn.get("max_auto_redeem_usdc_per_run", "0")))
        reserve = Decimal(str(earn.get("min_auto_redeem_reserve_usdc", "0")))
        amount = min(liquidity.redeem_amount, bankroll.flexible_draw_needed, max_auto)
        amount = self._money(amount)
        if amount <= 0:
            return self._blocked(asset, Decimal("0"), "Auto redeem amount is zero after configured limits.")

        intent_id = OrderIntentFactory(self.config).earn_redeem_intent_id(asset, amount)
        if intent_id in (existing_intents or set()):
            return self._blocked(asset, amount, f"Earn redeem intent {intent_id} was already submitted before.", intent_id=intent_id)

        try:
            position = self._select_position(asset, amount + reserve)
        except BinanceApiError as exc:
            return self._blocked(asset, amount, str(exc), intent_id=intent_id)
        if position is None:
            return self._blocked(asset, amount, f"No redeemable Flexible Earn {asset} position can cover amount plus reserve.", intent_id=intent_id)

        product_id = str(position.get("productId", ""))
        can_redeem = bool(position.get("canRedeem", True))
        redeem_type = str(earn.get("redeem_type", "FAST")).upper()
        if not product_id:
            return self._blocked(asset, amount, "Flexible Earn position has no productId.", intent_id=intent_id)
        if not can_redeem:
            return self._blocked(asset, amount, f"Flexible Earn product {product_id} is not currently redeemable.", intent_id=intent_id)

        if not self._submit_requested():
            return EarnRedeemPlan(
                intent_id=intent_id,
                enabled=True,
                asset=asset,
                amount=amount,
                status="PREVIEW_READY",
                product_id=product_id,
                redeem_type=redeem_type,
                can_redeem=True,
                submitted=False,
                confirmation_required="CONFIRM_EARN_REDEEM",
                message="Flexible Earn redeem is ready but was not submitted.",
            )

        confirm = str(self.config.get("_runtime", {}).get("earn_redeem_confirm", ""))
        if confirm != "CONFIRM_EARN_REDEEM":
            return EarnRedeemPlan(
                intent_id=intent_id,
                enabled=True,
                asset=asset,
                amount=amount,
                status="SUBMIT_SKIPPED",
                product_id=product_id,
                redeem_type=redeem_type,
                can_redeem=True,
                submitted=False,
                confirmation_required="CONFIRM_EARN_REDEEM",
                message="Redeem submit requested but confirmation string did not match CONFIRM_EARN_REDEEM.",
            )

        try:
            response = self.live_client.redeem_flexible_product(product_id, amount, redeem_type)
        except BinanceApiError as exc:
            return EarnRedeemPlan(
                intent_id=intent_id,
                enabled=True,
                asset=asset,
                amount=amount,
                status="SUBMIT_ERROR",
                product_id=product_id,
                redeem_type=redeem_type,
                can_redeem=True,
                submitted=True,
                confirmation_required="CONFIRM_EARN_REDEEM",
                message=str(exc),
            )

        return EarnRedeemPlan(
            intent_id=intent_id,
            enabled=True,
            asset=asset,
            amount=amount,
            status="SUBMITTED",
            product_id=product_id,
            redeem_type=redeem_type,
            can_redeem=True,
            submitted=True,
            confirmation_required="CONFIRM_EARN_REDEEM",
            message=f"Flexible Earn redeem submitted: {response}",
        )

    def _select_position(self, asset: str, minimum_total: Decimal) -> dict | None:
        positions = self.client.get_flexible_positions(asset)
        candidates = [
            row
            for row in positions
            if Decimal(str(row.get("totalAmount", "0"))) >= minimum_total and bool(row.get("canRedeem", True))
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda row: Decimal(str(row.get("totalAmount", "0"))), reverse=True)
        return candidates[0]

    def _submit_requested(self) -> bool:
        return bool(self.config.get("_runtime", {}).get("earn_redeem_submit", False))

    def _empty(self, message: str) -> EarnRedeemPlan:
        return EarnRedeemPlan("", False, None, Decimal("0"), "NOT_NEEDED", "", "", False, False, "CONFIRM_EARN_REDEEM", message)

    def _blocked(self, asset: str, amount: Decimal, message: str, intent_id: str = "") -> EarnRedeemPlan:
        return EarnRedeemPlan(intent_id, True, asset, self._money(amount), "BLOCKED", "", "", False, False, "CONFIRM_EARN_REDEEM", message)

    def _money(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
