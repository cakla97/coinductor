from __future__ import annotations

from pathlib import Path

from trading_agent.binance_client import BinanceApiError, BinanceClient
from trading_agent.config import default_config_path, load_config
from trading_agent.env import load_env_file

from .models import ConnectionCheckResult
from .service_strings import service_text


class ConnectionCheckService:
    def __init__(
        self,
        config_path: str | Path | None = None,
        env_path: str | Path = ".env",
        language: str = "en",
    ):
        self.config_path = Path(config_path or default_config_path())
        self.env_path = Path(env_path)
        self.language = language

    def _t(self, key: str) -> str:
        return service_text(key, self.language)

    def check_binance_read_only(self) -> ConnectionCheckResult:
        if not self.config_path.exists():
            return ConnectionCheckResult("BLOCK", self._t("conn_missing_config").format(path=self.config_path))
        if not self.env_path.exists():
            return ConnectionCheckResult("BLOCK", self._t("conn_missing_env_readonly"))

        try:
            load_env_file(self.env_path)
            config = load_config(self.config_path)
            BinanceClient(config.raw).assert_read_only_permissions()
        except BinanceApiError as exc:
            return ConnectionCheckResult("BLOCK", str(exc))
        except Exception as exc:
            return ConnectionCheckResult("BLOCK", self._t("conn_readonly_failed").format(error=exc))

        return ConnectionCheckResult("PASS", self._t("conn_readonly_ok"))


class LiveTradingCheckService:
    def __init__(
        self,
        config_path: str | Path | None = None,
        env_path: str | Path = ".env",
        language: str = "en",
    ):
        self.config_path = Path(config_path or default_config_path())
        self.env_path = Path(env_path)
        self.language = language

    def _t(self, key: str) -> str:
        return service_text(key, self.language)

    def check_binance_live_trading(self) -> ConnectionCheckResult:
        if not self.config_path.exists():
            return ConnectionCheckResult("BLOCK", self._t("conn_missing_config").format(path=self.config_path))
        if not self.env_path.exists():
            return ConnectionCheckResult("BLOCK", self._t("conn_missing_env_live"))

        try:
            load_env_file(self.env_path)
            config = load_config(self.config_path)
            BinanceClient(config.raw, credential_profile="live_trade").assert_live_spot_permissions()
        except BinanceApiError as exc:
            return ConnectionCheckResult("BLOCK", str(exc))
        except Exception as exc:
            return ConnectionCheckResult("BLOCK", self._t("conn_live_failed").format(error=exc))

        return ConnectionCheckResult(
            "PASS",
            self._t("conn_live_ok"),
        )


class TestnetCheckService:
    def __init__(
        self,
        config_path: str | Path | None = None,
        env_path: str | Path = ".env",
        language: str = "en",
    ):
        self.config_path = Path(config_path or default_config_path())
        self.env_path = Path(env_path)
        self.language = language

    def _t(self, key: str) -> str:
        return service_text(key, self.language)

    def check_binance_testnet(self) -> ConnectionCheckResult:
        if not self.config_path.exists():
            return ConnectionCheckResult("BLOCK", self._t("conn_missing_config").format(path=self.config_path))
        if not self.env_path.exists():
            return ConnectionCheckResult("BLOCK", self._t("conn_missing_env_testnet"))

        try:
            load_env_file(self.env_path)
            config = load_config(self.config_path)
            BinanceClient(config.raw, use_testnet=True).testnet_account_ping()
        except BinanceApiError as exc:
            return ConnectionCheckResult("BLOCK", str(exc))
        except Exception as exc:
            return ConnectionCheckResult("BLOCK", self._t("conn_testnet_failed").format(error=exc))

        return ConnectionCheckResult("PASS", self._t("conn_testnet_ok"))
