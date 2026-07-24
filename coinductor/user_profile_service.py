from __future__ import annotations

from pathlib import Path

from trading_agent.locale_profile import locale_profile
from trading_agent.user_profile import UserProfile, UserProfileStore, safe_default_profile

from .models import UserProfileSnapshot
from .service_strings import service_text


class UserProfileService:
    def __init__(self, path: str | Path = "state/user_profile.toml", language: str = "en"):
        self.store = UserProfileStore(path)
        self.language = language

    def _t(self, key: str) -> str:
        return service_text(key, self.language)

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
        t = self._t
        fields = (
            {"name": t("profile_field_exchange"), "value": profile.exchange, "detail": t("profile_field_exchange_detail")},
            {"name": t("profile_field_locale"), "value": profile.locale, "detail": f"{locale.language_name}, {locale.region_name}."},
            {"name": t("profile_field_path"), "value": profile.onboarding_path, "detail": t("profile_field_path_detail")},
            {"name": t("profile_field_setup"), "value": profile.setup_mode, "detail": t("profile_field_setup_detail")},
            {"name": t("profile_field_style"), "value": profile.management_style, "detail": t("profile_field_style_detail")},
            {"name": t("profile_field_automation"), "value": profile.automation_level, "detail": t("profile_field_automation_detail")},
            {"name": t("profile_field_cadence"), "value": profile.run_cadence, "detail": t("profile_field_cadence_detail")},
            {"name": t("profile_field_fiat"), "value": locale.fiat_currency, "detail": locale.fiat_to_funding_hint},
            {"name": t("profile_field_funding_currency"), "value": profile.base_currency, "detail": t("profile_field_funding_currency_detail")},
            {"name": t("profile_field_budget"), "value": f"{profile.planned_deposit_amount:.0f} {locale.fiat_currency}" if profile.planned_deposit_amount else t("profile_value_auto"), "detail": t("profile_field_budget_detail")},
            {"name": t("profile_field_reserve"), "value": f"{profile.reserve_pct:.0f}%", "detail": t("profile_field_reserve_detail")},
            {"name": t("profile_field_drawdown"), "value": f"{profile.max_drawdown_comfort_pct:.0f}%", "detail": t("profile_field_drawdown_detail")},
            {"name": t("profile_field_spot_trades"), "value": t("profile_value_allowed") if profile.allow_spot_trades else t("profile_value_disabled"), "detail": t("profile_field_spot_trades_detail")},
            {"name": t("profile_field_grid"), "value": t("profile_value_enabled") if profile.use_grid else t("profile_value_disabled"), "detail": t("profile_field_grid_detail")},
            {"name": t("profile_field_rebalancing"), "value": t("profile_value_enabled") if profile.use_rebalancing else t("profile_value_disabled"), "detail": t("profile_field_rebalancing_detail")},
        )
        return UserProfileSnapshot(
            configured=True,
            summary=profile.summary,
            fields=fields,
            exchange_steps=self._exchange_steps(profile.exchange, profile.onboarding_path),
        )

    def _exchange_steps(self, exchange: str, onboarding_path: str) -> tuple[dict[str, str], ...]:
        t = self._t
        if exchange != "BINANCE":
            return (
                {"name": t("exch_unsupported_name"), "value": exchange, "detail": t("exch_unsupported_detail")},
            )
        if onboarding_path == "FIRST_PORTFOLIO":
            return (
                {"name": t("exch_create_account"), "value": t("exch_value_manual"), "detail": t("exch_create_account_detail")},
                {"name": t("exch_deposit"), "value": t("exch_value_manual"), "detail": t("exch_deposit_detail")},
                {"name": t("exch_api_access"), "value": t("exch_value_required_later"), "detail": t("exch_api_access_detail")},
                {"name": t("exch_test_first"), "value": t("exch_value_recommended"), "detail": t("exch_test_first_detail")},
            )
        return (
            {"name": t("exch_existing_account"), "value": t("exch_value_assumed"), "detail": t("exch_existing_account_detail")},
            {"name": t("exch_readonly_api"), "value": t("exch_value_next"), "detail": t("exch_readonly_api_detail")},
            {"name": t("exch_classify"), "value": t("exch_value_next"), "detail": t("exch_classify_detail")},
        )
