from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .models import Balance, CapitalSourcePlanItem, CapitalSourcingPlan, PortfolioAnalysis


class CapitalSourcingAdvisor:
    def __init__(self, config: dict):
        self.config = config

    def plan(self, balances: list[Balance], portfolio: PortfolioAnalysis, needed_usdt: Decimal) -> CapitalSourcingPlan:
        quote_asset = self._quote_asset()
        available_usdt = self._available_quote(balances, quote_asset)
        missing = max(Decimal("0"), needed_usdt - available_usdt)
        if not self.config.get("capital_sourcing", {}).get("enabled", False):
            return self._empty(needed_usdt, available_usdt, missing, quote_asset, "Capital sourcing advisor is disabled.")
        if missing <= 0:
            return self._empty(needed_usdt, available_usdt, missing, quote_asset, "No extra capital source is needed.")

        items: list[CapitalSourcePlanItem] = []
        remaining = missing
        max_per_run = Decimal(str(self.config["capital_sourcing"]["max_source_value_usdt_per_run"]))
        allowed = set(self.config["capital_sourcing"].get("allowed_source_assets", []))
        protected = set(self.config["capital_sourcing"].get("protected_assets", []))
        min_remaining = Decimal(str(self.config["capital_sourcing"]["min_remaining_value_usdt_per_asset"]))

        candidates = [
            asset
            for asset in portfolio.assets
            if asset.asset in allowed
            and asset.asset not in protected
            and asset.total_value_usdt > min_remaining
        ]
        candidates.sort(key=lambda asset: self._candidate_score(asset), reverse=True)

        budget_remaining = max_per_run
        for candidate in candidates:
            if remaining <= 0 or budget_remaining <= 0:
                break
            max_from_asset = max(Decimal("0"), candidate.total_value_usdt - min_remaining)
            value = min(remaining, budget_remaining, max_from_asset)
            if value <= 0:
                continue
            items.append(
                CapitalSourcePlanItem(
                    asset=candidate.asset,
                    action=f"Consider manually selling up to {self._money(value)} USDT-equivalent worth of {candidate.asset} for {quote_asset}.",
                    value_usdt=self._money(value),
                    reason=self._reason(candidate.rebalance_action),
                )
            )
            remaining -= value
            budget_remaining -= value

        if not items:
            return CapitalSourcingPlan(
                needed_usdt=self._money(needed_usdt),
                available_usdt=self._money(available_usdt),
                missing_usdt=self._money(missing),
                quote_asset=quote_asset,
                recommended=False,
                summary=f"Additional {quote_asset} is needed, but no allowed source asset has enough non-protected value.",
                items=(),
            )

        covered = missing - max(Decimal("0"), remaining)
        summary = f"Manual capital sourcing can cover about {self._money(covered)} {quote_asset} of the {self._money(missing)} {quote_asset} gap."
        if remaining > 0:
            summary += f" Remaining uncovered gap: {self._money(remaining)} {quote_asset}."
        return CapitalSourcingPlan(
            needed_usdt=self._money(needed_usdt),
            available_usdt=self._money(available_usdt),
            missing_usdt=self._money(missing),
            quote_asset=quote_asset,
            recommended=True,
            summary=summary,
            items=tuple(items),
        )

    def _available_quote(self, balances: list[Balance], quote_asset: str) -> Decimal:
        for balance in balances:
            if balance.asset == quote_asset:
                return balance.spot_free + balance.flexible_amount
        return Decimal("0")

    def _candidate_score(self, asset) -> tuple[int, Decimal]:
        action_score = 2 if asset.rebalance_action == "REDUCE" else 1 if asset.rebalance_action == "NO_TARGET" else 0
        return (action_score, asset.total_value_usdt)

    def _reason(self, rebalance_action: str) -> str:
        if rebalance_action == "REDUCE":
            return "Asset is above its target allocation and is allowed as a capital source."
        if rebalance_action == "NO_TARGET":
            return "Asset has no configured target allocation and is allowed as a capital source."
        return "Asset is allowed as a capital source, but it is not overweight."

    def _empty(self, needed_usdt: Decimal, available_usdt: Decimal, missing_usdt: Decimal, quote_asset: str, summary: str) -> CapitalSourcingPlan:
        return CapitalSourcingPlan(
            needed_usdt=self._money(needed_usdt),
            available_usdt=self._money(available_usdt),
            missing_usdt=self._money(missing_usdt),
            quote_asset=quote_asset,
            recommended=False,
            summary=summary,
            items=(),
        )

    def _money(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _quote_asset(self) -> str:
        return str(self.config.get("live_confirm", {}).get("quote_asset", self.config.get("app", {}).get("base_currency", "USDT"))).upper()
