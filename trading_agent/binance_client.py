from __future__ import annotations

from decimal import Decimal
import os

from .models import Balance, MarketSnapshot


class BinanceClient:
    def __init__(self, config: dict):
        self.config = config
        self.api_key = os.getenv("BINANCE_API_KEY", "")
        self.api_secret = os.getenv("BINANCE_API_SECRET", "")

    def get_balances(self) -> list[Balance]:
        if self.config["app"].get("mock_data", True):
            return [
                Balance(asset="USDT", spot_free=Decimal("0"), flexible_amount=Decimal("250")),
                Balance(asset="BTC", spot_free=Decimal("0.0000"), flexible_amount=Decimal("0.003"), locked_amount=Decimal("0.01")),
                Balance(asset="ETH", spot_free=Decimal("0.000"), flexible_amount=Decimal("0.05")),
                Balance(asset="BNB", spot_free=Decimal("0.00"), flexible_amount=Decimal("0.2")),
            ]
        raise NotImplementedError("Real Binance account calls are planned for the next iteration.")

    def get_market_snapshots(self, symbols: list[str]) -> list[MarketSnapshot]:
        if self.config["app"].get("mock_data", True):
            prices = {
                "BTCUSDT": Decimal("104000"),
                "ETHUSDT": Decimal("3600"),
                "BNBUSDT": Decimal("650"),
            }
            return [
                MarketSnapshot(
                    symbol=symbol,
                    price=prices.get(symbol, Decimal("1")),
                    ema20=prices.get(symbol, Decimal("1")) * Decimal("1.01"),
                    ema50=prices.get(symbol, Decimal("1")) * Decimal("0.99"),
                    ema200=prices.get(symbol, Decimal("1")) * Decimal("0.90"),
                    rsi14=Decimal("58"),
                    atr14=prices.get(symbol, Decimal("1")) * Decimal("0.025"),
                    volume_trend="rising",
                    trend_regime="RISK_ON",
                )
                for symbol in symbols
            ]
        raise NotImplementedError("Real Binance market calls are planned for the next iteration.")

