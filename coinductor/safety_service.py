from __future__ import annotations

from pathlib import Path

from trading_agent.safety_state import SafetyState, SafetyStateStore

from .models import SafetySnapshot
from .service_strings import service_text


class SafetyService:
    def __init__(self, path: str | Path = "state/app_safety_state.toml", language: str = "en"):
        self.store = SafetyStateStore(path)
        self.language = language
        # Set from the onboarding profile: RECOMMEND_ONLY vetoes every submit.
        # It can only ever subtract from what the safety stage already allows,
        # so the stage remains the hard floor and this is a second lock on top.
        self.automation_allows_submit = True

    def _t(self, key: str) -> str:
        return service_text(key, self.language)

    def inspect(self) -> SafetySnapshot:
        state = self.store.load()
        t = self._t
        allows_submit = state.allows_live_submit and self.automation_allows_submit
        # Say which of the two locks is the one holding, so a user who armed the
        # stage is not left wondering why the submit buttons stayed away.
        if allows_submit:
            orders_detail = t("safety_check_orders_available")
        elif state.allows_live_submit:
            orders_detail = t("safety_check_orders_recommend_only")
        else:
            orders_detail = t("safety_check_orders_locked")
        checks = (
            {
                "name": t("safety_check_orders"),
                "status": "LOCKED" if not allows_submit else "AVAILABLE",
                "detail": orders_detail,
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
            # When the profile vetoes, the stage's own wording would contradict
            # the lock sitting right under it, so say what actually applies.
            detail=t("safety_stage_detail_recommend_only")
            if state.allows_live_submit and not allows_submit
            else (t(f"safety_stage_detail_{state.stage}") or state.detail),
            allows_live_preview=state.allows_live_preview,
            allows_live_submit=allows_submit,
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
        # Refuse the arming step outright rather than let the stage advance into
        # a state the profile would silently veto anyway.
        if target == "LIVE_ENABLED" and not self.automation_allows_submit:
            raise ValueError(
                "Automation level is Recommendations only, so guarded live submit stays locked. "
                "Switch the profile to Guarded automation in the setup wizard first."
            )
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
