from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


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
    return AppConfig(raw=raw, path=config_path)

