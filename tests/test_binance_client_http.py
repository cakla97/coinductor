import pytest

from trading_agent import binance_client as binance_client_module
from trading_agent.binance_client import BinanceApiError, BinanceClient, BinanceRateLimitError


class _FakeResponse:
    def __init__(self, status: int, body: str, headers: dict[str, str] | None = None):
        self.status = status
        self._body = body
        self._headers = headers or {}

    def read(self) -> bytes:
        return self._body.encode("utf-8")

    def getheader(self, name: str, default: str | None = None) -> str | None:
        return self._headers.get(name, default)


class _FakeConnection:
    """Replays a scripted list of responses; an Exception entry is raised instead."""

    def __init__(self, script: list[object]):
        self.script = script
        self.requests: list[tuple[str, str]] = []
        self.closes = 0

    def request(self, method: str, path: str, headers: dict[str, str] | None = None) -> None:
        self.requests.append((method, path))
        item = self.script[len(self.requests) - 1]
        if isinstance(item, Exception):
            raise item

    def getresponse(self) -> _FakeResponse:
        return self.script[len(self.requests) - 1]

    def close(self) -> None:
        self.closes += 1


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(binance_client_module.time, "sleep", lambda _seconds: None)


def _client(script: list[object], **binance_config) -> tuple[BinanceClient, _FakeConnection]:
    config = {"binance": {"api_base_url": "https://api.binance.com", **binance_config}}
    client = BinanceClient(config)
    connection = _FakeConnection(script)
    client._ensure_connection = lambda: connection  # type: ignore[method-assign]
    return client, connection


def test_get_is_retried_after_a_rate_limit_and_then_succeeds() -> None:
    client, connection = _client(
        [
            _FakeResponse(429, "too many requests", {"Retry-After": "1"}),
            _FakeResponse(200, '{"price": "65000"}'),
        ]
    )

    assert client._public_get("/api/v3/ticker/price") == {"price": "65000"}
    assert len(connection.requests) == 2


def test_rate_limit_that_never_clears_raises_a_rate_limit_error() -> None:
    client, connection = _client([_FakeResponse(429, "slow down")] * 4, max_retries=3)

    with pytest.raises(BinanceRateLimitError, match="429"):
        client._public_get("/api/v3/ticker/price")
    assert len(connection.requests) == 4


def test_ip_ban_fails_immediately_without_retrying() -> None:
    client, connection = _client([_FakeResponse(418, "banned")] * 4)

    with pytest.raises(BinanceRateLimitError, match="temporarily banned"):
        client._public_get("/api/v3/ticker/price")
    assert len(connection.requests) == 1


def test_client_error_is_not_retried() -> None:
    client, connection = _client([_FakeResponse(400, "bad symbol")] * 4)

    with pytest.raises(BinanceApiError, match="HTTP 400"):
        client._public_get("/api/v3/ticker/price")
    assert len(connection.requests) == 1


def test_server_error_is_retried_for_reads() -> None:
    client, connection = _client(
        [_FakeResponse(503, "unavailable"), _FakeResponse(200, "[]")]
    )

    assert client._public_get("/api/v3/ticker/price") == []
    assert len(connection.requests) == 2


def test_dropped_connection_is_retried_for_reads() -> None:
    client, connection = _client([ConnectionResetError("reset"), _FakeResponse(200, "[]")])

    assert client._public_get("/api/v3/ticker/price") == []
    assert len(connection.requests) == 2


def test_order_submission_is_never_replayed_after_a_transport_failure(monkeypatch) -> None:
    """A POST that fails in transit may already have reached the matching engine."""
    monkeypatch.setenv("BINANCE_API_KEY", "key")
    monkeypatch.setenv("BINANCE_API_SECRET", "secret")
    client, connection = _client([ConnectionResetError("reset")] * 4)
    client._server_time_offset_ms = 0

    with pytest.raises(BinanceApiError, match="connection failed"):
        client.signed_post("/api/v3/order", {"symbol": "BTCUSDT"})
    assert len(connection.requests) == 1


def test_symbol_rules_are_fetched_once_per_symbol() -> None:
    client, _ = _client([])
    calls: list[dict] = []

    def fake_public_get(path, params=None):
        calls.append(params or {})
        return {
            "symbols": [
                {
                    "symbol": "BTCUSDT",
                    "status": "TRADING",
                    "baseAsset": "BTC",
                    "quoteAsset": "USDT",
                    "quoteOrderQtyMarketAllowed": True,
                    "filters": [],
                }
            ]
        }

    client._public_get = fake_public_get  # type: ignore[method-assign]

    first = client.get_symbol_rules("BTCUSDT")
    second = client.get_symbol_rules("btcusdt")

    assert first is second
    assert len(calls) == 1
