from __future__ import annotations

from pathlib import Path
import shutil

from .models import LocalDataResetSnapshot
from .service_strings import service_text


class LocalDataResetService:
    def __init__(self, root: str | Path = ".", language: str = "en"):
        self.root = Path(root)
        self.language = language

    def _t(self, key: str) -> str:
        return service_text(key, self.language)

    def preview(self) -> LocalDataResetSnapshot:
        items = tuple(self._preview_item(group) for group in self._groups())
        summary = self._t("reset_summary_choose")
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
                parts.append(self._t("reset_summary_removed").format(paths=", ".join(removed)))
            if blocked:
                parts.append(self._t("reset_summary_blocked").format(paths=", ".join(blocked)))
            summary = " ".join(parts)
        else:
            summary = self._t("reset_summary_nothing")
        return LocalDataResetSnapshot(summary=summary, items=snapshot.items)

    def _groups(self) -> tuple[dict[str, object], ...]:
        return (
            {
                "code": "PROFILE",
                "name": self._t("reset_group_profile"),
                "detail": self._t("reset_group_profile_detail"),
                "default": True,
                "paths": ("state/user_profile.toml", "state/app_ui_state.toml"),
            },
            {
                "code": "POLICY_AND_STRATEGY",
                "name": self._t("reset_group_policy"),
                "detail": self._t("reset_group_policy_detail"),
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
                "name": self._t("reset_group_database"),
                "detail": self._t("reset_group_database_detail"),
                "default": False,
                "paths": ("work/trading_agent.sqlite3",),
            },
            {
                "code": "REPORTS",
                "name": self._t("reset_group_reports"),
                "detail": self._t("reset_group_reports_detail"),
                "default": False,
                "paths": ("reports",),
            },
            {
                "code": "RESEARCH",
                "name": self._t("reset_group_research"),
                "detail": self._t("reset_group_research_detail"),
                "default": False,
                "paths": ("research/notes", "research/requests"),
            },
            {
                "code": "AI_CHAT_HISTORY",
                "name": self._t("reset_group_ai_chat"),
                "detail": self._t("reset_group_ai_chat_detail"),
                "default": False,
                "paths": ("state/assistant_history.json", "state/assistant_attachments"),
            },
            {
                "code": "ENV",
                "name": self._t("reset_group_env"),
                "detail": self._t("reset_group_env_detail"),
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
