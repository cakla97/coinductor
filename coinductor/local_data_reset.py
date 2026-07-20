from __future__ import annotations

from pathlib import Path
import shutil

from .models import LocalDataResetSnapshot


class LocalDataResetService:
    def __init__(self, root: str | Path = "."):
        self.root = Path(root)

    def preview(self) -> LocalDataResetSnapshot:
        items = tuple(self._preview_item(group) for group in self._groups())
        summary = "Choose specific local data groups to remove, or use Delete everything to select the full local reset preview."
        return LocalDataResetSnapshot(summary=summary, items=items)

    def execute(self, codes: list[str]) -> LocalDataResetSnapshot:
        root = self.root.resolve()
        selected = {str(code).strip().upper() for code in codes}
        removed: list[str] = []
        blocked: list[str] = []
        for group in self._groups():
            if group["code"] not in selected:
                continue
            for raw_path in group["paths"]:
                target = (self.root / raw_path).resolve()
                if target == root:
                    blocked.append(f"{raw_path} (refused: resolves to the project root itself)")
                    continue
                try:
                    target.relative_to(root)
                except ValueError:
                    blocked.append(f"{raw_path} (refused: resolves outside the project root)")
                    continue
                if not target.exists():
                    continue
                try:
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                    removed.append(raw_path)
                except OSError as exc:
                    blocked.append(f"{raw_path} ({exc})")

        snapshot = self.preview()
        if removed or blocked:
            parts = []
            if removed:
                parts.append(f"Removed: {', '.join(removed)}.")
            if blocked:
                parts.append(f"Could not remove: {', '.join(blocked)}.")
            summary = " ".join(parts)
        else:
            summary = "No selected local data group had anything to remove."
        return LocalDataResetSnapshot(summary=summary, items=snapshot.items)

    def _groups(self) -> tuple[dict[str, object], ...]:
        return (
            {
                "code": "PROFILE",
                "name": "Onboarding profile",
                "detail": "Region, language, risk preference, automation preference, budget, planner settings, and first-use tour status.",
                "default": True,
                "paths": ("state/user_profile.toml", "state/app_ui_state.toml"),
            },
            {
                "code": "POLICY_AND_STRATEGY",
                "name": "Policy and strategy settings",
                "detail": "Manual asset role overrides, safety stage, active strategy registry, Grid/Rebalancing local registries.",
                "default": False,
                "paths": (
                    "state/asset_policy_overrides.toml",
                    "state/app_safety_state.toml",
                    "state/active_strategies.toml",
                    "state/grid_registry.toml",
                    "state/rebalancing_registry.toml",
                ),
            },
            {
                "code": "DATABASE",
                "name": "Local database and run history",
                "detail": "SQLite run history, portfolio snapshots, shadow signals, and local state derived from previous runs.",
                "default": False,
                "paths": ("work/trading_agent.sqlite3",),
            },
            {
                "code": "REPORTS",
                "name": "Reports",
                "detail": "Generated run reports and human-readable summaries.",
                "default": False,
                "paths": ("reports",),
            },
            {
                "code": "RESEARCH",
                "name": "Research notes and requests",
                "detail": "Manual research notes, Binance Skills prompts, generated research requests, and optional AI context files.",
                "default": False,
                "paths": ("research/notes", "research/requests"),
            },
            {
                "code": "AI_CHAT_HISTORY",
                "name": "AI chat history",
                "detail": "Locally stored AI Assistant conversations and screenshots pasted from the clipboard. The newest 20 chats and up to 40 pasted images are retained until this data group is removed.",
                "default": False,
                "paths": ("state/assistant_history.json", "state/assistant_attachments"),
            },
            {
                "code": "ENV",
                "name": "API keys and local environment",
                "detail": ".env file with Binance keys and optional AI provider settings. Only delete this when you want a completely clean app setup.",
                "default": False,
                "paths": (".env",),
            },
        )

    def _preview_item(self, group: dict[str, object]) -> dict[str, str]:
        paths = group["paths"]
        existing = [path for path in paths if (self.root / path).exists()]
        return {
            "code": str(group["code"]),
            "name": str(group["name"]),
            "detail": str(group["detail"]),
            "default": "true" if group["default"] else "false",
            "paths": ", ".join(paths),
            "status": "Present" if existing else "Not found yet",
        }
