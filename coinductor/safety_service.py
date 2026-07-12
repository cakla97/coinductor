from __future__ import annotations

from pathlib import Path

from trading_agent.safety_state import SafetyState, SafetyStateStore

from .models import SafetySnapshot


class SafetyService:
    def __init__(self, path: str | Path = "state/app_safety_state.toml"):
        self.store = SafetyStateStore(path)

    def inspect(self) -> SafetySnapshot:
        state = self.store.load()
        checks = (
            {
                "name": "Orders",
                "status": "LOCKED" if not state.allows_live_submit else "AVAILABLE",
                "detail": "Live order submit is disabled" if not state.allows_live_submit else "Guarded live submit workflows may be shown",
            },
            {
                "name": "Mainnet preview",
                "status": "LOCKED" if not state.allows_live_preview else "AVAILABLE",
                "detail": "Preview remains hidden until PREVIEW_ONLY" if not state.allows_live_preview else "Preview-only mainnet checks are available",
            },
            {
                "name": "Onboarding",
                "status": "SAFE",
                "detail": "Wizard steps cannot place orders or change exchange state.",
            },
        )
        return SafetySnapshot(
            stage=state.stage,
            label=state.stage.replace("_", " ").title(),
            detail=state.detail,
            allows_live_preview=state.allows_live_preview,
            allows_live_submit=state.allows_live_submit,
            checks=checks,
        )

    def transition(self, target: str, confirmation: str, *, live_key_verified: bool) -> SafetySnapshot:
        current = self.store.load().stage
        target = target.upper()
        requirements = {
            "PREVIEW_ONLY": ("SETUP", "ENABLE_MAINNET_PREVIEW", False),
            "ARMED": ("PREVIEW_ONLY", "ARM_GUARDED_ACTIONS", True),
            "LIVE_ENABLED": ("ARMED", "ENABLE_LIVE_GUARDED_SUBMIT", True),
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
