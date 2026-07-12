from coinductor import connection_check
from coinductor.connection_check import ConnectionCheckService, LiveTradingCheckService

from test_coinductor_setup_service import VALID_CONFIG


class FakeBinanceClient:
    def __init__(self, config: dict, credential_profile: str = "mainnet_read"):
        self.config = config
        self.credential_profile = credential_profile

    def assert_read_only_permissions(self) -> None:
        return None

    def assert_live_spot_permissions(self) -> None:
        assert self.credential_profile == "live_trade"


def test_connection_check_passes_without_exposing_secrets(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(connection_check, "BinanceClient", FakeBinanceClient)
    secret = "do-not-render-this-secret"
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / ".env").write_text(
        f"BINANCE_API_KEY={secret}\nBINANCE_API_SECRET=read-secret\n",
        encoding="utf-8",
    )

    result = ConnectionCheckService("config.toml", ".env").check_binance_read_only()

    assert result.status == "PASS"
    assert secret not in result.detail


def test_connection_check_blocks_missing_env(tmp_path) -> None:
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")

    result = ConnectionCheckService(tmp_path / "config.toml", tmp_path / ".env").check_binance_read_only()

    assert result.status == "BLOCK"
    assert ".env" in result.detail


def test_live_trading_check_passes_without_exposing_secrets(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(connection_check, "BinanceClient", FakeBinanceClient)
    secret = "never-render-live-secret"
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / ".env").write_text(
        f"BINANCE_LIVE_TRADE_API_KEY={secret}\nBINANCE_LIVE_TRADE_API_SECRET=live-secret\n",
        encoding="utf-8",
    )

    result = LiveTradingCheckService("config.toml", ".env").check_binance_live_trading()

    assert result.status == "PASS"
    assert "trusted-IP" in result.detail
    assert secret not in result.detail
