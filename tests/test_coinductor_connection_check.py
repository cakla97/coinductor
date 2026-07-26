import os

from coinductor import connection_check
from coinductor.connection_check import ConnectionCheckService, LiveTradingCheckService, TestnetCheckService

from test_coinductor_setup_service import VALID_CONFIG


class FakeBinanceClient:
    def __init__(self, config: dict, credential_profile: str = "mainnet_read", use_testnet: bool = False):
        self.config = config
        self.credential_profile = credential_profile
        self.use_testnet = use_testnet

    def assert_read_only_permissions(self) -> None:
        return None

    def assert_live_spot_permissions(self) -> None:
        assert self.credential_profile == "live_trade"

    def testnet_account_ping(self) -> dict:
        assert self.use_testnet is True
        return {"balances": []}


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
    # Keys may live in the OS keychain rather than a file, so the message names
    # the missing capability, not a filename the user may never have.
    assert "not configured" in result.detail


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


def test_testnet_check_passes_without_exposing_secrets(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(connection_check, "BinanceClient", FakeBinanceClient)
    secret = "never-render-testnet-secret"
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / ".env").write_text(
        f"BINANCE_TESTNET_API_KEY={secret}\nBINANCE_TESTNET_API_SECRET=testnet-secret\n",
        encoding="utf-8",
    )

    try:
        result = TestnetCheckService("config.toml", ".env").check_binance_testnet()

        assert result.status == "PASS"
        assert secret not in result.detail
    finally:
        # load_env_file mutates the real process os.environ directly. Pop it with
        # plain os.environ (not monkeypatch.delenv) so pytest's monkeypatch teardown
        # doesn't restore the leaked value once this test ends.
        os.environ.pop("BINANCE_TESTNET_API_KEY", None)
        os.environ.pop("BINANCE_TESTNET_API_SECRET", None)


def test_testnet_check_blocks_missing_env(tmp_path) -> None:
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")

    result = TestnetCheckService(tmp_path / "config.toml", tmp_path / ".env").check_binance_testnet()

    assert result.status == "BLOCK"
    # Keys may live in the OS keychain rather than a file, so the message names
    # the missing capability, not a filename the user may never have.
    assert "not configured" in result.detail
