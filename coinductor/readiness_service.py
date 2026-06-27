from __future__ import annotations

from .models import DesktopSnapshot, ReadinessSnapshot, SafetySnapshot, SetupSnapshot, UserProfileSnapshot


class ReadinessService:
    def inspect(
        self,
        setup: SetupSnapshot,
        user_profile: UserProfileSnapshot,
        safety: SafetySnapshot,
        desktop: DesktopSnapshot,
        connection_status: str = "Not checked",
    ) -> ReadinessSnapshot:
        steps = [
            self._profile_step(user_profile),
            self._binance_step(setup, connection_status),
            self._classification_step(desktop),
            self._preview_step(safety),
            self._live_step(safety),
        ]
        open_steps = [step for step in steps if step["status"] != "READY"]
        next_step = open_steps[0]["detail"] if open_steps else "All personal-stage readiness gates are satisfied."
        ready_count = len(steps) - len(open_steps)
        summary = f"{ready_count}/{len(steps)} readiness step(s) ready"
        return ReadinessSnapshot(summary=summary, next_step=next_step, steps=tuple(steps))

    def _profile_step(self, user_profile: UserProfileSnapshot) -> dict[str, str]:
        if user_profile.configured:
            return {
                "name": "Profile",
                "status": "READY",
                "detail": "Onboarding profile is configured.",
                "action": "Review when your risk preference changes.",
            }
        return {
            "name": "Profile",
            "status": "NEXT",
            "detail": "Choose safe defaults or Guide me before relying on recommendations.",
            "action": "Use Settings > Guide me.",
        }

    def _binance_step(self, setup: SetupSnapshot, connection_status: str) -> dict[str, str]:
        credential = next((item for item in setup.checks if item["name"] == "Binance read-only"), None)
        has_keys = credential is not None and credential["status"] == "PASS"
        if connection_status == "Connected":
            return {
                "name": "Binance read-only",
                "status": "READY",
                "detail": "Read-only API connection has been verified.",
                "action": "Recheck only after changing API keys.",
            }
        if has_keys:
            return {
                "name": "Binance read-only",
                "status": "NEXT",
                "detail": "Read-only keys exist but the connection check has not passed in this session.",
                "action": "Run the Binance read-only check.",
            }
        return {
            "name": "Binance read-only",
            "status": "BLOCKED",
            "detail": "Read-only API keys are required for real portfolio analysis.",
            "action": "Create read-only Binance keys and add them to .env.",
        }

    def _classification_step(self, desktop: DesktopSnapshot) -> dict[str, str]:
        if desktop.portfolio_assets:
            return {
                "name": "Portfolio classification",
                "status": "READY",
                "detail": f"{len(desktop.portfolio_assets)} tracked asset(s) loaded from the latest real run.",
                "action": "Review manual role overrides if needed.",
            }
        return {
            "name": "Portfolio classification",
            "status": "NEXT",
            "detail": "No real portfolio classification has been loaded yet.",
            "action": "Run initial classification after read-only access is ready.",
        }

    def _preview_step(self, safety: SafetySnapshot) -> dict[str, str]:
        if safety.allows_live_preview:
            return {
                "name": "Mainnet preview",
                "status": "READY",
                "detail": "Mainnet execution previews may be shown, but orders remain blocked.",
                "action": "Use preview runs before any live action.",
            }
        return {
            "name": "Mainnet preview",
            "status": "LOCKED",
            "detail": "Safety stage must reach PREVIEW_ONLY before mainnet previews are shown.",
            "action": "Complete setup and testnet checks first.",
        }

    def _live_step(self, safety: SafetySnapshot) -> dict[str, str]:
        if safety.allows_live_submit:
            return {
                "name": "Guarded live execution",
                "status": "READY",
                "detail": "Guarded live submit workflows may be exposed.",
                "action": "Keep limits and confirmations enabled.",
            }
        return {
            "name": "Guarded live execution",
            "status": "LOCKED",
            "detail": "Live submit stays locked until explicit safety stage promotion.",
            "action": "Do not unlock before repeated preview/testnet confidence.",
        }
