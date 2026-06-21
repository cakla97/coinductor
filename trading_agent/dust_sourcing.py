from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .models import DustConversionItem, DustConversionPlan, PortfolioAnalysis


class DustSourcingAdvisor:
    def __init__(self, config: dict):
        self.config = config

    def plan(self, portfolio: PortfolioAnalysis) -> DustConversionPlan:
        config = self.config.get("dust_sourcing", {})
        quote_asset = str(config.get("quote_asset", self.config.get("live_confirm", {}).get("quote_asset", "USDC"))).upper()
        if not config.get("enabled", False):
            return DustConversionPlan(False, quote_asset, Decimal("0"), False, "Dust sourcing is disabled.", ())

        exclude = {str(asset).upper() for asset in config.get("exclude_assets", [])}
        min_value = Decimal(str(config.get("min_convert_value_usdt_per_asset", "0.5")))
        max_per_run = Decimal(str(config.get("max_convert_value_usdt_per_run", "10")))
        max_pct = Decimal(str(config.get("max_convert_pct_per_asset", "100"))) / Decimal("100")

        items: list[DustConversionItem] = []
        budget_remaining = max_per_run
        candidates = [
            asset
            for asset in portfolio.assets
            if asset.asset.upper() not in exclude
            and asset.total_value_usdt >= min_value
            and asset.role == "UNCLASSIFIED"
        ]
        candidates.sort(key=lambda asset: asset.total_value_usdt, reverse=True)

        for asset in candidates:
            if budget_remaining <= 0:
                break
            value = min(asset.total_value_usdt * max_pct, budget_remaining)
            value = self._money(value)
            if value <= 0:
                continue
            items.append(
                DustConversionItem(
                    asset=asset.asset,
                    value_usdt=value,
                    action=f"Consider converting up to {value} USD-like value of {asset.asset} to {quote_asset}.",
                    reason="Asset is unclassified, outside the portfolio keep-list, and can be treated as airdrop/dust funding.",
                )
            )
            budget_remaining -= value

        total = self._money(sum((item.value_usdt for item in items), Decimal("0")))
        if not items:
            return DustConversionPlan(True, quote_asset, Decimal("0"), False, "No eligible airdrop/dust assets found outside the keep-list.", ())
        return DustConversionPlan(
            True,
            quote_asset,
            total,
            True,
            f"Dust sourcing can provide up to {total} {quote_asset} from unclassified airdrop/dust assets.",
            tuple(items),
        )

    def _money(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
