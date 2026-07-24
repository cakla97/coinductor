from __future__ import annotations

from .models import DesktopSnapshot, ReadinessSnapshot, SafetySnapshot, SetupSnapshot, UserProfileSnapshot
from .service_strings import service_text


class ReadinessService:
    """Derives the next readiness step from the other snapshots.

    Steps carry a stable ``code`` alongside their translated ``name``: matching
    on the display name would break as soon as a name is translated. The same
    applies to ``connection_status``, which the controller keeps in English
    because guarded-action gates compare it verbatim.
    """

    def __init__(self, language: str = "en"):
        self.language = language

    def _t(self, key: str) -> str:
        return service_text(key, self.language)

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
        next_step = open_steps[0]["detail"] if open_steps else self._t("readiness_all_satisfied")
        action_code, action_label, action_enabled = self._next_action(steps, user_profile, desktop, connection_status)
        ready_count = len(steps) - len(open_steps)
        summary = self._t("readiness_summary").format(ready=ready_count, total=len(steps))
        return ReadinessSnapshot(
            summary=summary,
            next_step=next_step,
            action_code=action_code,
            action_label=action_label,
            action_enabled=action_enabled,
            steps=tuple(steps),
        )

    def _profile_step(self, user_profile: UserProfileSnapshot) -> dict[str, str]:
        name = self._t("readiness_step_profile")
        if user_profile.configured:
            return {
                "code": "PROFILE",
                "name": name,
                "status": "READY",
                "detail": self._t("readiness_profile_ready_detail"),
                "action": self._t("readiness_profile_ready_action"),
            }
        return {
            "code": "PROFILE",
            "name": name,
            "status": "NEXT",
            "detail": self._t("readiness_profile_next_detail"),
            "action": self._t("readiness_profile_next_action"),
        }

    def _binance_step(self, setup: SetupSnapshot, connection_status: str) -> dict[str, str]:
        credential = next((item for item in setup.checks if item.get("code") == "BINANCE_READONLY"), None)
        has_keys = credential is not None and credential["status"] == "PASS"
        name = self._t("readiness_step_binance")
        if connection_status == "Connected":
            return {
                "code": "BINANCE_READONLY",
                "name": name,
                "status": "READY",
                "detail": self._t("readiness_binance_ready_detail"),
                "action": self._t("readiness_binance_ready_action"),
            }
        if has_keys:
            return {
                "code": "BINANCE_READONLY",
                "name": name,
                "status": "NEXT",
                "detail": self._t("readiness_binance_next_detail"),
                "action": self._t("readiness_binance_next_action"),
            }
        return {
            "code": "BINANCE_READONLY",
            "name": name,
            "status": "BLOCKED",
            "detail": self._t("readiness_binance_blocked_detail"),
            "action": self._t("readiness_binance_blocked_action"),
        }

    def _classification_step(self, desktop: DesktopSnapshot) -> dict[str, str]:
        name = self._t("readiness_step_classification")
        if desktop.portfolio_assets:
            return {
                "code": "CLASSIFICATION",
                "name": name,
                "status": "READY",
                "detail": self._t("readiness_classification_ready_detail").format(
                    count=len(desktop.portfolio_assets)
                ),
                "action": self._t("readiness_classification_ready_action"),
            }
        return {
            "code": "CLASSIFICATION",
            "name": name,
            "status": "NEXT",
            "detail": self._t("readiness_classification_next_detail"),
            "action": self._t("readiness_classification_next_action"),
        }

    def _preview_step(self, safety: SafetySnapshot) -> dict[str, str]:
        name = self._t("readiness_step_preview")
        if safety.allows_live_preview:
            return {
                "code": "PREVIEW",
                "name": name,
                "status": "READY",
                "detail": self._t("readiness_preview_ready_detail"),
                "action": self._t("readiness_preview_ready_action"),
            }
        return {
            "code": "PREVIEW",
            "name": name,
            "status": "LOCKED",
            "detail": self._t("readiness_preview_locked_detail"),
            "action": self._t("readiness_preview_locked_action"),
        }

    def _live_step(self, safety: SafetySnapshot) -> dict[str, str]:
        name = self._t("readiness_step_live")
        if safety.allows_live_submit:
            return {
                "code": "LIVE",
                "name": name,
                "status": "READY",
                "detail": self._t("readiness_live_ready_detail"),
                "action": self._t("readiness_live_ready_action"),
            }
        return {
            "code": "LIVE",
            "name": name,
            "status": "LOCKED",
            "detail": self._t("readiness_live_locked_detail"),
            "action": self._t("readiness_live_locked_action"),
        }

    def _next_action(
        self,
        steps: list[dict[str, str]],
        user_profile: UserProfileSnapshot,
        desktop: DesktopSnapshot,
        connection_status: str,
    ) -> tuple[str, str, bool]:
        profile = self._step(steps, "PROFILE")
        binance = self._step(steps, "BINANCE_READONLY")
        classification = self._step(steps, "CLASSIFICATION")

        # Action codes are identifiers consumed by the assistant/controller;
        # only the labels are translated.
        if profile["status"] != "READY":
            return ("GUIDE_PROFILE", self._t("readiness_action_guide_me"), True)
        if binance["status"] == "NEXT":
            return ("CHECK_BINANCE", self._t("readiness_action_check_binance"), connection_status != "Checking")
        if binance["status"] == "BLOCKED":
            return ("OPEN_SETTINGS", self._t("readiness_action_add_keys"), False)
        if classification["status"] != "READY":
            return ("RUN_CLASSIFICATION", self._t("readiness_action_run_classification"), True)
        if user_profile.configured and desktop.portfolio_assets:
            return ("OPEN_PORTFOLIO", self._t("readiness_action_review_portfolio"), True)
        return ("NONE", self._t("readiness_action_none"), False)

    def _step(self, steps: list[dict[str, str]], code: str) -> dict[str, str]:
        return next(item for item in steps if item["code"] == code)
