from decimal import Decimal

from trading_agent.binance_client import BinanceApiError
from trading_agent.market_research import MarketResearchCollector
from trading_agent.models import MarketSnapshot
from trading_agent.storage import Storage


class FakeClient:
    def get_24h_tickers(self) -> list[dict]:
        return [
            _ticker("BTCUSDC", "2", "10000000", "110", "90", "100", 50000),
            _ticker("ETHUSDC", "-1", "8000000", "105", "95", "100", 40000),
            _ticker("SOLUSDC", "4", "5000000", "120", "90", "100", 30000),
            _ticker("USDTUSDC", "0.01", "20000000", "1.01", "0.99", "1", 10000),
            _ticker("LOWUSDC", "20", "10", "2", "1", "1.5", 5),
        ]

    def get_klines(self, symbol: str, interval: str, limit: int) -> list[list]:
        assert interval == "4h"
        assert limit == 180
        multiplier = Decimal("1.001") if symbol == "BTCUSDC" else Decimal("0.999")
        price = Decimal("100")
        rows = []
        for _ in range(limit):
            price *= multiplier
            rows.append([0, "0", "0", "0", str(price), "0"])
        return rows


class FailingClient:
    def get_24h_tickers(self) -> list[dict]:
        raise BinanceApiError("offline")


def _ticker(symbol: str, change: str, volume: str, high: str, low: str, weighted: str, count: int) -> dict:
    return {
        "symbol": symbol,
        "priceChangePercent": change,
        "quoteVolume": volume,
        "highPrice": high,
        "lowPrice": low,
        "weightedAvgPrice": weighted,
        "count": count,
    }


def _config() -> dict:
    return {
        "app": {"mock_data": False},
        "market_research": {
            "enabled": True,
            "breadth_quote_asset": "USDC",
            "min_quote_volume_24h": 100000,
            "max_movers": 3,
            "multi_timeframe_interval": "4h",
            "kline_limit": 180,
            "excluded_breadth_assets": ["USDC", "USDT", "FDUSD"],
        },
    }


def _snapshots() -> list[MarketSnapshot]:
    return [
        MarketSnapshot(
            symbol="BTCUSDC",
            price=Decimal("100"),
            ema20=Decimal("99"),
            ema50=Decimal("98"),
            ema200=Decimal("80"),
            rsi14=Decimal("55"),
            atr14=Decimal("4"),
            volume_trend="rising",
            trend_regime="RISK_ON",
        ),
        MarketSnapshot(
            symbol="ETHUSDC",
            price=Decimal("100"),
            ema20=Decimal("101"),
            ema50=Decimal("102"),
            ema200=Decimal("110"),
            rsi14=Decimal("40"),
            atr14=Decimal("5"),
            volume_trend="falling",
            trend_regime="RISK_OFF",
        ),
    ]


def test_collects_multitimeframe_context_and_filtered_breadth(tmp_path) -> None:
    report = MarketResearchCollector(_config(), FakeClient()).collect(_snapshots())

    assert report.status == "OK"
    assert len(report.symbols) == 2
    assert report.symbols[0].return_7d_pct is not None
    assert report.symbols[0].return_30d_pct is not None
    assert report.symbols[1].relative_strength_vs_btc_24h_pct == Decimal("-3")
    assert report.breadth is not None
    assert report.breadth.symbols_analyzed == 3
    assert report.breadth.advancing == 2
    assert report.breadth.declining == 1
    assert report.breadth.top_gainers[0].symbol == "SOLUSDC"

    storage = Storage(tmp_path / "agent.sqlite3")
    run_id = storage.start_run("TEST")
    storage.save_market_research(run_id, report)
    count = storage.connection.execute(
        "select count(*) as count from market_research_symbols where run_id = ?",
        (run_id,),
    ).fetchone()["count"]
    assert count == 2


def test_public_market_failure_does_not_raise() -> None:
    report = MarketResearchCollector(_config(), FailingClient()).collect(_snapshots())

    assert report.status == "PARTIAL"
    assert report.symbols == ()
    assert report.breadth is None
    assert "offline" in report.errors[0]
