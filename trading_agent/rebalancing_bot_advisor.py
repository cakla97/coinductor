from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .decimal_utils import money
from .manual_steps import ManualStep, render_manual_step, render_manual_steps
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
        # Same as the grid: blockers have their own field and are shown on the
        # card, in the next-review panel and in the report. Repeating them here
        # printed the same sentence three times on one screen.

        steps = self._manual_steps(
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
        )
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
            manual_steps=render_manual_steps(steps),
            summary=summary,
            funding_plan=funding_plan,
            manual_step_specs=steps,
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
    ) -> tuple[ManualStep, ...]:
        allocation = ", ".join(f"{item.asset} {item.target_weight_pct}%" for item in assets)
        form_steps = [
            ManualStep("rebalance_allocation_custom", {"allocation": allocation})
            if allocation_method == "CUSTOM"
            else ManualStep(
                "rebalance_allocation_preset",
                {"method": allocation_method.replace("_", " ").title(), "allocation": allocation},
            ),
            ManualStep(
                "rebalance_auto_rebalance",
                {
                    "mode": auto_rebalance_mode.replace("_", " ").title(),
                    "threshold": str(self._one_decimal(threshold)),
                },
            ),
            ManualStep("rebalance_trigger_price", {"state": "ON" if trigger_price_enabled else "OFF"}),
            ManualStep("rebalance_stop_trigger", {"state": "ON" if stop_trigger_enabled else "OFF"}),
            ManualStep(
                "rebalance_sell_all_on_stop",
                {"state": "ON" if sell_all_coins_on_stop else "OFF"},
            ),
        ]
        if not deployment_allowed:
            # A funding shortfall is a blocker the reader can actually clear, so
            # the steps stay: first how to close the gap, then the parameters to
            # use afterwards. Without the divider the numbered list read as an
            # instruction to create the bot now, contradicting step 1.
            steps = [ManualStep("rebalance_blocked_do_not_create")]
            steps.extend(
                item.action_step or ManualStep(item.action) for item in funding_plan.items
            )
            if funding_plan.summary_step is not None:
                steps.append(funding_plan.summary_step)
            steps.append(ManualStep("rebalance_blocked_divider"))
            steps.extend(form_steps)
            return tuple(steps)
        protected_note = ", ".join(sorted(protected)) or "none"
        return (
            ManualStep("bots_manual_because_no_api"),
            ManualStep("rebalance_open_menu"),
            *form_steps,
            ManualStep("rebalance_invest_cap", {"investment": str(self._money(investment))}),
            ManualStep("rebalance_fund_separately"),
            ManualStep("rebalance_keep_wbeth"),
            ManualStep("rebalance_do_not_sell_protected", {"protected": protected_note}),
            ManualStep("rebalance_review_minimums"),
            ManualStep("rebalance_record_locally"),
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
            action_step = ManualStep(
                "funding_convert",
                {"value": str(self._money(value)), "asset": asset, "quote": quote_asset},
            )
            items.append(
                CapitalSourcePlanItem(
                    asset=asset,
                    action=render_manual_step(action_step),
                    action_step=action_step,
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
            summary_step = ManualStep(
                "funding_summary_balance_covers",
                {"quote": quote_asset, "investment": str(self._money(investment))},
            )
        elif uncovered <= 0:
            summary_step = ManualStep(
                "funding_summary_conversions_cover",
                {
                    "available": str(self._money(available)),
                    "quote": quote_asset,
                    "investment": str(self._money(investment)),
                },
            )
        else:
            summary_step = ManualStep(
                "funding_summary_gap",
                {
                    "available": str(self._money(available)),
                    "quote": quote_asset,
                    "covered": str(self._money(covered)),
                    "uncovered": str(self._money(uncovered)),
                },
            )
        return CapitalSourcingPlan(
            needed_usdt=self._money(investment),
            available_usdt=self._money(available),
            missing_usdt=self._money(missing),
            quote_asset=quote_asset,
            recommended=bool(items),
            summary=render_manual_step(summary_step),
            items=tuple(items),
            summary_step=summary_step,
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
