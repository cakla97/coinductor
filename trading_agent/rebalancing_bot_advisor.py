from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .decimal_utils import money
from .models import Balance, CapitalSourcePlanItem, CapitalSourcingPlan, PortfolioAnalysis, PortfolioAssetValuation, RebalancingBotAsset, RebalancingBotRecommendation


class RebalancingBotAdvisor:
    def __init__(self, config: dict):
        self.config = config

    def recommend(self, portfolio: PortfolioAnalysis, balances: list[Balance] | None = None) -> RebalancingBotRecommendation:
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
        allocation_method = str(config.get("allocation_method", "CUSTOM")).upper()
        auto_rebalance_mode = str(config.get("auto_rebalance_mode", "BY_RATIO")).upper()
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
        funding_plan = self._funding_plan(portfolio, balances or [], investment)
        if funding_plan.missing_usdt > 0:
            covered = sum((item.value_usdt for item in funding_plan.items), Decimal("0"))
            uncovered = max(Decimal("0"), funding_plan.missing_usdt - covered)
            if uncovered > 0:
                blockers.append(
                    f"safe funding plan leaves {self._money(uncovered)} USDC uncovered without using protected assets"
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
            manual_steps=self._manual_steps(
                assets,
                mode,
                threshold,
                investment,
                protected,
                deployment_allowed,
                funding_plan,
                allocation_method,
                auto_rebalance_mode,
                bool(config.get("trigger_price_enabled", False)),
                bool(config.get("stop_trigger_enabled", False)),
                bool(config.get("sell_all_coins_on_stop", False)),
            ),
            summary=summary,
            funding_plan=funding_plan,
        )

    def _manual_steps(
        self,
        assets: list[RebalancingBotAsset],
        mode: str,
        threshold: Decimal,
        investment: Decimal,
        protected: set[str],
        deployment_allowed: bool,
        funding_plan: CapitalSourcingPlan,
        allocation_method: str,
        auto_rebalance_mode: str,
        trigger_price_enabled: bool,
        stop_trigger_enabled: bool,
        sell_all_coins_on_stop: bool,
    ) -> tuple[str, ...]:
        allocation = ", ".join(f"{item.asset} {item.target_weight_pct}%" for item in assets)
        allocation_instruction = (
            "Select Equal as the starting layout, then manually edit the percentages"
            if allocation_method == "CUSTOM"
            else f"Select {allocation_method.replace('_', ' ').title()}"
        )
        form_steps = [
            f"After funding is complete: {allocation_instruction}; use {allocation}.",
            f"Enable Auto Rebalance, choose {auto_rebalance_mode.replace('_', ' ').title()}, and set {self._one_decimal(threshold)}%.",
            f"Trigger Price: {'ON' if trigger_price_enabled else 'OFF'} for the initial deployment.",
            f"Stop Trigger: {'ON' if stop_trigger_enabled else 'OFF'} for the initial deployment.",
            f"Sell All Coins on Stop: {'ON' if sell_all_coins_on_stop else 'OFF'} to avoid unintended liquidation on a manual stop.",
        ]
        if not deployment_allowed:
            steps = [
                "Do not create a Rebalancing Bot while any deployment blocker remains.",
            ]
            steps.extend(item.action for item in funding_plan.items)
            steps.append(funding_plan.summary)
            steps.extend(form_steps)
            return tuple(steps)
        protected_note = ", ".join(sorted(protected)) or "none"
        return (
            "Binance has no public API for creating trading bots, so Coinductor works out the parameters and you enter them yourself - it is not an unfinished feature.",
            "Open Binance Home > Trading Bots > Rebalancing Bot.",
            *form_steps,
            f"Invest no more than {self._money(investment)} USDC-equivalent.",
            "Fund the bot from its separate USDC allocation; let Binance acquire the configured ETH share inside the bot.",
            "Keep existing WBETH outside the bot and do not convert or sell it automatically.",
            f"Do not fund it by automatically selling protected assets ({protected_note}).",
            "Review Binance minimum allocation and investment requirements before confirming.",
            "Record the created bot parameters in the local strategy registry before the next run.",
        )

    def _funding_plan(
        self,
        portfolio: PortfolioAnalysis,
        balances: list[Balance],
        investment: Decimal,
    ) -> CapitalSourcingPlan:
        quote_asset = str(self.config.get("live_confirm", {}).get("quote_asset", "USDC")).upper()
        available = next(
            (
                balance.spot_free + balance.flexible_amount
                for balance in balances
                if balance.asset.upper() == quote_asset
            ),
            Decimal("0"),
        )
        missing = max(Decimal("0"), investment - available)
        funding = self.config.get("rebalancing_bot", {}).get("funding", {})
        priority = [str(asset).upper() for asset in funding.get("source_priority", [])]
        full_exit = {str(asset).upper() for asset in funding.get("full_exit_assets", [])}
        reserves = {str(asset).upper() for asset in funding.get("reserve_source_assets", [])}
        protected = {str(asset).upper() for asset in self.config.get("capital_sourcing", {}).get("protected_assets", [])}
        default_pct = Decimal(str(funding.get("max_source_pct_per_reserve_asset", "15"))) / Decimal("100")
        wld_pct = Decimal(str(funding.get("max_source_pct_wld", "30"))) / Decimal("100")
        min_remaining = Decimal(str(funding.get("min_remaining_value_usdt", "50")))
        by_asset = {item.asset.upper(): item for item in portfolio.assets}
        remaining = missing
        items: list[CapitalSourcePlanItem] = []

        for asset in priority:
            if remaining <= 0 or asset in protected or asset not in by_asset:
                continue
            valuation = by_asset[asset]
            if asset in full_exit:
                maximum = valuation.total_value_usdt
                reason = "Small legacy/speculative holding is configured for full conversion to fund the bot."
            elif asset in reserves:
                pct = wld_pct if asset == "WLD" else default_pct
                maximum = min(
                    valuation.total_value_usdt * pct,
                    max(Decimal("0"), valuation.total_value_usdt - min_remaining),
                )
                reason = "Reserve source is capped by percentage and minimum remaining-value limits."
            else:
                continue
            value = min(remaining, maximum)
            if value <= 0:
                continue
            remaining_value = valuation.total_value_usdt - value
            items.append(
                CapitalSourcePlanItem(
                    asset=asset,
                    action=f"Convert approximately {self._money(value)} USDC-equivalent of {asset} to {quote_asset}.",
                    value_usdt=self._money(value),
                    source_pct_of_asset=self._one_decimal(value / valuation.total_value_usdt * Decimal("100")),
                    remaining_value_usdt=self._money(remaining_value),
                    remaining_pct_of_asset=self._one_decimal(remaining_value / valuation.total_value_usdt * Decimal("100")),
                    reason=reason,
                )
            )
            remaining -= value

        covered = sum((item.value_usdt for item in items), Decimal("0"))
        uncovered = max(Decimal("0"), missing - covered)
        if missing <= 0:
            summary = f"Existing {quote_asset} balance fully covers the {self._money(investment)} setup."
        elif uncovered <= 0:
            summary = (
                f"Existing {self._money(available)} {quote_asset} plus proposed conversions cover "
                f"the {self._money(investment)} investment."
            )
        else:
            summary = (
                f"Use existing {self._money(available)} {quote_asset} and convert about {self._money(covered)} "
                f"from allowed sources. Remaining gap: {self._money(uncovered)} {quote_asset}; "
                "do not fill it from protected BTC, ETH, WBETH, or BNB without a separate policy decision."
            )
        return CapitalSourcingPlan(
            needed_usdt=self._money(investment),
            available_usdt=self._money(available),
            missing_usdt=self._money(missing),
            quote_asset=quote_asset,
            recommended=bool(items),
            summary=summary,
            items=tuple(items),
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
            funding_plan=None,
        )

    def _money(self, value: Decimal) -> Decimal:
        return money(value)

    def _one_decimal(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
