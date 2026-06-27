from __future__ import annotations

from trading_agent.user_profile import UserProfile

from .models import FirstPortfolioPlanSnapshot


class FirstPortfolioPlanner:
    def plan(self, profile: UserProfile) -> FirstPortfolioPlanSnapshot:
        if profile.onboarding_path != "FIRST_PORTFOLIO":
            return FirstPortfolioPlanSnapshot(
                available=False,
                summary="First portfolio planning is available after selecting Build my first portfolio.",
                funding=(),
                allocation=(),
                steps=(),
                notes=(),
            )

        investment = profile.planned_deposit_amount or self._default_investment(profile.management_style)
        reserve_amount = investment * profile.reserve_pct / 100
        deployable = investment - reserve_amount
        allocation = self._allocation(profile.management_style, deployable, profile.base_currency)
        summary = (
            f"Start with {investment:.0f} {profile.base_currency}: keep {reserve_amount:.0f} "
            f"{profile.base_currency} as reserve and deploy about {deployable:.0f} {profile.base_currency} gradually."
        )
        return FirstPortfolioPlanSnapshot(
            available=True,
            summary=summary,
            funding=self._funding(profile, investment, reserve_amount, deployable),
            allocation=allocation,
            steps=self._steps(profile),
            notes=self._notes(profile, deployable),
        )

    def _default_investment(self, style: str) -> float:
        if style == "ACTIVE":
            return 600.0
        if style == "BALANCED":
            return 400.0
        return 250.0

    def _allocation(self, style: str, deployable: float, currency: str) -> tuple[dict[str, str], ...]:
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
                "amount": f"{deployable * weight / 100:.0f} {currency}",
                "role": self._role(asset),
            }
            for asset, weight in weights
        )

    def _funding(self, profile: UserProfile, investment: float, reserve_amount: float, deployable: float) -> tuple[dict[str, str], ...]:
        return (
            {
                "name": "Deposit",
                "value": f"{investment:.0f} {profile.base_currency}",
                "detail": "Suggested first funding amount before any automation.",
            },
            {
                "name": "Reserve",
                "value": f"{reserve_amount:.0f} {profile.base_currency}",
                "detail": "Keep this liquid; do not allocate it to bots or trades.",
            },
            {
                "name": "Initial deployment",
                "value": f"{deployable:.0f} {profile.base_currency}",
                "detail": "Split into the proposed basket over one or more manual buys.",
            },
        )

    def _steps(self, profile: UserProfile) -> tuple[dict[str, str], ...]:
        cadence = profile.run_cadence.replace("_", " ").lower()
        return (
            {
                "name": "Fund Binance",
                "value": "Manual",
                "detail": f"Deposit {profile.base_currency} or EUR, then convert funding to {profile.base_currency}.",
            },
            {
                "name": "Buy basket",
                "value": "Manual",
                "detail": "Buy the suggested assets manually first; Coinductor can analyze after read-only API is connected.",
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
                "detail": "This planner never places orders; it prepares a human-readable starting plan.",
            },
        )

    def _role(self, asset: str) -> str:
        if asset in {"BTC", "ETH"}:
            return "Core"
        if asset == "BNB":
            return "Utility"
        return "Growth"
