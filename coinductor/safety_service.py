from __future__ import annotations

from pathlib import Path

from trading_agent.safety_state import SafetyStateStore

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
