from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import tomllib

from .asset_policy import apply_asset_policy_overrides


def default_config_path() -> str:
    """Config file to load when a caller does not specify one.

    Prefers a local, gitignored ``config.toml`` (personal settings) and
    falls back to the tracked, neutral ``config.example.toml`` template.
    ``COINDUCTOR_CONFIG`` overrides both. Resolved relative to the current
    working directory, so it honors the frozen build's data-dir chdir.
    """
    override = os.environ.get("COINDUCTOR_CONFIG")
    if override:
        return override
    if Path("config.toml").exists():
        return "config.toml"
    return "config.example.toml"


@dataclass(frozen=True)
class AppConfig:
    raw: dict
    path: Path

    @property
    def mode(self) -> str:
        return str(self.raw["app"]["mode"]).upper()

    @property
    def mock_data(self) -> bool:
        return bool(self.raw["app"].get("mock_data", True))

    @property
    def database_path(self) -> Path:
        return Path(self.raw["app"]["database_path"])

    @property
    def reports_dir(self) -> Path:
        return Path(self.raw["app"]["reports_dir"])

    @property
    def allowed_symbols(self) -> list[str]:
        return list(self.raw["strategy"]["allowed_symbols"])


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)
    raw = apply_asset_policy_overrides(raw)
    return AppConfig(raw=raw, path=config_path)
