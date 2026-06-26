from __future__ import annotations

from pathlib import Path

from trading_agent.user_profile import UserProfile, UserProfileStore

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
            )
        return self._snapshot(profile)

    def save_safe_default(self, onboarding_path: str) -> UserProfileSnapshot:
        return self._snapshot(self.store.save_safe_default(onboarding_path))

    def _snapshot(self, profile: UserProfile) -> UserProfileSnapshot:
        fields = (
            {"name": "Path", "value": profile.onboarding_path, "detail": "Existing portfolio or first portfolio."},
            {"name": "Setup", "value": profile.setup_mode, "detail": "Safe defaults, guided, or advanced."},
            {"name": "Style", "value": profile.management_style, "detail": "Portfolio management intensity."},
            {"name": "Automation", "value": profile.automation_level, "detail": "How much the app may automate."},
            {"name": "Run cadence", "value": profile.run_cadence, "detail": "Suggested review rhythm."},
            {"name": "Spot trades", "value": "Allowed" if profile.allow_spot_trades else "Disabled", "detail": "Live execution still needs guard approval."},
            {"name": "Grid", "value": "Enabled" if profile.use_grid else "Disabled", "detail": "Manual Binance creation remains required."},
            {"name": "Rebalancing", "value": "Enabled" if profile.use_rebalancing else "Disabled", "detail": "Only when minimum capital and limits pass."},
        )
        return UserProfileSnapshot(configured=True, summary=profile.summary, fields=fields)
