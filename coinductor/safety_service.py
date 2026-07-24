from __future__ import annotations

from pathlib import Path

from trading_agent.safety_state import SafetyState, SafetyStateStore

from .models import SafetySnapshot
from .service_strings import service_text


class SafetyService:
    def __init__(self, path: str | Path = "state/app_safety_state.toml", language: str = "en"):
        self.store = SafetyStateStore(path)
        self.language = language

    def _t(self, key: str) -> str:
        return service_text(key, self.language)

    def inspect(self) -> SafetySnapshot:
        state = self.store.load()
        t = self._t
        checks = (
            {
                "name": t("safety_check_orders"),
                "status": "LOCKED" if not state.allows_live_submit else "AVAILABLE",
                "detail": t("safety_check_orders_locked")
                if not state.allows_live_submit
                else t("safety_check_orders_available"),
            },
            {
                "name": t("safety_check_preview"),
                "status": "LOCKED" if not state.allows_live_preview else "AVAILABLE",
                "detail": t("safety_check_preview_locked")
                if not state.allows_live_preview
                else t("safety_check_preview_available"),
            },
            {
                "name": t("safety_check_onboarding"),
                "status": "SAFE",
                "detail": t("safety_check_onboarding_detail"),
            },
        )
        return SafetySnapshot(
            stage=state.stage,
            # Display label only; state.stage stays the identifier everything
            # else compares against.
            label=t(f"safety_stage_label_{state.stage}") or state.stage.replace("_", " ").title(),
            # Resolved from the stage so a language switch re-renders it; the
            # persisted detail is the fallback for stages we do not describe.
            detail=t(f"safety_stage_detail_{state.stage}") or state.detail,
            allows_live_preview=state.allows_live_preview,
            allows_live_submit=state.allows_live_submit,
            checks=checks,
        )

    def transition(self, target: str, confirmation: str, *, live_key_verified: bool) -> SafetySnapshot:
        current = self.store.load().stage
        target = target.upper()
        requirements = {
            "PREVIEW_ONLY": ("SETUP", "Enable mainnet preview", False),
            "ARMED": ("PREVIEW_ONLY", "Arm guarded actions", True),
            "LIVE_ENABLED": ("ARMED", "Enable guarded live submit", True),
        }
        if target not in requirements:
            raise ValueError(f"Unsupported safety transition target: {target}")
        expected_current, expected_confirmation, needs_live_key = requirements[target]
        if current != expected_current:
            raise ValueError(f"Safety stage must be {expected_current} before moving to {target}; current stage is {current}.")
        if confirmation.strip() != expected_confirmation:
            raise ValueError(f"Confirmation text did not match {expected_confirmation}.")
        if needs_live_key and not live_key_verified:
            raise ValueError("Verify the live Binance API permissions in this app session before continuing.")
        detail = {
            "PREVIEW_ONLY": "Mainnet previews are available; all live submissions remain locked.",
            "ARMED": "Live credentials are verified and guarded actions are armed; final live submission remains locked.",
            "LIVE_ENABLED": "Guarded live submissions are enabled with fresh validation and explicit per-action confirmation.",
        }[target]
        self.store.save(SafetyState(stage=target, detail=detail))
        return self.inspect()

    def lock_live_submit(self) -> SafetySnapshot:
        self.store.save(
            SafetyState(
                stage="PREVIEW_ONLY",
                detail="Mainnet previews are available; live submissions were manually locked.",
            )
        )
        return self.inspect()
