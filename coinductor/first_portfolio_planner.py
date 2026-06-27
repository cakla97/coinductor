from __future__ import annotations

from trading_agent.locale_profile import locale_profile, translated
from trading_agent.user_profile import UserProfile

from .models import FirstPortfolioPlanSnapshot


class FirstPortfolioPlanner:
    def plan(self, profile: UserProfile) -> FirstPortfolioPlanSnapshot:
        locale = locale_profile(profile.locale)
        if profile.onboarding_path != "FIRST_PORTFOLIO":
            return FirstPortfolioPlanSnapshot(
                available=False,
                summary=translated(locale, "planner.unavailable"),
                funding=(),
                allocation=(),
                steps=(),
                notes=(),
            )

        investment = profile.planned_deposit_amount or locale.default_starting_budget
        reserve_amount = investment * profile.reserve_pct / 100
        deployable = investment - reserve_amount
        allocation = self._allocation(profile.management_style, locale.funding_currency)
        summary = translated(
            locale,
            "planner.summary",
            investment=investment,
            reserve=reserve_amount,
            deployable=deployable,
            fiat=locale.fiat_currency,
            funding=locale.funding_currency,
        )
        return FirstPortfolioPlanSnapshot(
            available=True,
            summary=summary,
            funding=self._funding(profile, investment, reserve_amount, deployable),
            allocation=allocation,
            steps=self._steps(profile),
            notes=self._notes(profile, deployable),
        )

    def _allocation(self, style: str, funding_currency: str) -> tuple[dict[str, str], ...]:
        if style == "ACTIVE":
            weights = (("BTC", 35), ("ETH", 25), ("SOL", 20), ("BNB", 10), ("WLD", 10))
        elif style == "BALANCED":
            weights = (("BTC", 40), ("ETH", 30), ("SOL", 15), ("BNB", 10), ("WLD", 5))
        else:
            weights = (("BTC", 50), ("ETH", 30), ("BNB", 10), ("SOL", 10))
        return tuple(
            {
                "asset": asset,
                "target": f"{weight}%",
                "amount": f"{weight}% of converted {funding_currency}",
                "role": self._role(asset),
            }
            for asset, weight in weights
        )

    def _funding(self, profile: UserProfile, investment: float, reserve_amount: float, deployable: float) -> tuple[dict[str, str], ...]:
        locale = locale_profile(profile.locale)
        return (
            {
                "name": "Deposit",
                "value": f"{investment:.0f} {locale.fiat_currency}",
                "detail": translated(locale, "funding.deposit.detail"),
            },
            {
                "name": "Reserve",
                "value": f"{reserve_amount:.0f} {locale.fiat_currency}",
                "detail": translated(locale, "funding.reserve.detail"),
            },
            {
                "name": "Initial deployment",
                "value": f"{deployable:.0f} {locale.fiat_currency} -> {locale.funding_currency}",
                "detail": translated(locale, "funding.deployment.detail", funding=locale.funding_currency),
            },
        )

    def _steps(self, profile: UserProfile) -> tuple[dict[str, str], ...]:
        locale = locale_profile(profile.locale)
        cadence = profile.run_cadence.replace("_", " ").lower()
        return (
            {
                "name": "Fund Binance",
                "value": "Manual",
                "detail": translated(locale, "steps.fund.detail", fiat=locale.fiat_currency, funding=locale.funding_currency),
            },
            {
                "name": "Buy basket",
                "value": "Manual",
                "detail": translated(locale, "steps.buy.detail"),
            },
            {
                "name": "Enable Earn",
                "value": "Optional",
                "detail": "Flexible Earn is fine for idle reserve, but keep enough liquid for planned actions.",
            },
            {
                "name": "Review rhythm",
                "value": cadence.title(),
                "detail": "Run Coinductor on this rhythm before enabling more active automation.",
            },
        )

    def _notes(self, profile: UserProfile, deployable: float) -> tuple[dict[str, str], ...]:
        locale = locale_profile(profile.locale)
        bot_note = "Rebalancing bot can be considered after at least 200 USDC is available for its basket."
        if deployable < 200:
            bot_note = "Rebalancing bot is below the usual 200 USDC minimum; start with manual basket review."
        grid_note = "Grid bot stays disabled for the first portfolio plan."
        if profile.use_grid:
            grid_note = "Grid bot can be reviewed later, after the first portfolio has a stable tracked baseline."
        return (
            {
                "name": "Rebalancing",
                "value": "Later",
                "detail": bot_note,
            },
            {
                "name": "Grid",
                "value": "Later",
                "detail": grid_note,
            },
            {
                "name": "Execution",
                "value": "Manual first",
                "detail": translated(locale, "notes.execution.detail"),
            },
        )

    def _role(self, asset: str) -> str:
        if asset in {"BTC", "ETH"}:
            return "Core"
        if asset == "BNB":
            return "Utility"
        return "Growth"
