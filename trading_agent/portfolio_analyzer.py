from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .decimal_utils import money
from .models import Balance, PortfolioAnalysis, PortfolioAssetValuation


class PortfolioAnalyzer:
    def __init__(self, config: dict):
        self.config = config

    def analyze(self, balances: list[Balance], prices: dict[str, Decimal]) -> PortfolioAnalysis:
        rebalancing = self.config.get("rebalancing", {})
        target_mode = str(rebalancing.get("target_mode", "static")).lower()
        configured_target_allocation = {
            asset.upper(): Decimal(str(percent))
            for asset, percent in rebalancing.get("target_allocation", {}).items()
        }
        raw_rows: list[tuple[Balance, Decimal, Decimal, Decimal, Decimal]] = []
        unpriced_assets: list[str] = []
        ignored_internal_assets: list[str] = []
        for balance in balances:
            price = prices.get(balance.asset, Decimal("0"))
            total_amount = balance.spot_free + balance.spot_locked + balance.flexible_amount + balance.locked_amount
            if price == 0 and total_amount > 0:
                if self._is_ignored_internal_asset(balance.asset):
                    ignored_internal_assets.append(balance.asset)
                    continue
                unpriced_assets.append(balance.asset)
            spot_value = (balance.spot_free + balance.spot_locked) * price
            flexible_value = balance.flexible_amount * price
            locked_value = balance.locked_amount * price
            total_value = spot_value + flexible_value + locked_value
            if total_value > 0:
                raw_rows.append((balance, price, spot_value, flexible_value, locked_value))

        total_value = sum((row[2] + row[3] + row[4] for row in raw_rows), Decimal("0"))
        spot_value_total = sum((row[2] for row in raw_rows), Decimal("0"))
        flexible_value_total = sum((row[3] for row in raw_rows), Decimal("0"))
        locked_value_total = sum((row[4] for row in raw_rows), Decimal("0"))
        assets = tuple(
            self._asset_valuation(
                balance=row[0],
                price=row[1],
                spot_value=row[2],
                flexible_value=row[3],
                locked_value=row[4],
                total_value=total_value,
                target_mode=target_mode,
                target_allocation=configured_target_allocation,
            )
            for row in sorted(raw_rows, key=lambda item: item[2] + item[3] + item[4], reverse=True)
        )
        locked_pct = self._pct(locked_value_total, total_value)
        liquid_value = spot_value_total + flexible_value_total
        return PortfolioAnalysis(
            total_value_usdt=self._money(total_value),
            spot_value_usdt=self._money(spot_value_total),
            flexible_value_usdt=self._money(flexible_value_total),
            locked_value_usdt=self._money(locked_value_total),
            liquid_value_usdt=self._money(liquid_value),
            locked_pct=self._percent(locked_pct),
            assets=assets,
            unpriced_assets=tuple(sorted(unpriced_assets)),
            ignored_internal_assets=tuple(sorted(ignored_internal_assets)),
            rebalance_summary=self._rebalance_summary(assets, target_mode),
            liquidity_summary=self._liquidity_summary(locked_pct, unpriced_assets),
        )

    def _asset_valuation(
        self,
        balance: Balance,
        price: Decimal,
        spot_value: Decimal,
        flexible_value: Decimal,
        locked_value: Decimal,
        total_value: Decimal,
        target_mode: str,
        target_allocation: dict[str, Decimal],
    ) -> PortfolioAssetValuation:
        asset_total = spot_value + flexible_value + locked_value
        allocation_pct = self._pct(asset_total, total_value)
        target_pct = allocation_pct if target_mode == "baseline_current" else target_allocation.get(balance.asset)
        gap_pct = allocation_pct - target_pct if target_pct is not None else None
        action = self._rebalance_action(gap_pct, target_mode)
        return PortfolioAssetValuation(
            asset=balance.asset,
            role=self._asset_role(balance.asset),
            price_usdt=self._money(price),
            spot_value_usdt=self._money(spot_value),
            flexible_value_usdt=self._money(flexible_value),
            locked_value_usdt=self._money(locked_value),
            total_value_usdt=self._money(asset_total),
            allocation_pct=self._percent(allocation_pct),
            target_pct=self._percent(target_pct) if target_pct is not None else None,
            gap_pct=self._percent(gap_pct) if gap_pct is not None else None,
            rebalance_action=action,
        )

    def _rebalance_action(self, gap_pct: Decimal | None, target_mode: str) -> str:
        if gap_pct is None:
            return "NO_TARGET"
        rebalancing = self.config.get("rebalancing", {})
        threshold_key = "drift_threshold_pct" if target_mode == "baseline_current" else "threshold_pct"
        threshold = Decimal(str(rebalancing.get(threshold_key, rebalancing.get("threshold_pct", 5))))
        if gap_pct > threshold:
            return "REDUCE"
        if gap_pct < -threshold:
            return "INCREASE"
        return "HOLD"

    def _is_ignored_internal_asset(self, asset: str) -> bool:
        prefixes = self.config.get("portfolio", {}).get("ignored_asset_prefixes", [])
        return any(asset.upper().startswith(str(prefix).upper()) for prefix in prefixes)

    def _asset_role(self, asset: str) -> str:
        roles = self.config.get("portfolio", {}).get("asset_roles", {})
        return str(roles.get(asset.upper(), "UNCLASSIFIED")).upper()

    def _rebalance_summary(self, assets: tuple[PortfolioAssetValuation, ...], target_mode: str) -> str:
        actions = [asset for asset in assets if asset.rebalance_action in {"REDUCE", "INCREASE"}]
        if not actions:
            if target_mode == "baseline_current":
                return "Portfolio is treated as the current allocation baseline; no drift beyond configured baseline thresholds is detected."
            return "Portfolio is within configured rebalance thresholds for targeted assets."
        fragments = [f"{asset.asset}: {asset.rebalance_action} ({asset.gap_pct:+} pp)" for asset in actions if asset.gap_pct is not None]
        return "Rebalance gaps detected: " + "; ".join(fragments)

    def _liquidity_summary(self, locked_pct: Decimal, unpriced_assets: list[str]) -> str:
        locked_percent = self._percent(locked_pct)
        unpriced_note = ""
        if unpriced_assets:
            unpriced_note = f" Unpriced assets are excluded from totals: {', '.join(sorted(unpriced_assets))}."
        if locked_percent > Decimal("50"):
            return (
                f"{locked_percent}% of portfolio value is locked. For a more flexible assistant workflow, consider "
                f"manually moving expiring or low-yield locked positions to Flexible Earn.{unpriced_note}"
            )
        if locked_percent > Decimal("0"):
            return f"{locked_percent}% of portfolio value is locked. Keep locked positions read-only unless you manually decide otherwise.{unpriced_note}"
        return f"Portfolio is fully liquid from the assistant perspective: Spot plus Flexible Earn only.{unpriced_note}"

    def _pct(self, part: Decimal, total: Decimal) -> Decimal:
        if total == 0:
            return Decimal("0")
        return part / total * Decimal("100")

    def _money(self, value: Decimal) -> Decimal:
        return money(value)

    def _percent(self, value: Decimal | None) -> Decimal:
        if value is None:
            return Decimal("0")
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
