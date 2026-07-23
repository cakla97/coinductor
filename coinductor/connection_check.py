from __future__ import annotations

from pathlib import Path

from trading_agent.binance_client import BinanceApiError, BinanceClient
from trading_agent.config import default_config_path, load_config
from trading_agent.env import load_env_file

from .models import ConnectionCheckResult


class ConnectionCheckService:
    def __init__(
        self,
        config_path: str | Path | None = None,
        env_path: str | Path = ".env",
    ):
        self.config_path = Path(config_path or default_config_path())
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


class LiveTradingCheckService:
    def __init__(
        self,
        config_path: str | Path | None = None,
        env_path: str | Path = ".env",
    ):
        self.config_path = Path(config_path or default_config_path())
        self.env_path = Path(env_path)

    def check_binance_live_trading(self) -> ConnectionCheckResult:
        if not self.config_path.exists():
            return ConnectionCheckResult("BLOCK", f"Missing config: {self.config_path}")
        if not self.env_path.exists():
            return ConnectionCheckResult("BLOCK", "Missing .env with Binance live trading keys")

        try:
            load_env_file(self.env_path)
            config = load_config(self.config_path)
            BinanceClient(config.raw, credential_profile="live_trade").assert_live_spot_permissions()
        except BinanceApiError as exc:
            return ConnectionCheckResult("BLOCK", str(exc))
        except Exception as exc:
            return ConnectionCheckResult("BLOCK", f"Live trading check failed: {exc}")

        return ConnectionCheckResult(
            "PASS",
            "Live key is reachable: Reading + Spot trading enabled, trusted-IP restriction active, forbidden permissions disabled",
        )


class TestnetCheckService:
    def __init__(
        self,
        config_path: str | Path | None = None,
        env_path: str | Path = ".env",
    ):
        self.config_path = Path(config_path or default_config_path())
        self.env_path = Path(env_path)

    def check_binance_testnet(self) -> ConnectionCheckResult:
        if not self.config_path.exists():
            return ConnectionCheckResult("BLOCK", f"Missing config: {self.config_path}")
        if not self.env_path.exists():
            return ConnectionCheckResult("BLOCK", "Missing .env with Binance Spot Testnet keys")

        try:
            load_env_file(self.env_path)
            config = load_config(self.config_path)
            BinanceClient(config.raw, use_testnet=True).testnet_account_ping()
        except BinanceApiError as exc:
            return ConnectionCheckResult("BLOCK", str(exc))
        except Exception as exc:
            return ConnectionCheckResult("BLOCK", f"Testnet check failed: {exc}")

        return ConnectionCheckResult("PASS", "Spot Testnet key is reachable. Virtual funds are ready for safe testing.")
