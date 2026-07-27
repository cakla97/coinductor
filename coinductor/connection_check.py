from __future__ import annotations

from pathlib import Path

from trading_agent.binance_client import BinanceApiError, BinanceClient
from trading_agent.config import default_config_path, load_config

from .models import ConnectionCheckResult
from .secret_store import load_secrets
from .service_strings import service_text


def _configured(*names: str) -> bool:
    """Whether these credentials resolved, wherever they are stored.

    Call after load_secrets: keys normally live in the OS keychain, so the
    presence of a .env file says nothing about whether they are configured.
    """
    import os  # noqa: PLC0415

    return all(os.environ.get(name, "").strip() for name in names)


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

        try:
            load_secrets(self.env_path)
            if not _configured("BINANCE_API_KEY", "BINANCE_API_SECRET"):
                return ConnectionCheckResult("BLOCK", self._t("conn_missing_env_readonly"))
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

        try:
            load_secrets(self.env_path)
            if not _configured("BINANCE_LIVE_TRADE_API_KEY", "BINANCE_LIVE_TRADE_API_SECRET"):
                return ConnectionCheckResult("BLOCK", self._t("conn_missing_env_live"))
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

        try:
            load_secrets(self.env_path)
            if not _configured("BINANCE_TESTNET_API_KEY", "BINANCE_TESTNET_API_SECRET"):
                return ConnectionCheckResult("BLOCK", self._t("conn_missing_env_testnet"))
            config = load_config(self.config_path)
            BinanceClient(config.raw, use_testnet=True).testnet_account_ping()
        except BinanceApiError as exc:
            return ConnectionCheckResult("BLOCK", str(exc))
        except Exception as exc:
            return ConnectionCheckResult("BLOCK", self._t("conn_testnet_failed").format(error=exc))

        return ConnectionCheckResult("PASS", self._t("conn_testnet_ok"))
