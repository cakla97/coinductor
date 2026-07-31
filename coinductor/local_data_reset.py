from __future__ import annotations

from pathlib import Path
import shutil

from .models import LocalDataResetSnapshot
from .service_strings import service_text

# The AI provider's own keys. Removing these is how a model gets disconnected:
# the wizard writes them, and nothing else in the app reads an endpoint from
# anywhere but here.
AI_PROVIDER_KEYS: tuple[str, ...] = (
    "LLM_API_KEY",
    "LLM_BASE_URL",
    "LLM_MODEL",
    "LLM_VISION_MODEL",
)


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
            if group.get("clears_keychain"):
                removed.extend(self._clear_keychain(group.get("keychain_keys")))
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
                # app.reports_dir is "outputs/reports"; this group used to list
                # only "reports", so selecting it deleted nothing at all. The
                # bare name is kept for older layouts that used it. Diagnostics
                # bundles are generated, human-readable output too, and survived
                # a "delete everything" that claimed to be a full local reset.
                "paths": ("outputs/reports", "outputs/diagnostics", "reports"),
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
                # Off by default and listed separately: this holds hand-tuned
                # risk limits and the trading universe, so it is the one thing
                # here a user may want to keep while clearing everything else.
                "code": "CONFIG",
                "name": self._t("reset_group_config"),
                "detail": self._t("reset_group_config_detail"),
                "default": False,
                "paths": ("config.toml",),
            },
            {
                # Disconnecting a model had no path through the app at all:
                # clearing the fields in the wizard and saving just reloaded
                # what was already stored, because saving nothing writes
                # nothing. Separate from CREDENTIALS so that stepping away from
                # AI does not also throw away the Binance keys.
                "code": "AI_PROVIDER",
                "name": self._t("reset_group_ai_provider"),
                "detail": self._t("reset_group_ai_provider_detail"),
                "default": False,
                "paths": (),
                "clears_keychain": True,
                "keychain_keys": AI_PROVIDER_KEYS,
            },
            {
                "code": "CREDENTIALS",
                "name": self._t("reset_group_credentials"),
                "detail": self._t("reset_group_credentials_detail"),
                "default": False,
                "paths": (".env",),
                # .env is usually absent because keys live in the OS keychain.
                # Deleting only the file would leave the single most sensitive
                # thing behind for someone removing the app for good.
                "clears_keychain": True,
            },
        )

    def _clear_keychain(self, only: object = None) -> list[str]:
        """Remove the app's keys from the OS credential store.

        ``only`` narrows it to one family - the AI provider's keys, say -
        so that disconnecting a model does not also remove Binance access.

        Returns what was actually held, so the summary can name it. Failure to
        reach a keychain is not an error: there may simply not be one.
        """
        from .secret_store import SecretStore  # noqa: PLC0415

        store = SecretStore(env_path=self.root / ".env")
        try:
            held = store.stored_keys()
            if only:
                wanted = {str(key) for key in only}
                held = tuple(key for key in held if key in wanted)
            if not held:
                return []
            store.clear(held)
            return [self._t("reset_keychain_entry").format(count=len(held))]
        except Exception:
            return []

    def _preview_item(self, group: dict[str, object]) -> dict[str, str]:
        paths = group["paths"]
        existing = [path for path in paths if (self.root / path).exists()]
        if group.get("clears_keychain"):
            try:
                from .secret_store import SecretStore  # noqa: PLC0415

                if SecretStore(env_path=self.root / ".env").stored_keys():
                    existing.append("keychain")
            except Exception:
                pass
        return {
            "code": str(group["code"]),
            "name": str(group["name"]),
            "detail": str(group["detail"]),
            "default": "true" if group["default"] else "false",
            "paths": ", ".join(paths),
            "status": "Present" if existing else "Not found yet",
        }
