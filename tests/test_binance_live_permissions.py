import pytest

from trading_agent.binance_client import BinanceApiError, BinanceClient


def _client(monkeypatch, permissions: dict) -> BinanceClient:
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_KEY", "test-key")
    monkeypatch.setenv("BINANCE_LIVE_TRADE_API_SECRET", "test-secret")
    client = BinanceClient(
        {"binance": {"api_base_url": "https://api.binance.com"}},
        credential_profile="live_trade",
    )
    monkeypatch.setattr(client, "_signed_get", lambda _path: permissions)
    return client


def test_live_permission_check_accepts_minimal_trusted_ip_spot_key(monkeypatch) -> None:
    client = _client(
        monkeypatch,
        {
            "enableReading": True,
            "enableSpotAndMarginTrading": True,
            "ipRestrict": True,
            "enableWithdrawals": False,
            "enableInternalTransfer": False,
            "permitsUniversalTransfer": False,
            "enableMargin": False,
            "enableFutures": False,
            "enableVanillaOptions": False,
            "enablePortfolioMarginTrading": False,
        },
    )

    client.assert_live_spot_permissions()


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"ipRestrict": False}, "trusted IP"),
        ({"enableSpotAndMarginTrading": False}, "Spot trading"),
        ({"enableWithdrawals": True}, "withdrawals"),
        ({"enableFutures": True}, "futures"),
    ],
)
def test_live_permission_check_rejects_unsafe_key(monkeypatch, change, message) -> None:
    permissions = {
        "enableReading": True,
        "enableSpotAndMarginTrading": True,
        "ipRestrict": True,
        "enableWithdrawals": False,
        "enableInternalTransfer": False,
        "permitsUniversalTransfer": False,
        "enableMargin": False,
        "enableFutures": False,
        "enableVanillaOptions": False,
        "enablePortfolioMarginTrading": False,
    }
    permissions.update(change)
    client = _client(monkeypatch, permissions)

    with pytest.raises(BinanceApiError, match=message):
        client.assert_live_spot_permissions()
