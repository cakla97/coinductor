from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .decimal_utils import money
from .models import PortfolioAnalysis, RebalancePlan, RebalancePlanStep


class RebalancePlanner:
    def __init__(self, config: dict):
        self.config = config

    def plan(self, portfolio: PortfolioAnalysis) -> RebalancePlan:
        rebalancing = self.config.get("rebalancing", {})
        if not rebalancing.get("enabled", False):
            return RebalancePlan(enabled=False, preview_only=True, steps=(), summary="Rebalancing is disabled.")

        min_trade = Decimal(str(rebalancing.get("min_trade_value_usdt", 5)))
        max_per_step = Decimal(str(rebalancing.get("max_trade_value_usdt_per_step", 25)))
        max_pct_per_asset = Decimal(str(rebalancing.get("max_trade_pct_per_asset", "15"))) / Decimal("100")
        min_remaining_pct = Decimal(str(rebalancing.get("min_remaining_pct_per_asset", "70"))) / Decimal("100")
        min_remaining_value = Decimal(str(rebalancing.get("min_remaining_value_usdt_per_asset", "50")))
        preview_only = bool(rebalancing.get("preview_only", True))
        allowed_symbols = {str(symbol).upper() for symbol in self.config.get("strategy", {}).get("allowed_symbols", [])}
        protected_assets = {str(asset).upper() for asset in self.config.get("capital_sourcing", {}).get("protected_assets", [])}
        source_assets = {str(asset).upper() for asset in self.config.get("capital_sourcing", {}).get("allowed_source_assets", [])}
        quote_asset = str(self.config.get("live_confirm", {}).get("quote_asset", self.config.get("app", {}).get("base_currency", "USDT"))).upper()

        steps: list[RebalancePlanStep] = []
        for asset in portfolio.assets:
            if asset.target_pct is None or asset.gap_pct is None or asset.rebalance_action == "HOLD":
                continue

            target_value = portfolio.total_value_usdt * asset.target_pct / Decimal("100")
            delta = target_value - asset.total_value_usdt
            if abs(delta) < min_trade:
                continue

            if asset.rebalance_action == "REDUCE":
                steps.append(
                    self._reduce_step(
                        asset.asset,
                        asset.total_value_usdt,
                        abs(delta),
                        max_per_step,
                        max_pct_per_asset,
                        min_remaining_pct,
                        min_remaining_value,
                        allowed_symbols,
                        protected_assets,
                        source_assets,
                        quote_asset,
                    )
                )
            elif asset.rebalance_action == "INCREASE":
                steps.append(self._increase_step(asset.asset, delta, max_per_step, allowed_symbols, quote_asset))

        if not steps:
            summary = "No actionable rebalance preview steps are needed inside configured thresholds and limits."
        else:
            actionable = len([step for step in steps if step.status == "READY"])
            blocked = len([step for step in steps if step.status == "BLOCKED"])
            summary = f"{actionable} ready rebalance preview step(s), {blocked} blocked step(s). Preview only; no orders are created."
        return RebalancePlan(enabled=True, preview_only=preview_only, steps=tuple(steps), summary=summary)

    def _reduce_step(
        self,
        asset: str,
        asset_value: Decimal,
        value: Decimal,
        max_per_step: Decimal,
        max_pct_per_asset: Decimal,
        min_remaining_pct: Decimal,
        min_remaining_value: Decimal,
        allowed_symbols: set[str],
        protected_assets: set[str],
        source_assets: set[str],
        quote_asset: str,
    ) -> RebalancePlanStep:
        capped_value = self._guarded_reduce_value(asset_value, value, max_per_step, max_pct_per_asset, min_remaining_pct, min_remaining_value)
        if asset.upper() in protected_assets:
            return RebalancePlanStep(
                asset=asset,
                symbol=None,
                side="SELL",
                value_usdt=self._money(capped_value),
                status="BLOCKED",
                reason=f"{asset} is protected and will not be sold by the rebalancing planner.",
            )
        if asset.upper() not in source_assets:
            return RebalancePlanStep(
                asset=asset,
                symbol=None,
                side="SELL",
                value_usdt=self._money(capped_value),
                status="BLOCKED",
                reason=f"{asset} is not in capital_sourcing.allowed_source_assets, so rebalancing will not sell it.",
            )
        symbol = f"{asset.upper()}{quote_asset}"
        if symbol not in allowed_symbols:
            return RebalancePlanStep(
                asset=asset,
                symbol=symbol,
                side="SELL",
                value_usdt=self._money(capped_value),
                status="BLOCKED",
                reason=f"{symbol} is not in strategy.allowed_symbols.",
            )
        if capped_value <= 0:
            return RebalancePlanStep(
                asset=asset,
                symbol=symbol,
                side="SELL",
                value_usdt=Decimal("0.00"),
                status="BLOCKED",
                reason="Rebalancing sell is blocked by remaining-value and percentage reserve limits.",
            )
        return RebalancePlanStep(
            asset=asset,
            symbol=symbol,
            side="SELL",
            value_usdt=self._money(capped_value),
            status="READY",
            reason=(
                f"{asset} is above target allocation and can be reduced within guarded rebalancing caps "
                f"(max {self._percent(max_pct_per_asset)}% per asset, keep at least {self._percent(min_remaining_pct)}%)."
            ),
        )

    def _increase_step(
        self,
        asset: str,
        value: Decimal,
        max_per_step: Decimal,
        allowed_symbols: set[str],
        quote_asset: str,
    ) -> RebalancePlanStep:
        if asset.upper() == quote_asset:
            return RebalancePlanStep(
                asset=asset,
                symbol=None,
                side="KEEP_CASH",
                value_usdt=self._money(min(value, max_per_step)),
                status="READY",
                reason=f"{quote_asset} is below target; keep or source more cash instead of placing a trade.",
            )
        symbol = f"{asset.upper()}{quote_asset}"
        if symbol not in allowed_symbols:
            return RebalancePlanStep(
                asset=asset,
                symbol=symbol,
                side="BUY",
                value_usdt=self._money(min(value, max_per_step)),
                status="BLOCKED",
                reason=f"{symbol} is not in strategy.allowed_symbols.",
            )
        return RebalancePlanStep(
            asset=asset,
            symbol=symbol,
            side="BUY",
            value_usdt=self._money(min(value, max_per_step)),
            status="READY",
            reason=f"{asset} is below target allocation and can be increased within the configured per-step cap.",
        )

    def _money(self, value: Decimal) -> Decimal:
        return money(value)

    def _guarded_reduce_value(
        self,
        asset_value: Decimal,
        requested: Decimal,
        max_per_step: Decimal,
        max_pct_per_asset: Decimal,
        min_remaining_pct: Decimal,
        min_remaining_value: Decimal,
    ) -> Decimal:
        min_remaining_from_pct = asset_value * min_remaining_pct
        required_remaining = max(min_remaining_value, min_remaining_from_pct)
        max_from_remaining = max(Decimal("0"), asset_value - required_remaining)
        max_from_pct = asset_value * max_pct_per_asset
        return min(requested, max_per_step, max_from_remaining, max_from_pct)

    def _percent(self, ratio: Decimal) -> Decimal:
        return (ratio * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
