"""Notice new pairs on the exchange. Never buy one.

The strategy this was asked for - buy at listing, sell fast - is not
implementable competitively from a desktop app on a home connection, and the
reasoning is in docs/automation-proposal.md. What is worth having is the part
underneath it: a record of what actually appeared, when this machine saw it,
and at what price. After a dozen listings that is evidence rather than
intuition, and it is what any later decision should be built on.

So this watches, records, and notifies. Acting on a listing goes through the
same guarded path as any other trade, started by a person.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from trading_agent.binance_client import BinanceApiError, BinanceClient
from trading_agent.storage import Storage

# How many listings the journal keeps. High enough to cover a year of Binance's
# pace with room to spare, low enough that the table cannot become the reason a
# journal is large.
DEFAULT_KEEP = 200

# A first sighting is only interesting for pairs someone could actually act on.
# Binance lists the same base asset against many quotes; recording all of them
# turns one listing into eight rows saying the same thing.
INTERESTING_QUOTES = ("USDC", "USDT", "FDUSD", "BTC")


@dataclass(frozen=True)
class ListingScan:
    """What one pass over the exchange found."""

    new_listings: tuple[dict[str, object], ...]
    total_known: int
    error: str = ""

    @property
    def ok(self) -> bool:
        return not self.error


class ListingWatcher:
    def __init__(self, config: dict, storage: Storage, keep: int = DEFAULT_KEEP):
        self.config = config
        self.storage = storage
        self.keep = keep

    def scan(self) -> ListingScan:
        """One pass. Never raises: a watcher that dies on a timeout is useless."""
        try:
            symbols = self._trading_symbols()
        except BinanceApiError as exc:
            return ListingScan((), self._known_count(), error=str(exc))
        except Exception as exc:  # noqa: BLE001 - a watcher must survive anything
            return ListingScan((), self._known_count(), error=type(exc).__name__)

        known = self.storage.known_listing_symbols()
        first_ever = not known
        seen_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        candidates = [
            {
                "symbol": symbol,
                "baseAsset": base,
                "quoteAsset": quote,
                "status": "TRADING",
                "firstSeenAt": seen_at,
                "firstPrice": "",
            }
            for symbol, base, quote in symbols
            if symbol not in known
        ]

        # The baseline goes into its own uncapped table, always. Storing it in
        # the capped one meant the cap silently discarded most of it, and every
        # discarded pair looked new again on the next pass - 400 false listings
        # on the second scan of a real exchange.
        self.storage.remember_listing_symbols([(symbol, seen_at) for symbol, _, _ in symbols])

        # The first scan sees the entire exchange, which is true and useless:
        # nobody wants six hundred notifications on the day they switch this on.
        # The baseline is remembered; only what appears after it is news, and
        # only news is stored where the screen will show it.
        if first_ever:
            return ListingScan((), self._known_count())

        added = self.storage.record_listings(candidates)
        self.storage.prune_listing_events(self.keep)
        return ListingScan(tuple(added), self._known_count())

    def _trading_symbols(self) -> list[tuple[str, str, str]]:
        client = BinanceClient(self.config)
        info = client.get_exchange_info()
        symbols = info.get("symbols", []) if isinstance(info, dict) else []
        found: list[tuple[str, str, str]] = []
        for entry in symbols:
            if not isinstance(entry, dict) or entry.get("status") != "TRADING":
                continue
            quote = str(entry.get("quoteAsset", "")).upper()
            if quote not in INTERESTING_QUOTES:
                continue
            found.append(
                (
                    str(entry.get("symbol", "")).upper(),
                    str(entry.get("baseAsset", "")).upper(),
                    quote,
                )
            )
        return found

    def _known_count(self) -> int:
        return len(self.storage.known_listing_symbols())
