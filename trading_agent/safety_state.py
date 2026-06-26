from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


SAFETY_STAGES = (
    "SETUP",
    "READ_ONLY_CONNECTED",
    "TESTNET_READY",
    "PREVIEW_ONLY",
    "ARMED",
    "LIVE_ENABLED",
)

STAGE_ORDER = {stage: index for index, stage in enumerate(SAFETY_STAGES)}


@dataclass(frozen=True)
class SafetyState:
    stage: str
    detail: str

    @property
    def allows_live_preview(self) -> bool:
        return stage_at_least(self.stage, "PREVIEW_ONLY")

    @property
    def allows_live_submit(self) -> bool:
        return stage_at_least(self.stage, "LIVE_ENABLED")


class SafetyStateStore:
    def __init__(self, path: str | Path = "state/app_safety_state.toml"):
        self.path = Path(path)

    def load(self) -> SafetyState:
        if not self.path.exists():
            return SafetyState(
                stage="SETUP",
                detail="Onboarding mode. Coinductor cannot place orders and live previews stay disabled.",
            )
        with self.path.open("rb") as handle:
            payload = tomllib.load(handle)
        values = payload.get("safety_state", {})
        if not isinstance(values, dict):
            return SafetyState(stage="SETUP", detail="Invalid safety state file; using setup mode.")
        stage = normalize_stage(values.get("stage"))
        detail = str(values.get("detail", "")).strip() or _default_detail(stage)
        return SafetyState(stage=stage, detail=detail)

    def save(self, state: SafetyState) -> None:
        stage = normalize_stage(state.stage)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            "\n".join(
                [
                    "# Coinductor safety stage.",
                    "# Live execution is unavailable unless stage is LIVE_ENABLED.",
                    "",
                    "[safety_state]",
                    f'stage = "{stage}"',
                    f'detail = "{state.detail}"',
                    "",
                ]
            ),
            encoding="utf-8",
        )


def normalize_stage(value: object) -> str:
    stage = str(value or "").upper()
    return stage if stage in STAGE_ORDER else "SETUP"


def stage_at_least(stage: str, minimum: str) -> bool:
    return STAGE_ORDER[normalize_stage(stage)] >= STAGE_ORDER[normalize_stage(minimum)]


def _default_detail(stage: str) -> str:
    if stage == "READ_ONLY_CONNECTED":
        return "Read-only portfolio analysis is available; no exchange-changing actions are allowed."
    if stage == "TESTNET_READY":
        return "Testnet validation is available; mainnet remains preview/submit locked."
    if stage == "PREVIEW_ONLY":
        return "Mainnet previews are allowed; submissions remain locked."
    if stage == "ARMED":
        return "Guarded workflows can be prepared, but final live submission remains separately locked."
    if stage == "LIVE_ENABLED":
        return "Live guarded submit workflows are enabled with confirmation and risk gates."
    return "Onboarding mode. Coinductor cannot place orders and live previews stay disabled."
