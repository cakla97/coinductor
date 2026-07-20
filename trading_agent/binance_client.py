from __future__ import annotations

from decimal import Decimal
import hashlib
import hmac
import json
import os
import ssl
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Balance, MarketSnapshot, SymbolRules


class BinanceApiError(RuntimeError):
    pass


class BinanceClient:
    def __init__(self, config: dict, use_testnet: bool = False, credential_profile: str = "mainnet_read"):
        self.config = config
        self.use_testnet = use_testnet
        self.credential_profile = "testnet" if use_testnet else credential_profile
        key_env, secret_env = self._credential_env_names()
        self.api_key = os.getenv(key_env, "")
        self.api_secret = os.getenv(secret_env, "")
        base_key = "testnet_api_base_url" if use_testnet else "api_base_url"
        self.base_url = str(config["binance"].get(base_key, "https://api.binance.com")).rstrip("/")
        self.ssl_context = self._ssl_context()
        self._server_time_offset_ms: int | None = None

    def _credential_env_names(self) -> tuple[str, str]:
        if self.credential_profile == "testnet":
            return "BINANCE_TESTNET_API_KEY", "BINANCE_TESTNET_API_SECRET"
        if self.credential_profile == "live_trade":
            return "BINANCE_LIVE_TRADE_API_KEY", "BINANCE_LIVE_TRADE_API_SECRET"
        return "BINANCE_API_KEY", "BINANCE_API_SECRET"

    def get_balances(self) -> list[Balance]:
        if self.config["app"].get("mock_data", True):
            return [
                Balance(asset="USDC", spot_free=Decimal("12"), flexible_amount=Decimal("250")),
                Balance(asset="USDT", spot_free=Decimal("0"), flexible_amount=Decimal("0")),
                Balance(asset="BTC", spot_free=Decimal("0.0000"), flexible_amount=Decimal("0.003"), locked_amount=Decimal("0.01")),
                Balance(asset="ETH", spot_free=Decimal("0.000"), flexible_amount=Decimal("0.05")),
                Balance(asset="BNB", spot_free=Decimal("0.00"), flexible_amount=Decimal("0.2")),
            ]

        self.assert_read_only_permissions()
        spot_balances = self._get_spot_balances()
        flexible_balances = self._get_flexible_balances()
        locked_balances = self._get_locked_balances()
        assets = sorted(set(spot_balances) | set(flexible_balances) | set(locked_balances))
        return [
            Balance(
                asset=asset,
                spot_free=spot_balances.get(asset, (Decimal("0"), Decimal("0")))[0],
                spot_locked=spot_balances.get(asset, (Decimal("0"), Decimal("0")))[1],
                flexible_amount=flexible_balances.get(asset, Decimal("0")),
                locked_amount=locked_balances.get(asset, Decimal("0")),
            )
            for asset in assets
        ]

    def get_market_snapshots(self, symbols: list[str]) -> list[MarketSnapshot]:
        if self.config["app"].get("mock_data", True):
            prices = {
                "BTCUSDT": Decimal("104000"),
                "BTCUSDC": Decimal("104000"),
                "ETHUSDT": Decimal("3600"),
                "ETHUSDC": Decimal("3600"),
                "BNBUSDT": Decimal("650"),
                "BNBUSDC": Decimal("650"),
                "SOLUSDC": Decimal("150"),
                "WLDUSDC": Decimal("3"),
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
        return [self._get_market_snapshot(symbol) for symbol in symbols]

    def get_asset_prices_usdt(self, assets: list[str]) -> dict[str, Decimal]:
        if self.config["app"].get("mock_data", True):
            return {
                "USDT": Decimal("1"),
                "USDC": Decimal("1"),
                "BTC": Decimal("104000"),
                "ETH": Decimal("3600"),
                "WBETH": Decimal("3700"),
                "BNB": Decimal("650"),
                "SOL": Decimal("150"),
                "WLD": Decimal("3"),
            }
        tickers = self._public_get("/api/v3/ticker/price")
        ticker_map = {row["symbol"]: Decimal(row["price"]) for row in tickers}
        return self._price_assets_from_tickers({asset.upper() for asset in assets}, ticker_map)

    def get_symbol_rules(self, symbol: str) -> SymbolRules:
        payload = self._public_get("/api/v3/exchangeInfo", {"symbol": symbol.upper()})
        symbols = payload.get("symbols", [])
        if not symbols:
            raise BinanceApiError(f"Symbol {symbol.upper()} was not found in exchangeInfo.")
        row = symbols[0]
        filters = {item["filterType"]: item for item in row.get("filters", [])}
        lot_size = filters.get("LOT_SIZE", {})
        price_filter = filters.get("PRICE_FILTER", {})
        notional_filter = filters.get("NOTIONAL") or filters.get("MIN_NOTIONAL") or {}
        return SymbolRules(
            symbol=row["symbol"],
            status=row.get("status", ""),
            base_asset=row.get("baseAsset", ""),
            quote_asset=row.get("quoteAsset", ""),
            quote_order_qty_market_allowed=bool(row.get("quoteOrderQtyMarketAllowed", False)),
            min_qty=Decimal(str(lot_size.get("minQty", "0"))),
            max_qty=Decimal(str(lot_size.get("maxQty", "0"))),
            step_size=Decimal(str(lot_size.get("stepSize", "0"))),
            min_notional=Decimal(str(notional_filter.get("minNotional", "0"))),
            tick_size=Decimal(str(price_filter.get("tickSize", "0"))),
        )

    def get_symbol_price(self, symbol: str) -> Decimal:
        payload = self._public_get("/api/v3/ticker/price", {"symbol": symbol.upper()})
        return Decimal(str(payload["price"]))

    def get_24h_tickers(self) -> list[dict]:
        payload = self._public_get("/api/v3/ticker/24hr")
        if not isinstance(payload, list):
            raise BinanceApiError("Unexpected Binance 24h ticker response.")
        return payload

    def get_symbol_market_snapshot(self, symbol: str) -> dict:
        payload = self._public_get("/api/v3/ticker/24hr", {"symbol": symbol.upper()})
        if not isinstance(payload, dict):
            raise BinanceApiError(f"Unexpected Binance 24h ticker response for {symbol.upper()}.")
        return payload

    def get_klines(self, symbol: str, interval: str, limit: int) -> list[list]:
        payload = self._public_get(
            "/api/v3/klines",
            {"symbol": symbol.upper(), "interval": interval, "limit": limit},
        )
        if not isinstance(payload, list):
            raise BinanceApiError(f"Unexpected Binance kline response for {symbol.upper()}.")
        return payload

    def get_historical_close(self, symbol: str, timestamp_ms: int) -> Decimal:
        payload = self._public_get(
            "/api/v3/klines",
            {
                "symbol": symbol.upper(),
                "interval": "1m",
                "startTime": timestamp_ms,
                "limit": 1,
            },
        )
        if not isinstance(payload, list) or not payload:
            raise BinanceApiError(f"No historical candle returned for {symbol.upper()} at {timestamp_ms}.")
        return Decimal(str(payload[0][4]))

    def assert_read_only_permissions(self) -> None:
        if self.use_testnet:
            raise BinanceApiError("Read-only permission check uses /sapi and is not available on Spot Testnet.")
        permissions = self._signed_get("/sapi/v1/account/apiRestrictions")
        dangerous_flags = {
            "enableWithdrawals": permissions.get("enableWithdrawals"),
            "enableInternalTransfer": permissions.get("enableInternalTransfer"),
            "permitsUniversalTransfer": permissions.get("permitsUniversalTransfer"),
            "enableMargin": permissions.get("enableMargin"),
            "enableFutures": permissions.get("enableFutures"),
            "enableVanillaOptions": permissions.get("enableVanillaOptions"),
            "enableSpotAndMarginTrading": permissions.get("enableSpotAndMarginTrading"),
            "enablePortfolioMarginTrading": permissions.get("enablePortfolioMarginTrading"),
        }
        if not permissions.get("enableReading"):
            raise BinanceApiError("Binance API key does not have reading enabled.")
        enabled = [name for name, value in dangerous_flags.items() if value]
        if enabled:
            raise BinanceApiError(f"Binance API key is not read-only. Disable these permissions: {', '.join(enabled)}")

    def assert_live_spot_permissions(self) -> None:
        if self.use_testnet:
            raise BinanceApiError("Live Spot permission check is not available on Spot Testnet.")
        permissions = self._signed_get("/sapi/v1/account/apiRestrictions")
        if not permissions.get("enableReading"):
            raise BinanceApiError("Live Binance API key must have Reading enabled.")
        if not permissions.get("enableSpotAndMarginTrading"):
            raise BinanceApiError("Live Binance API key must have Spot trading enabled.")
        forbidden_flags = {
            "withdrawals": permissions.get("enableWithdrawals"),
            "internal transfer": permissions.get("enableInternalTransfer"),
            "universal transfer": permissions.get("permitsUniversalTransfer"),
            "margin": permissions.get("enableMargin"),
            "futures": permissions.get("enableFutures"),
            "vanilla options": permissions.get("enableVanillaOptions"),
            "portfolio margin": permissions.get("enablePortfolioMarginTrading"),
        }
        enabled = [name for name, value in forbidden_flags.items() if value]
        if enabled:
            raise BinanceApiError(
                "Live Binance API key has forbidden permissions enabled: " + ", ".join(enabled)
            )
        if not permissions.get("ipRestrict"):
            raise BinanceApiError("Live Binance API key must be restricted to trusted IP addresses.")

    def _get_spot_balances(self) -> dict[str, tuple[Decimal, Decimal]]:
        payload = self._signed_get("/api/v3/account", {"omitZeroBalances": "true"})
        balances: dict[str, tuple[Decimal, Decimal]] = {}
        for row in payload.get("balances", []):
            free = Decimal(row["free"])
            locked = Decimal(row["locked"])
            if free or locked:
                balances[row["asset"]] = (free, locked)
        return balances

    def get_spot_free_balance(self, asset: str) -> Decimal:
        balances = self._get_spot_balances()
        return balances.get(asset.upper(), (Decimal("0"), Decimal("0")))[0]

    def _get_flexible_balances(self) -> dict[str, Decimal]:
        payload = self._signed_get("/sapi/v1/simple-earn/flexible/position", {"size": 100})
        balances: dict[str, Decimal] = {}
        for row in payload.get("rows", []):
            asset = row["asset"]
            balances[asset] = balances.get(asset, Decimal("0")) + Decimal(row["totalAmount"])
        return balances

    def get_flexible_positions(self, asset: str | None = None) -> list[dict]:
        payload = self._signed_get("/sapi/v1/simple-earn/flexible/position", {"size": 100})
        rows = list(payload.get("rows", []))
        if asset is None:
            return rows
        wanted = asset.upper()
        return [row for row in rows if str(row.get("asset", "")).upper() == wanted]

    def redeem_flexible_product(self, product_id: str, amount: Decimal, redeem_type: str = "FAST") -> dict:
        return self.signed_post(
            "/sapi/v1/simple-earn/flexible/redeem",
            {
                "productId": product_id,
                "amount": str(amount),
                "type": redeem_type,
            },
        )

    def _get_locked_balances(self) -> dict[str, Decimal]:
        payload = self._signed_get("/sapi/v1/simple-earn/locked/position", {"size": 100})
        balances: dict[str, Decimal] = {}
        for row in payload.get("rows", []):
            asset = row["asset"]
            balances[asset] = balances.get(asset, Decimal("0")) + Decimal(row["amount"])
        return balances

    def _get_market_snapshot(self, symbol: str) -> MarketSnapshot:
        klines = self.get_klines(symbol, "1d", 210)
        closes = [Decimal(row[4]) for row in klines]
        highs = [Decimal(row[2]) for row in klines]
        lows = [Decimal(row[3]) for row in klines]
        volumes = [Decimal(row[5]) for row in klines]
        price = closes[-1]
        ema20 = self._ema(closes, 20)
        ema50 = self._ema(closes, 50)
        ema200 = self._ema(closes, 200)
        rsi14 = self._rsi(closes, 14)
        atr14 = self._atr(highs, lows, closes, 14)
        recent_volume = sum(volumes[-7:]) / Decimal("7")
        prior_volume = sum(volumes[-14:-7]) / Decimal("7")
        volume_trend = "rising" if recent_volume >= prior_volume else "falling"
        trend_regime = self._trend_regime(price, ema20, ema50, ema200, rsi14)
        return MarketSnapshot(
            symbol=symbol,
            price=price,
            ema20=ema20,
            ema50=ema50,
            ema200=ema200,
            rsi14=rsi14,
            atr14=atr14,
            volume_trend=volume_trend,
            trend_regime=trend_regime,
        )

    def _signed_get(self, path: str, params: dict[str, object] | None = None) -> dict:
        self._require_api_keys()
        request_params = dict(params or {})
        request_params["timestamp"] = self._timestamp_ms()
        request_params["recvWindow"] = int(self.config["binance"].get("recv_window_ms", 5000))
        query = urlencode(request_params)
        signature = hmac.new(self.api_secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()
        return self._request("GET", f"{path}?{query}&signature={signature}", signed=True)

    def signed_post(self, path: str, params: dict[str, object] | None = None) -> dict:
        self._require_api_keys()
        request_params = dict(params or {})
        request_params["timestamp"] = self._timestamp_ms()
        request_params["recvWindow"] = int(self.config["binance"].get("recv_window_ms", 5000))
        query = urlencode(request_params)
        signature = hmac.new(self.api_secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()
        return self._request("POST", f"{path}?{query}&signature={signature}", signed=True)

    def testnet_account_ping(self) -> dict:
        if not self.use_testnet:
            raise BinanceApiError("testnet_account_ping requires use_testnet=True.")
        return self._signed_get("/api/v3/account")

    def testnet_free_balance(self, asset: str) -> Decimal:
        account = self.testnet_account_ping()
        for row in account.get("balances", []):
            if row.get("asset", "").upper() == asset.upper():
                return Decimal(str(row.get("free", "0")))
        return Decimal("0")

    def query_order(self, symbol: str, order_id: str | None = None, client_order_id: str | None = None) -> dict:
        params: dict[str, object] = {"symbol": symbol.upper()}
        if order_id:
            params["orderId"] = order_id
        if client_order_id:
            params["origClientOrderId"] = client_order_id
        if "orderId" not in params and "origClientOrderId" not in params:
            raise BinanceApiError("query_order requires order_id or client_order_id.")
        return self._signed_get("/api/v3/order", params)

    def query_order_list(self, order_list_id: str | None = None, list_client_order_id: str | None = None) -> dict:
        params: dict[str, object] = {}
        if order_list_id:
            params["orderListId"] = order_list_id
        if list_client_order_id:
            params["listClientOrderId"] = list_client_order_id
        if "orderListId" not in params and "listClientOrderId" not in params:
            raise BinanceApiError("query_order_list requires order_list_id or list_client_order_id.")
        return self._signed_get("/api/v3/orderList", params)

    def submit_market_buy_quote(self, symbol: str, quote_amount: Decimal, client_order_id: str) -> dict:
        return self.signed_post(
            "/api/v3/order",
            {
                "symbol": symbol.upper(),
                "side": "BUY",
                "type": "MARKET",
                "quoteOrderQty": str(quote_amount),
                "newClientOrderId": client_order_id,
            },
        )

    def submit_sell_oco_protection(
        self,
        symbol: str,
        quantity: Decimal,
        take_profit_price: Decimal,
        stop_loss_stop_price: Decimal,
        list_client_order_id: str,
        above_client_order_id: str,
        below_client_order_id: str,
    ) -> dict:
        return self.signed_post(
            "/api/v3/orderList/oco",
            {
                "symbol": symbol.upper(),
                "side": "SELL",
                "quantity": str(quantity),
                "listClientOrderId": list_client_order_id,
                "aboveType": "LIMIT_MAKER",
                "abovePrice": str(take_profit_price),
                "aboveClientOrderId": above_client_order_id,
                "belowType": "STOP_LOSS",
                "belowStopPrice": str(stop_loss_stop_price),
                "belowClientOrderId": below_client_order_id,
                "newOrderRespType": "RESULT",
            },
        )

    def _public_get(self, path: str, params: dict[str, object] | None = None) -> list | dict:
        query = urlencode(params or {})
        suffix = f"?{query}" if query else ""
        return self._request("GET", f"{path}{suffix}", signed=False)

    def _request(self, method: str, path_with_query: str, signed: bool) -> list | dict:
        headers = {"User-Agent": "binance-trading-agent/0.1"}
        if signed:
            headers["X-MBX-APIKEY"] = self.api_key
        request = Request(f"{self.base_url}{path_with_query}", headers=headers, method=method)
        try:
            with urlopen(request, timeout=int(self.config["binance"].get("timeout_seconds", 30)), context=self.ssl_context) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise BinanceApiError(f"Binance API HTTP {exc.code}: {body}") from exc
        except URLError as exc:
            raise BinanceApiError(f"Binance API connection failed: {exc.reason}") from exc

    def _require_api_keys(self) -> None:
        if not self.api_key or not self.api_secret:
            if self.use_testnet:
                raise BinanceApiError("BINANCE_TESTNET_API_KEY and BINANCE_TESTNET_API_SECRET must be set in .env for testnet mode.")
            if self.credential_profile == "live_trade":
                raise BinanceApiError("BINANCE_LIVE_TRADE_API_KEY and BINANCE_LIVE_TRADE_API_SECRET must be set in .env for LIVE_CONFIRM preview.")
            raise BinanceApiError("BINANCE_API_KEY and BINANCE_API_SECRET must be set in .env for real-data mode.")

    def _timestamp_ms(self) -> int:
        if self._server_time_offset_ms is None:
            payload = self._public_get("/api/v3/time")
            server_time = int(payload["serverTime"])
            local_time = int(time.time() * 1000)
            self._server_time_offset_ms = server_time - local_time
        return int(time.time() * 1000) + self._server_time_offset_ms

    def _ssl_context(self) -> ssl.SSLContext:
        try:
            import truststore

            return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        except ImportError:
            pass
        try:
            import certifi

            return ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            return ssl.create_default_context()

    def _ema(self, values: list[Decimal], period: int) -> Decimal:
        multiplier = Decimal("2") / Decimal(period + 1)
        ema = sum(values[:period]) / Decimal(period)
        for value in values[period:]:
            ema = (value - ema) * multiplier + ema
        return ema

    def _rsi(self, closes: list[Decimal], period: int) -> Decimal:
        gains: list[Decimal] = []
        losses: list[Decimal] = []
        for previous, current in zip(closes[-period - 1 : -1], closes[-period:]):
            change = current - previous
            gains.append(max(change, Decimal("0")))
            losses.append(abs(min(change, Decimal("0"))))
        average_gain = sum(gains) / Decimal(period)
        average_loss = sum(losses) / Decimal(period)
        if average_loss == 0:
            return Decimal("100")
        relative_strength = average_gain / average_loss
        return Decimal("100") - (Decimal("100") / (Decimal("1") + relative_strength))

    def _atr(self, highs: list[Decimal], lows: list[Decimal], closes: list[Decimal], period: int) -> Decimal:
        true_ranges: list[Decimal] = []
        for index in range(1, len(closes)):
            true_ranges.append(
                max(
                    highs[index] - lows[index],
                    abs(highs[index] - closes[index - 1]),
                    abs(lows[index] - closes[index - 1]),
                )
            )
        return sum(true_ranges[-period:]) / Decimal(period)

    def _trend_regime(self, price: Decimal, ema20: Decimal, ema50: Decimal, ema200: Decimal, rsi14: Decimal) -> str:
        if price > ema50 > ema200 and Decimal("40") <= rsi14 <= Decimal("70"):
            return "RISK_ON"
        if price < ema50 < ema200 or rsi14 < Decimal("35"):
            return "RISK_OFF"
        return "NEUTRAL"

    def _price_assets_from_tickers(self, assets: set[str], ticker_map: dict[str, Decimal]) -> dict[str, Decimal]:
        prices: dict[str, Decimal] = {"USDT": Decimal("1"), "USDC": Decimal("1"), "FDUSD": Decimal("1")}
        quote_assets = [quote.upper() for quote in self.config.get("portfolio", {}).get("pricing_quote_assets", ["USDT"])]
        pending = set(assets)
        for asset in list(pending):
            if asset in prices:
                pending.discard(asset)
                continue
            for quote in quote_assets:
                symbol = f"{asset}{quote}"
                if symbol in ticker_map:
                    prices[asset] = ticker_map[symbol] * prices.get(quote, Decimal("1"))
                    pending.discard(asset)
                    break

        if "ETH" not in prices and "ETHUSDT" in ticker_map:
            prices["ETH"] = ticker_map["ETHUSDT"]
        if "BTC" not in prices and "BTCUSDT" in ticker_map:
            prices["BTC"] = ticker_map["BTCUSDT"]

        for asset in list(pending):
            eth_pair = f"{asset}ETH"
            btc_pair = f"{asset}BTC"
            if eth_pair in ticker_map and "ETH" in prices:
                prices[asset] = ticker_map[eth_pair] * prices["ETH"]
                pending.discard(asset)
            elif btc_pair in ticker_map and "BTC" in prices:
                prices[asset] = ticker_map[btc_pair] * prices["BTC"]
                pending.discard(asset)
        return {asset: price for asset, price in prices.items() if asset in assets or asset in {"USDT", "USDC", "FDUSD"}}
