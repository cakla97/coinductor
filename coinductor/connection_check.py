from __future__ import annotations

from pathlib import Path

from trading_agent.binance_client import BinanceApiError, BinanceClient
from trading_agent.config import load_config
from trading_agent.env import load_env_file

from .models import ConnectionCheckResult


class ConnectionCheckService:
    def __init__(
        self,
        config_path: str | Path = "config.example.toml",
        env_path: str | Path = ".env",
    ):
        self.config_path = Path(config_path)
        self.env_path = Path(env_path)

    def check_binance_read_only(self) -> ConnectionCheckResult:
        if not self.config_path.exists():
            return ConnectionCheckResult("BLOCK", f"Missing config: {self.config_path}")
        if not self.env_path.exists():
            return ConnectionCheckResult("BLOCK", "Missing .env with Binance read-only keys")

        try:
            load_env_file(self.env_path)
            config = load_config(self.config_path)
            BinanceClient(config.raw).assert_read_only_permissions()
        except BinanceApiError as exc:
            return ConnectionCheckResult("BLOCK", str(exc))
        except Exception as exc:
            return ConnectionCheckResult("BLOCK", f"Connection check failed: {exc}")

        return ConnectionCheckResult("PASS", "Read-only API key is reachable and trading permissions are disabled")
