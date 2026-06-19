from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

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
        preview_only = bool(rebalancing.get("preview_only", True))
        allowed_symbols = {str(symbol).upper() for symbol in self.config.get("strategy", {}).get("allowed_symbols", [])}
        protected_assets = {str(asset).upper() for asset in self.config.get("capital_sourcing", {}).get("protected_assets", [])}

        steps: list[RebalancePlanStep] = []
        for asset in portfolio.assets:
            if asset.target_pct is None or asset.gap_pct is None or asset.rebalance_action == "HOLD":
                continue

            target_value = portfolio.total_value_usdt * asset.target_pct / Decimal("100")
            delta = target_value - asset.total_value_usdt
            if abs(delta) < min_trade:
                continue

            if asset.rebalance_action == "REDUCE":
                steps.append(self._reduce_step(asset.asset, abs(delta), max_per_step, allowed_symbols, protected_assets))
            elif asset.rebalance_action == "INCREASE":
                steps.append(self._increase_step(asset.asset, delta, max_per_step, allowed_symbols))

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
        value: Decimal,
        max_per_step: Decimal,
        allowed_symbols: set[str],
        protected_assets: set[str],
    ) -> RebalancePlanStep:
        if asset.upper() in protected_assets:
            return RebalancePlanStep(
                asset=asset,
                symbol=None,
                side="SELL",
                value_usdt=self._money(min(value, max_per_step)),
                status="BLOCKED",
                reason=f"{asset} is protected and will not be sold by the rebalancing planner.",
            )
        symbol = f"{asset.upper()}USDT"
        if symbol not in allowed_symbols:
            return RebalancePlanStep(
                asset=asset,
                symbol=symbol,
                side="SELL",
                value_usdt=self._money(min(value, max_per_step)),
                status="BLOCKED",
                reason=f"{symbol} is not in strategy.allowed_symbols.",
            )
        return RebalancePlanStep(
            asset=asset,
            symbol=symbol,
            side="SELL",
            value_usdt=self._money(min(value, max_per_step)),
            status="READY",
            reason=f"{asset} is above target allocation and can be reduced within the configured per-step cap.",
        )

    def _increase_step(
        self,
        asset: str,
        value: Decimal,
        max_per_step: Decimal,
        allowed_symbols: set[str],
    ) -> RebalancePlanStep:
        if asset.upper() == "USDT":
            return RebalancePlanStep(
                asset=asset,
                symbol=None,
                side="KEEP_CASH",
                value_usdt=self._money(min(value, max_per_step)),
                status="READY",
                reason="USDT is below target; keep or source more cash instead of placing a trade.",
            )
        symbol = f"{asset.upper()}USDT"
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
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
