from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tomllib

from trading_agent.asset_policy import ROLE_OPTIONS


class AssetPolicyStore:
    def __init__(self, path: str | Path = "state/asset_policy_overrides.toml"):
        self.path = Path(path)

    @property
    def role_options(self) -> list[str]:
        return list(ROLE_OPTIONS)

    def load(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        with self.path.open("rb") as handle:
            payload = tomllib.load(handle)
        overrides = payload.get("overrides", {})
        if not isinstance(overrides, dict):
            return {}
        roles: dict[str, str] = {}
        for asset, details in overrides.items():
            if not isinstance(details, dict):
                continue
            role = str(details.get("role", "")).upper()
            if role and role != "SYSTEM_DEFAULT":
                roles[str(asset).upper()] = role
        return roles

    def save_role(self, asset: str, role: str) -> None:
        asset = asset.strip().upper()
        role = role.strip().upper()
        if not asset or role not in ROLE_OPTIONS:
            return

        overrides = self.load()
        if role == "SYSTEM_DEFAULT":
            overrides.pop(asset, None)
        else:
            overrides[asset] = role
        self._write(overrides)

    def _write(self, overrides: dict[str, str]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Manual Coinductor asset policy overrides.",
            "# SYSTEM_DEFAULT removes an override and lets config/report classification decide.",
            "",
        ]
        for asset in sorted(overrides):
            lines.extend(
                [
                    f"[overrides.{asset}]",
                    f'role = "{overrides[asset]}"',
                    f'updated_at = "{datetime.now(timezone.utc).isoformat()}"',
                    "",
                ]
            )
        self.path.write_text("\n".join(lines), encoding="utf-8")
