from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .models import PortfolioAnalysis, PortfolioAssetValuation, RebalancingBotAsset, RebalancingBotRecommendation


class RebalancingBotAdvisor:
    def __init__(self, config: dict):
        self.config = config

    def recommend(self, portfolio: PortfolioAnalysis) -> RebalancingBotRecommendation:
        config = self.config.get("rebalancing_bot", {})
        if not config.get("enabled", False):
            return self._empty("Rebalancing Bot advisor is disabled.")

        allowed = tuple(str(asset).upper() for asset in config.get("allowed_assets", []))
        minimum_assets = int(config.get("min_assets", 2))
        minimum_value = Decimal(str(config.get("min_asset_value_usdt", "25")))
        maximum_investment = Decimal(str(config.get("max_investment_usdt", "100")))
        maximum_portfolio_pct = Decimal(str(config.get("max_portfolio_pct", "15"))) / Decimal("100")
        threshold = Decimal(str(config.get("threshold_pct", "5")))
        mode = str(config.get("mode", "THRESHOLD")).upper()
        by_asset = {item.asset.upper(): item for item in portfolio.assets}

        eligible: list[tuple[str, PortfolioAssetValuation, str, str]] = []
        blockers: list[str] = []
        for asset in allowed:
            if asset in by_asset and by_asset[asset].total_value_usdt >= minimum_value:
                eligible.append(
                    (
                        asset,
                        by_asset[asset],
                        "ELIGIBLE",
                        "Target preserves this asset's relative weight inside the eligible bot basket.",
                    )
                )
            elif asset == "ETH" and "WBETH" in by_asset and by_asset["WBETH"].total_value_usdt >= minimum_value:
                eligible.append(
                    (
                        "ETH",
                        by_asset["WBETH"],
                        "FUNDED_FROM_USDC",
                        (
                            "Target uses protected WBETH only as a reference for current ETH exposure. "
                            "The bot's ETH allocation must be funded from its separate USDC investment."
                        ),
                    )
                )
        if len(eligible) < minimum_assets:
            blockers.append(f"only {len(eligible)} eligible assets meet the minimum value; at least {minimum_assets} are required")

        eligible_total = sum((item.total_value_usdt for _, item, _, _ in eligible), Decimal("0"))
        assets: list[RebalancingBotAsset] = []
        if eligible_total > 0:
            raw_weights = [item.total_value_usdt / eligible_total * Decimal("100") for _, item, _, _ in eligible]
            rounded_weights = self._balanced_weights(raw_weights)
            for (asset, item, status, reason), target in zip(eligible, rounded_weights):
                assets.append(
                    RebalancingBotAsset(
                        asset=asset,
                        current_value_usdt=self._money(item.total_value_usdt),
                        current_weight_pct=self._one_decimal(item.allocation_pct),
                        target_weight_pct=target,
                        role=item.role,
                        status=status,
                        reason=reason,
                    )
                )

        investment = min(maximum_investment, portfolio.total_value_usdt * maximum_portfolio_pct, eligible_total)
        minimum_investment = Decimal(str(config.get("min_investment_usdt", "50")))
        if investment < minimum_investment:
            blockers.append(
                f"guarded investment {self._money(investment)} is below configured minimum {self._money(minimum_investment)}"
            )

        protected = {str(asset).upper() for asset in self.config.get("capital_sourcing", {}).get("protected_assets", [])}
        excluded = tuple(
            item.asset
            for item in portfolio.assets
            if item.asset.upper() not in allowed and item.total_value_usdt > 0
        )
        deployment_allowed = bool(assets) and not blockers
        summary = (
            f"Proposed {mode.lower()} Rebalancing Bot basket: "
            + ", ".join(f"{item.asset} {item.target_weight_pct}%" for item in assets)
            + f"; guarded investment {self._money(investment)} USDC."
        )
        if blockers:
            summary += " Deployment blocked: " + "; ".join(blocker.rstrip(".") for blocker in blockers) + "."

        return RebalancingBotRecommendation(
            enabled=True,
            recommended=deployment_allowed,
            deployment_allowed=deployment_allowed,
            mode=mode,
            threshold_pct=self._one_decimal(threshold),
            investment_usdt=self._money(investment),
            assets=tuple(assets),
            excluded_assets=excluded,
            blockers=tuple(blockers),
            manual_steps=self._manual_steps(assets, mode, threshold, investment, protected, deployment_allowed),
            summary=summary,
        )

    def _manual_steps(
        self,
        assets: list[RebalancingBotAsset],
        mode: str,
        threshold: Decimal,
        investment: Decimal,
        protected: set[str],
        deployment_allowed: bool,
    ) -> tuple[str, ...]:
        if not deployment_allowed:
            return (
                "Do not create a Rebalancing Bot while any deployment blocker remains.",
                "Resolve the WBETH/ETH decision or funding minimum, then rerun the assistant.",
            )
        allocation = ", ".join(f"{item.asset} {item.target_weight_pct}%" for item in assets)
        protected_note = ", ".join(sorted(protected)) or "none"
        return (
            "Open Binance Home > Trading Bots > Rebalancing Bot.",
            f"Choose Manual setup and add: {allocation}.",
            f"Select {mode.title()} rebalancing and set the threshold to {self._one_decimal(threshold)}%.",
            f"Invest no more than {self._money(investment)} USDC-equivalent.",
            "Fund the bot from its separate USDC allocation; let Binance acquire the configured ETH share inside the bot.",
            "Keep existing WBETH outside the bot and do not convert or sell it automatically.",
            f"Do not fund it by automatically selling protected assets ({protected_note}).",
            "Review Binance minimum allocation and investment requirements before confirming.",
            "Record the created bot parameters in the local strategy registry before the next run.",
        )

    def _balanced_weights(self, weights: list[Decimal]) -> list[Decimal]:
        rounded = [self._one_decimal(value) for value in weights]
        if rounded:
            rounded[-1] += Decimal("100.0") - sum(rounded, Decimal("0"))
        return rounded

    def _empty(self, summary: str) -> RebalancingBotRecommendation:
        return RebalancingBotRecommendation(
            enabled=False,
            recommended=False,
            deployment_allowed=False,
            mode="",
            threshold_pct=Decimal("0"),
            investment_usdt=Decimal("0"),
            assets=(),
            excluded_assets=(),
            blockers=(summary,),
            manual_steps=(),
            summary=summary,
        )

    def _money(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _one_decimal(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
