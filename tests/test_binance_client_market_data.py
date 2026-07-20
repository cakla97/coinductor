from trading_agent.binance_client import BinanceApiError, BinanceClient


def _client() -> BinanceClient:
    return BinanceClient({"binance": {"api_base_url": "https://api.binance.com"}})


def test_get_symbol_market_snapshot_returns_the_24h_ticker(monkeypatch) -> None:
    client = _client()
    seen_params = {}

    def fake_public_get(path, params=None):
        seen_params["path"] = path
        seen_params["params"] = params
        return {
            "symbol": "BTCUSDC",
            "lastPrice": "65000.00",
            "priceChangePercent": "2.50",
            "highPrice": "66000.00",
            "lowPrice": "63000.00",
        }

    monkeypatch.setattr(client, "_public_get", fake_public_get)

    snapshot = client.get_symbol_market_snapshot("btcusdc")

    assert snapshot["lastPrice"] == "65000.00"
    assert snapshot["priceChangePercent"] == "2.50"
    assert seen_params["path"] == "/api/v3/ticker/24hr"
    assert seen_params["params"] == {"symbol": "BTCUSDC"}


def test_get_symbol_market_snapshot_rejects_a_non_dict_response(monkeypatch) -> None:
    client = _client()
    monkeypatch.setattr(client, "_public_get", lambda path, params=None: [])

    try:
        client.get_symbol_market_snapshot("BTCUSDC")
        assert False, "expected BinanceApiError"
    except BinanceApiError as exc:
        assert "BTCUSDC" in str(exc)
