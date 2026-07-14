from __future__ import annotations

from pathlib import Path

from .models import LocalDataResetSnapshot


class LocalDataResetService:
    def __init__(self, root: str | Path = "."):
        self.root = Path(root)

    def preview(self) -> LocalDataResetSnapshot:
        items = (
            self._item(
                code="PROFILE",
                name="Onboarding profile",
                detail="Region, language, risk preference, automation preference, budget, planner settings, and first-use tour status.",
                default=True,
                paths=("state/user_profile.toml", "state/app_ui_state.toml"),
            ),
            self._item(
                code="POLICY_AND_STRATEGY",
                name="Policy and strategy settings",
                detail="Manual asset role overrides, safety stage, active strategy registry, Grid/Rebalancing local registries.",
                default=False,
                paths=(
                    "state/asset_policy_overrides.toml",
                    "state/app_safety_state.toml",
                    "state/active_strategies.toml",
                    "state/grid_registry.toml",
                    "state/rebalancing_registry.toml",
                ),
            ),
            self._item(
                code="DATABASE",
                name="Local database and run history",
                detail="SQLite run history, portfolio snapshots, shadow signals, and local state derived from previous runs.",
                default=False,
                paths=("work/trading_agent.sqlite3",),
            ),
            self._item(
                code="REPORTS",
                name="Reports",
                detail="Generated run reports and human-readable summaries.",
                default=False,
                paths=("reports",),
            ),
            self._item(
                code="RESEARCH",
                name="Research notes and requests",
                detail="Manual research notes, Binance Skills prompts, generated research requests, and optional AI context files.",
                default=False,
                paths=("research/notes", "research/requests"),
            ),
            self._item(
                code="AI_CHAT_HISTORY",
                name="AI chat history",
                detail="Locally stored AI Assistant conversations. The newest 20 chats are retained until this data group is removed.",
                default=False,
                paths=("state/assistant_history.json",),
            ),
            self._item(
                code="ENV",
                name="API keys and local environment",
                detail=".env file with Binance keys and optional AI provider settings. Only delete this when you want a completely clean app setup.",
                default=False,
                paths=(".env",),
            ),
        )
        summary = "Choose specific local data groups to remove, or use Delete everything to select the full local reset preview."
        return LocalDataResetSnapshot(summary=summary, items=items)

    def _item(
        self,
        code: str,
        name: str,
        detail: str,
        default: bool,
        paths: tuple[str, ...],
    ) -> dict[str, str]:
        existing = [path for path in paths if (self.root / path).exists()]
        return {
            "code": code,
            "name": name,
            "detail": detail,
            "default": "true" if default else "false",
            "paths": ", ".join(paths),
            "status": "Present" if existing else "Not found yet",
        }
