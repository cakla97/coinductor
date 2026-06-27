from __future__ import annotations

from pathlib import Path

from trading_agent.locale_profile import locale_profile
from trading_agent.user_profile import UserProfile, UserProfileStore, safe_default_profile

from .models import UserProfileSnapshot


class UserProfileService:
    def __init__(self, path: str | Path = "state/user_profile.toml"):
        self.store = UserProfileStore(path)

    def inspect(self) -> UserProfileSnapshot:
        profile = self.store.load()
        if profile is None:
            return UserProfileSnapshot(
                configured=False,
                summary="No onboarding profile is configured yet. Safe defaults are available.",
                fields=(
                    {"name": "Profile", "value": "Not configured", "detail": "Use safe defaults or guided setup."},
                    {"name": "Safety", "value": "Conservative default", "detail": "Recommend-only until configured."},
                ),
                exchange_steps=self._exchange_steps("BINANCE", "EXISTING_PORTFOLIO"),
            )
        return self._snapshot(profile)

    def save_safe_default(self, onboarding_path: str) -> UserProfileSnapshot:
        return self._snapshot(self.store.save_safe_default(onboarding_path))

    def delete_profile(self) -> UserProfileSnapshot:
        self.store.delete()
        return self.inspect()

    def save_guided(
        self,
        onboarding_path: str,
        management_style: str,
        automation_level: str,
        run_cadence: str,
        base_currency: str,
        use_bots: bool,
        allow_spot_trades: bool,
        max_drawdown_comfort_pct: float,
        locale: str = "en-US",
        planned_deposit_amount: float = 0.0,
    ) -> UserProfileSnapshot:
        return self._snapshot(
            self.store.save_guided(
                onboarding_path=onboarding_path,
                management_style=management_style,
                automation_level=automation_level,
                run_cadence=run_cadence,
                base_currency=base_currency,
                use_bots=use_bots,
                allow_spot_trades=allow_spot_trades,
                max_drawdown_comfort_pct=max_drawdown_comfort_pct,
                locale=locale,
                planned_deposit_amount=planned_deposit_amount,
            )
        )

    def current_profile(self, fallback_onboarding_path: str = "EXISTING_PORTFOLIO") -> UserProfile:
        profile = self.store.load()
        if profile is not None and profile.onboarding_path == fallback_onboarding_path:
            return profile
        return safe_default_profile(fallback_onboarding_path)

    def _snapshot(self, profile: UserProfile) -> UserProfileSnapshot:
        locale = locale_profile(profile.locale)
        fields = (
            {"name": "Exchange", "value": profile.exchange, "detail": "Where the portfolio will be managed."},
            {"name": "Locale", "value": profile.locale, "detail": f"{locale.language_name}, {locale.region_name}."},
            {"name": "Path", "value": profile.onboarding_path, "detail": "Existing portfolio or first portfolio."},
            {"name": "Setup", "value": profile.setup_mode, "detail": "Safe defaults, guided, or advanced."},
            {"name": "Style", "value": profile.management_style, "detail": "Portfolio management intensity."},
            {"name": "Automation", "value": profile.automation_level, "detail": "How much the app may automate."},
            {"name": "Run cadence", "value": profile.run_cadence, "detail": "Suggested review rhythm."},
            {"name": "Fiat funding", "value": locale.fiat_currency, "detail": locale.fiat_to_funding_hint},
            {"name": "Funding currency", "value": profile.base_currency, "detail": "Internal strategy funding and reporting currency."},
            {"name": "Starting budget", "value": f"{profile.planned_deposit_amount:.0f} {locale.fiat_currency}" if profile.planned_deposit_amount else "Auto", "detail": "Used by first portfolio planner."},
            {"name": "Reserve", "value": f"{profile.reserve_pct:.0f}%", "detail": "Capital kept outside active strategy use."},
            {"name": "Drawdown comfort", "value": f"{profile.max_drawdown_comfort_pct:.0f}%", "detail": "Used for conservative strategy sizing."},
            {"name": "Spot trades", "value": "Allowed" if profile.allow_spot_trades else "Disabled", "detail": "Live execution still needs guard approval."},
            {"name": "Grid", "value": "Enabled" if profile.use_grid else "Disabled", "detail": "Manual Binance creation remains required."},
            {"name": "Rebalancing", "value": "Enabled" if profile.use_rebalancing else "Disabled", "detail": "Only when minimum capital and limits pass."},
        )
        return UserProfileSnapshot(
            configured=True,
            summary=profile.summary,
            fields=fields,
            exchange_steps=self._exchange_steps(profile.exchange, profile.onboarding_path),
        )

    def _exchange_steps(self, exchange: str, onboarding_path: str) -> tuple[dict[str, str], ...]:
        if exchange != "BINANCE":
            return (
                {"name": "Exchange", "value": exchange, "detail": "This exchange is planned but not supported yet."},
            )
        if onboarding_path == "FIRST_PORTFOLIO":
            return (
                {"name": "Create account", "value": "Manual", "detail": "Open a Binance account and complete identity verification."},
                {"name": "Deposit funds", "value": "Manual", "detail": "Deposit EUR or stablecoins; Coinductor can later recommend a USDC starting plan."},
                {"name": "API access", "value": "Required later", "detail": "Create read-only API keys before portfolio analysis."},
                {"name": "Test first", "value": "Recommended", "detail": "Use Testnet or preview-only flows before guarded mainnet actions."},
            )
        return (
            {"name": "Existing account", "value": "Assumed", "detail": "Account creation is skipped for existing Binance users."},
            {"name": "Read-only API", "value": "Next", "detail": "Connect read-only keys so Coinductor can inventory the portfolio."},
            {"name": "Classify assets", "value": "Next", "detail": "Review protected, funding, trading, Grid, and Rebalancing universes."},
        )
