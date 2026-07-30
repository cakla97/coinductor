from __future__ import annotations

from trading_agent.locale_profile import LOCALE_PROFILES, LocaleProfile, locale_profile, translated
from trading_agent.user_profile import UserProfile

from .models import FirstPortfolioPlanSnapshot
from .service_strings import service_text


# Which locale's translations to read prose from, given the language the reader
# picked. Deliberately separate from profile.locale: that one decides currency
# and starting budget, which are regional facts and not a language. Someone in
# Czechia reading English still deposits CZK.
_PROSE_LOCALE = {"cs": "cs-CZ", "en": "en-US"}


class FirstPortfolioPlanner:
    def plan(self, profile: UserProfile, language: str = "en") -> FirstPortfolioPlanSnapshot:
        language = "cs" if str(language).strip().lower().startswith("cs") else "en"
        locale = locale_profile(profile.locale)
        prose = self._prose_locale(language)
        if profile.onboarding_path != "FIRST_PORTFOLIO":
            return FirstPortfolioPlanSnapshot(
                available=False,
                summary=translated(prose, "planner.unavailable"),
                funding=(),
                allocation=(),
                steps=(),
                notes=(),
            )

        investment = profile.planned_deposit_amount or locale.default_starting_budget
        reserve_amount = investment * profile.reserve_pct / 100
        deployable = investment - reserve_amount
        allocation = self._allocation(profile.management_style, locale.funding_currency, language)
        summary = translated(
            prose,
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
            funding=self._funding(locale, prose, language, investment, reserve_amount, deployable),
            allocation=allocation,
            steps=self._steps(profile, locale, prose, language),
            notes=self._notes(profile, deployable, prose, language),
        )

    def _prose_locale(self, language: str) -> LocaleProfile:
        return LOCALE_PROFILES[_PROSE_LOCALE.get(language, "en-US")]

    def _allocation(self, style: str, funding_currency: str, language: str) -> tuple[dict[str, object], ...]:
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
                "targetPct": weight,
                "amount": service_text("first_plan_share_of_converted", language).format(
                    pct=weight, funding=funding_currency
                ),
                "role": self._role(asset, language),
            }
            for asset, weight in weights
        )

    def _funding(
        self,
        locale: LocaleProfile,
        prose: LocaleProfile,
        language: str,
        investment: float,
        reserve_amount: float,
        deployable: float,
    ) -> tuple[dict[str, str], ...]:
        return (
            {
                "name": service_text("first_plan_funding_deposit", language),
                "value": f"{investment:.0f} {locale.fiat_currency}",
                "detail": translated(prose, "funding.deposit.detail"),
            },
            {
                "name": service_text("first_plan_funding_reserve", language),
                "value": f"{reserve_amount:.0f} {locale.fiat_currency}",
                "detail": translated(prose, "funding.reserve.detail"),
            },
            {
                "name": service_text("first_plan_funding_deployment", language),
                "value": f"{deployable:.0f} {locale.fiat_currency} -> {locale.funding_currency}",
                "detail": translated(prose, "funding.deployment.detail", funding=locale.funding_currency),
            },
        )

    def _steps(
        self, profile: UserProfile, locale: LocaleProfile, prose: LocaleProfile, language: str
    ) -> tuple[dict[str, str], ...]:
        manual = service_text("first_plan_value_manual", language)
        return (
            {
                "name": service_text("first_plan_step_fund", language),
                "value": manual,
                "detail": translated(
                    prose, "steps.fund.detail", fiat=locale.fiat_currency, funding=locale.funding_currency
                ),
            },
            {
                "name": service_text("first_plan_step_buy", language),
                "value": manual,
                "detail": translated(prose, "steps.buy.detail"),
            },
            {
                "name": service_text("first_plan_step_earn", language),
                "value": service_text("first_plan_value_optional", language),
                "detail": service_text("first_plan_step_earn_detail", language),
            },
            {
                "name": service_text("first_plan_step_rhythm", language),
                # The cadence values already have their own translations, used
                # wherever else a cadence is shown.
                "value": service_text(f"cadence_{profile.run_cadence.lower()}", language),
                "detail": service_text("first_plan_step_rhythm_detail", language),
            },
        )

    def _notes(
        self, profile: UserProfile, deployable: float, prose: LocaleProfile, language: str
    ) -> tuple[dict[str, str], ...]:
        bot_key = "first_plan_note_rebalancing_ready" if deployable >= 200 else "first_plan_note_rebalancing_below_minimum"
        grid_key = "first_plan_note_grid_later" if profile.use_grid else "first_plan_note_grid_disabled"
        later = service_text("first_plan_value_later", language)
        return (
            {
                "name": service_text("first_plan_note_rebalancing", language),
                "value": later,
                "detail": service_text(bot_key, language),
            },
            {
                "name": service_text("first_plan_note_grid", language),
                "value": later,
                "detail": service_text(grid_key, language),
            },
            {
                "name": service_text("first_plan_note_execution", language),
                "value": service_text("first_plan_value_manual_first", language),
                "detail": translated(prose, "notes.execution.detail"),
            },
        )

    def _role(self, asset: str, language: str) -> str:
        if asset in {"BTC", "ETH"}:
            return service_text("first_plan_role_core", language)
        if asset == "BNB":
            return service_text("first_plan_role_utility", language)
        return service_text("first_plan_role_growth", language)
