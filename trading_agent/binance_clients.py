"""Choosing between the live exchange and the offline fixture.

``BinanceClient`` used to carry its own mock branches, so three of its methods
began by answering a question that has nothing to do with talking to Binance.
The fixture now lives in a subclass and the choice is made once, at construction,
by :func:`create_binance_client`.

Mock mode is what the first run and the whole test suite use, so these numbers
are effectively the project's demo portfolio rather than throwaway stubs.
"""

from __future__ import annotations

from decimal import Decimal

from .binance_client import BinanceClient
from .models import Balance, MarketSnapshot

_MOCK_BALANCES: tuple[Balance, ...] = (
    Balance(asset="USDC", spot_free=Decimal("12"), flexible_amount=Decimal("250")),
    Balance(asset="USDT", spot_free=Decimal("0"), flexible_amount=Decimal("0")),
    Balance(asset="BTC", spot_free=Decimal("0.0000"), flexible_amount=Decimal("0.003"), locked_amount=Decimal("0.01")),
    Balance(asset="ETH", spot_free=Decimal("0.000"), flexible_amount=Decimal("0.05")),
    Balance(asset="BNB", spot_free=Decimal("0.00"), flexible_amount=Decimal("0.2")),
)

_MOCK_SYMBOL_PRICES: dict[str, Decimal] = {
    "BTCUSDT": Decimal("104000"),
    "BTCUSDC": Decimal("104000"),
    "ETHUSDT": Decimal("3600"),
    "ETHUSDC": Decimal("3600"),
    "BNBUSDT": Decimal("650"),
    "BNBUSDC": Decimal("650"),
    "SOLUSDC": Decimal("150"),
    "WLDUSDC": Decimal("3"),
}

_MOCK_ASSET_PRICES: dict[str, Decimal] = {
    "USDT": Decimal("1"),
    "USDC": Decimal("1"),
    "BTC": Decimal("104000"),
    "ETH": Decimal("3600"),
    "WBETH": Decimal("3700"),
    "BNB": Decimal("650"),
    "SOL": Decimal("150"),
    "WLD": Decimal("3"),
}

_UNKNOWN_SYMBOL_PRICE = Decimal("1")


class MockBinanceClient(BinanceClient):
    """Serves a fixed portfolio and market so a run works with no network.

    Only the three read methods a run starts from are overridden. Anything else
    still reaches the real client, which will fail without credentials: that is
    deliberate, because a mock run has no business submitting orders.
    """

    def get_balances(self) -> list[Balance]:
        return list(_MOCK_BALANCES)

    def get_market_snapshots(self, symbols: list[str]) -> list[MarketSnapshot]:
        return [self._mock_snapshot(symbol) for symbol in symbols]

    def get_asset_prices_usdt(self, assets: list[str]) -> dict[str, Decimal]:
        return dict(_MOCK_ASSET_PRICES)

    @staticmethod
    def _mock_snapshot(symbol: str) -> MarketSnapshot:
        price = _MOCK_SYMBOL_PRICES.get(symbol, _UNKNOWN_SYMBOL_PRICE)
        return MarketSnapshot(
            symbol=symbol,
            price=price,
            ema20=price * Decimal("1.01"),
            ema50=price * Decimal("0.99"),
            ema200=price * Decimal("0.90"),
            rsi14=Decimal("58"),
            atr14=price * Decimal("0.025"),
            volume_trend="rising",
            trend_regime="RISK_ON",
        )


def create_binance_client(
    config: dict,
    use_testnet: bool = False,
    credential_profile: str = "mainnet_read",
) -> BinanceClient:
    """Build the client this config asks for. Mock is the default, as before."""
    if config.get("app", {}).get("mock_data", True):
        return MockBinanceClient(config, use_testnet=use_testnet, credential_profile=credential_profile)
    return BinanceClient(config, use_testnet=use_testnet, credential_profile=credential_profile)
