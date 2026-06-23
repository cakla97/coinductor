from __future__ import annotations

from decimal import Decimal

from .binance_client import BinanceApiError, BinanceClient
from .models import MarketBreadth, MarketMover, MarketResearchReport, MarketSnapshot, SymbolMarketResearch


class MarketResearchCollector:
    def __init__(self, config: dict, client: BinanceClient):
        self.config = config
        self.client = client

    def collect(self, snapshots: list[MarketSnapshot]) -> MarketResearchReport:
        research = self.config.get("market_research", {})
        if not research.get("enabled", True):
            return MarketResearchReport(False, "DISABLED", (), None, (), "Local market research is disabled.")
        if self.config.get("app", {}).get("mock_data", True):
            return self._mock_report(snapshots)

        errors: list[str] = []
        try:
            tickers = self.client.get_24h_tickers()
        except BinanceApiError as exc:
            return MarketResearchReport(
                True,
                "PARTIAL",
                (),
                None,
                (str(exc),),
                "Local market research could not load Binance 24h ticker data; the main run continued.",
            )

        ticker_by_symbol = {str(row.get("symbol", "")).upper(): row for row in tickers}
        btc_ticker = ticker_by_symbol.get("BTCUSDC")
        btc_change = self._decimal(btc_ticker.get("priceChangePercent")) if btc_ticker is not None else None
        try:
            symbol_reports: list[SymbolMarketResearch] = []
            interval = str(research.get("multi_timeframe_interval", "4h"))
            kline_limit = int(research.get("kline_limit", 180))
            for snapshot in snapshots:
                ticker = ticker_by_symbol.get(snapshot.symbol.upper())
                if ticker is None:
                    errors.append(f"No 24h ticker was returned for {snapshot.symbol}.")
                    continue
                closes: list[Decimal] = []
                try:
                    klines = self.client.get_klines(snapshot.symbol, interval, kline_limit)
                    closes = [Decimal(str(row[4])) for row in klines]
                except Exception as exc:
                    errors.append(f"{snapshot.symbol} multi-timeframe data failed: {exc}")

                change_24h = self._decimal(ticker.get("priceChangePercent"))
                symbol_reports.append(
                    SymbolMarketResearch(
                        symbol=snapshot.symbol,
                        change_24h_pct=change_24h,
                        return_7d_pct=self._period_return(closes, 42),
                        return_30d_pct=self._period_return(closes, 179),
                        quote_volume_24h=self._decimal(ticker.get("quoteVolume")),
                        trades_24h=int(ticker.get("count", 0) or 0),
                        range_24h_pct=self._range_pct(ticker),
                        atr_pct=self._safe_pct(snapshot.atr14, snapshot.price),
                        price_vs_ema200_pct=self._safe_pct(snapshot.price - snapshot.ema200, snapshot.ema200),
                        relative_strength_vs_btc_24h_pct=change_24h - btc_change if btc_change is not None else None,
                        volume_trend=snapshot.volume_trend,
                        trend_regime=snapshot.trend_regime,
                    )
                )
            breadth = self._breadth(tickers)
        except Exception as exc:
            errors.append(f"Market research parsing failed: {exc}")
            return MarketResearchReport(
                True,
                "PARTIAL",
                (),
                None,
                tuple(errors),
                "Local market research returned malformed data; the main run continued without it.",
            )
        status = "OK" if not errors else "PARTIAL"
        summary = self._summary(symbol_reports, breadth, errors)
        return MarketResearchReport(True, status, tuple(symbol_reports), breadth, tuple(errors), summary)

    def _breadth(self, tickers: list[dict]) -> MarketBreadth:
        research = self.config.get("market_research", {})
        quote_asset = str(research.get("breadth_quote_asset", "USDC")).upper()
        min_volume = Decimal(str(research.get("min_quote_volume_24h", "1000000")))
        max_movers = int(research.get("max_movers", 5))
        excluded_bases = {
            str(asset).upper()
            for asset in research.get(
                "excluded_breadth_assets",
                ["USDC", "USDT", "FDUSD", "TUSD", "DAI", "USD1", "USDE", "EURI", "EUR"],
            )
        }
        rows: list[MarketMover] = []
        for ticker in tickers:
            symbol = str(ticker.get("symbol", "")).upper()
            if not symbol.endswith(quote_asset):
                continue
            base_asset = symbol[: -len(quote_asset)]
            if base_asset in excluded_bases or self._looks_leveraged(base_asset):
                continue
            quote_volume = self._decimal(ticker.get("quoteVolume"))
            if quote_volume < min_volume:
                continue
            rows.append(
                MarketMover(
                    symbol=symbol,
                    change_24h_pct=self._decimal(ticker.get("priceChangePercent")),
                    quote_volume_24h=quote_volume,
                )
            )

        changes = sorted(row.change_24h_pct for row in rows)
        advancing = sum(1 for change in changes if change > 0)
        declining = sum(1 for change in changes if change < 0)
        unchanged = len(changes) - advancing - declining
        return MarketBreadth(
            quote_asset=quote_asset,
            symbols_analyzed=len(rows),
            advancing=advancing,
            declining=declining,
            unchanged=unchanged,
            advance_pct=self._safe_pct(Decimal(advancing), Decimal(len(rows))),
            median_change_24h_pct=self._median(changes),
            top_gainers=tuple(sorted(rows, key=lambda item: item.change_24h_pct, reverse=True)[:max_movers]),
            top_losers=tuple(sorted(rows, key=lambda item: item.change_24h_pct)[:max_movers]),
            top_volume=tuple(sorted(rows, key=lambda item: item.quote_volume_24h, reverse=True)[:max_movers]),
        )

    def _mock_report(self, snapshots: list[MarketSnapshot]) -> MarketResearchReport:
        symbols = tuple(
            SymbolMarketResearch(
                symbol=snapshot.symbol,
                change_24h_pct=Decimal("1.5"),
                return_7d_pct=Decimal("3.2"),
                return_30d_pct=Decimal("6.4"),
                quote_volume_24h=Decimal("1000000"),
                trades_24h=10000,
                range_24h_pct=Decimal("4"),
                atr_pct=self._safe_pct(snapshot.atr14, snapshot.price),
                price_vs_ema200_pct=self._safe_pct(snapshot.price - snapshot.ema200, snapshot.ema200),
                relative_strength_vs_btc_24h_pct=Decimal("0"),
                volume_trend=snapshot.volume_trend,
                trend_regime=snapshot.trend_regime,
            )
            for snapshot in snapshots
        )
        movers = tuple(MarketMover(item.symbol, item.change_24h_pct, item.quote_volume_24h) for item in symbols[:2])
        breadth = MarketBreadth(
            "USDC",
            len(symbols),
            len(symbols),
            0,
            0,
            Decimal("100"),
            Decimal("1.5"),
            movers,
            movers,
            movers,
        )
        return MarketResearchReport(True, "MOCK", symbols, breadth, (), "Mock local market research generated.")

    def _summary(
        self,
        symbols: list[SymbolMarketResearch],
        breadth: MarketBreadth,
        errors: list[str],
    ) -> str:
        prefix = (
            f"{breadth.advancing}/{breadth.symbols_analyzed} liquid {breadth.quote_asset} pairs advanced "
            f"({breadth.advance_pct:.2f}%); median 24h change {breadth.median_change_24h_pct:.2f}%."
        )
        if symbols:
            context = "; ".join(
                f"{item.symbol} {item.change_24h_pct:+.2f}%/24h, {item.trend_regime}"
                for item in symbols
            )
            prefix += f" Allowed universe: {context}."
        if errors:
            prefix += f" Partial data: {len(errors)} warning(s)."
        return prefix

    def _period_return(self, closes: list[Decimal], periods: int) -> Decimal | None:
        if len(closes) <= periods:
            return None
        base = closes[-periods - 1]
        if base == 0:
            return None
        return (closes[-1] / base - Decimal("1")) * Decimal("100")

    def _range_pct(self, ticker: dict) -> Decimal:
        high = self._decimal(ticker.get("highPrice"))
        low = self._decimal(ticker.get("lowPrice"))
        weighted = self._decimal(ticker.get("weightedAvgPrice"))
        return self._safe_pct(high - low, weighted)

    def _median(self, values: list[Decimal]) -> Decimal:
        if not values:
            return Decimal("0")
        middle = len(values) // 2
        if len(values) % 2:
            return values[middle]
        return (values[middle - 1] + values[middle]) / Decimal("2")

    def _safe_pct(self, numerator: Decimal, denominator: Decimal) -> Decimal:
        if denominator == 0:
            return Decimal("0")
        return numerator / denominator * Decimal("100")

    def _decimal(self, value: object) -> Decimal:
        if value in (None, ""):
            return Decimal("0")
        return Decimal(str(value))

    def _looks_leveraged(self, base_asset: str) -> bool:
        return base_asset.endswith(("UP", "DOWN", "BULL", "BEAR"))
