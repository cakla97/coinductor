"""The listing watcher: notices new pairs, never buys one.

The interesting cases are the ones that would make it useless in practice - a
first scan reporting the whole exchange, an outage killing the loop, and a
table with no run_id growing without limit because run retention cannot see it.
"""

from pathlib import Path

import pytest

from coinductor.listing_watcher import INTERESTING_QUOTES, ListingWatcher
from trading_agent.binance_client import BinanceApiError, BinanceClient
from trading_agent.storage import Storage

CONFIG: dict = {"binance": {"api_base_url": "https://api.binance.com"}, "app": {}}


def _storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "journal.sqlite3")


def _info(*pairs: tuple[str, str, str], status: str = "TRADING") -> dict:
    return {
        "symbols": [
            {"symbol": symbol, "baseAsset": base, "quoteAsset": quote, "status": status}
            for symbol, base, quote in pairs
        ]
    }


def _serve(monkeypatch, payload) -> None:
    def fake(self):
        if isinstance(payload, Exception):
            raise payload
        return payload

    monkeypatch.setattr(BinanceClient, "get_exchange_info", fake)


def test_the_first_scan_records_a_baseline_without_reporting_it(tmp_path, monkeypatch) -> None:
    """Turning this on must not produce a notification per existing pair."""
    storage = _storage(tmp_path)
    _serve(monkeypatch, _info(("BTCUSDC", "BTC", "USDC"), ("ETHUSDC", "ETH", "USDC")))

    scan = ListingWatcher(CONFIG, storage).scan()

    assert scan.ok
    assert scan.new_listings == ()
    assert scan.total_known == 2
    assert storage.known_listing_symbols() == {"BTCUSDC", "ETHUSDC"}


def test_a_pair_that_appears_after_the_baseline_is_reported(tmp_path, monkeypatch) -> None:
    storage = _storage(tmp_path)
    watcher = ListingWatcher(CONFIG, storage)
    _serve(monkeypatch, _info(("BTCUSDC", "BTC", "USDC")))
    watcher.scan()

    _serve(monkeypatch, _info(("BTCUSDC", "BTC", "USDC"), ("NEWUSDC", "NEW", "USDC")))
    scan = watcher.scan()

    assert [item["symbol"] for item in scan.new_listings] == ["NEWUSDC"]
    assert scan.new_listings[0]["baseAsset"] == "NEW"
    assert scan.new_listings[0]["firstSeenAt"], "the moment this machine saw it is the point"


def test_the_same_pair_is_never_reported_twice(tmp_path, monkeypatch) -> None:
    storage = _storage(tmp_path)
    watcher = ListingWatcher(CONFIG, storage)
    _serve(monkeypatch, _info(("BTCUSDC", "BTC", "USDC")))
    watcher.scan()
    _serve(monkeypatch, _info(("BTCUSDC", "BTC", "USDC"), ("NEWUSDC", "NEW", "USDC")))
    watcher.scan()

    assert watcher.scan().new_listings == ()


def test_a_pair_that_is_not_trading_yet_is_ignored(tmp_path, monkeypatch) -> None:
    """PRE_TRADING and BREAK are not listings anyone can act on."""
    storage = _storage(tmp_path)
    watcher = ListingWatcher(CONFIG, storage)
    _serve(monkeypatch, _info(("BTCUSDC", "BTC", "USDC")))
    watcher.scan()

    _serve(
        monkeypatch,
        {
            "symbols": [
                {"symbol": "BTCUSDC", "baseAsset": "BTC", "quoteAsset": "USDC", "status": "TRADING"},
                {"symbol": "SOONUSDC", "baseAsset": "SOON", "quoteAsset": "USDC", "status": "PRE_TRADING"},
            ]
        },
    )

    assert watcher.scan().new_listings == ()


def test_only_quotes_someone_could_act_on_are_recorded(tmp_path, monkeypatch) -> None:
    """One listing against eight quotes is one listing, not eight."""
    storage = _storage(tmp_path)
    watcher = ListingWatcher(CONFIG, storage)
    _serve(monkeypatch, _info(("BTCUSDC", "BTC", "USDC")))
    watcher.scan()

    _serve(
        monkeypatch,
        _info(
            ("BTCUSDC", "BTC", "USDC"),
            ("NEWUSDC", "NEW", "USDC"),
            ("NEWTRY", "NEW", "TRY"),
            ("NEWEUR", "NEW", "EUR"),
        ),
    )
    scan = watcher.scan()

    assert [item["symbol"] for item in scan.new_listings] == ["NEWUSDC"]
    assert "TRY" not in INTERESTING_QUOTES


def test_an_exchange_outage_does_not_kill_the_watcher(tmp_path, monkeypatch) -> None:
    """A watcher that dies on one timeout stops watching, silently."""
    storage = _storage(tmp_path)
    watcher = ListingWatcher(CONFIG, storage)
    _serve(monkeypatch, _info(("BTCUSDC", "BTC", "USDC")))
    watcher.scan()

    _serve(monkeypatch, BinanceApiError("503 from Binance"))
    scan = watcher.scan()

    assert scan.ok is False
    assert "503" in scan.error
    assert scan.new_listings == ()
    # And the next successful pass still works.
    _serve(monkeypatch, _info(("BTCUSDC", "BTC", "USDC"), ("NEWUSDC", "NEW", "USDC")))
    assert [item["symbol"] for item in watcher.scan().new_listings] == ["NEWUSDC"]


def test_an_unexpected_error_is_survived_too(tmp_path, monkeypatch) -> None:
    _serve(monkeypatch, ValueError("malformed json"))

    scan = ListingWatcher(CONFIG, _storage(tmp_path)).scan()

    assert scan.ok is False
    assert scan.error == "ValueError"


def test_the_shown_listings_are_capped_because_run_retention_cannot_see_them(tmp_path, monkeypatch) -> None:
    """These rows have no run_id on purpose, so nothing else prunes them.

    The cap applies to what the page shows, never to the baseline - that
    distinction is the whole of the bug this file's later tests describe.
    """
    storage = _storage(tmp_path)
    watcher = ListingWatcher(CONFIG, storage, keep=5)
    existing = tuple((f"OLD{index}USDC", f"OLD{index}", "USDC") for index in range(3))
    _serve(monkeypatch, _info(*existing))
    watcher.scan()

    arrivals = tuple((f"NEW{index}USDC", f"NEW{index}", "USDC") for index in range(20))
    _serve(monkeypatch, _info(*existing, *arrivals))
    watcher.scan()

    assert len(storage.get_recent_listings(100)) == 5
    # The baseline keeps every pair, capped or not.
    assert len(storage.known_listing_symbols()) == 23


def test_the_newest_listings_are_the_ones_kept(tmp_path) -> None:
    storage = _storage(tmp_path)
    storage.record_listings(
        [
            {"symbol": "OLDUSDC", "baseAsset": "OLD", "quoteAsset": "USDC", "firstSeenAt": "2020-01-01 00:00:00"},
            {"symbol": "NEWUSDC", "baseAsset": "NEW", "quoteAsset": "USDC", "firstSeenAt": "2026-01-01 00:00:00"},
        ]
    )

    storage.prune_listing_events(1)

    assert [row["symbol"] for row in storage.get_recent_listings()] == ["NEWUSDC"]


def test_recording_the_same_symbol_twice_adds_it_once(tmp_path) -> None:
    storage = _storage(tmp_path)
    event = {"symbol": "NEWUSDC", "baseAsset": "NEW", "quoteAsset": "USDC", "firstSeenAt": "2026-01-01 00:00:00"}

    assert len(storage.record_listings([event])) == 1
    assert storage.record_listings([event]) == []


def test_a_listing_can_be_acknowledged(tmp_path) -> None:
    storage = _storage(tmp_path)
    storage.record_listings(
        [{"symbol": "NEWUSDC", "baseAsset": "NEW", "quoteAsset": "USDC", "firstSeenAt": "2026-01-01 00:00:00"}]
    )

    storage.acknowledge_listing("newusdc")

    assert storage.get_recent_listings()[0]["acknowledged"] is True


@pytest.mark.parametrize("quote", INTERESTING_QUOTES)
def test_every_interesting_quote_is_actually_recorded(tmp_path, monkeypatch, quote) -> None:
    """A quote in the list that the filter drops would be a silent gap."""
    storage = _storage(tmp_path)
    watcher = ListingWatcher(CONFIG, storage)
    _serve(monkeypatch, _info(("BTCUSDC", "BTC", "USDC")))
    watcher.scan()

    _serve(monkeypatch, _info(("BTCUSDC", "BTC", "USDC"), (f"NEW{quote}", "NEW", quote)))

    assert [item["symbol"] for item in watcher.scan().new_listings] == [f"NEW{quote}"]


def test_the_cap_does_not_make_pruned_pairs_look_new_again(tmp_path, monkeypatch) -> None:
    """The bug a tester found by asking what "watching 200 pairs" meant.

    The baseline used to be stored in the capped table, so the cap discarded
    most of it - and every discarded pair was reported as a new listing on the
    very next pass. Against a real exchange that was 400 false notifications,
    fifteen minutes after switching the watcher on.
    """
    storage = _storage(tmp_path)
    watcher = ListingWatcher(CONFIG, storage, keep=5)
    many = tuple((f"C{index}USDC", f"C{index}", "USDC") for index in range(50))
    _serve(monkeypatch, _info(*many))

    assert watcher.scan().new_listings == ()
    second = watcher.scan()

    assert second.new_listings == (), "pruned baseline pairs came back as new"
    assert second.total_known == 50, "the baseline must not be capped"


def test_only_genuinely_new_pairs_reach_the_page(tmp_path, monkeypatch) -> None:
    """The page reads listing_events; the baseline must never land there."""
    storage = _storage(tmp_path)
    watcher = ListingWatcher(CONFIG, storage, keep=200)
    existing = tuple((f"C{index}USDC", f"C{index}", "USDC") for index in range(30))
    _serve(monkeypatch, _info(*existing))
    watcher.scan()

    assert storage.get_recent_listings() == [], "the baseline was shown as listings"

    _serve(monkeypatch, _info(*existing, ("GENUINEUSDC", "GENUINE", "USDC")))
    watcher.scan()

    rows = storage.get_recent_listings()
    assert [row["symbol"] for row in rows] == ["GENUINEUSDC"]


def test_the_watched_count_is_the_whole_exchange_not_the_cap(tmp_path, monkeypatch) -> None:
    """"Watching 200 pairs" was the cap talking, not the exchange."""
    storage = _storage(tmp_path)
    watcher = ListingWatcher(CONFIG, storage, keep=5)
    _serve(monkeypatch, _info(*((f"C{i}USDC", f"C{i}", "USDC") for i in range(40))))

    assert watcher.scan().total_known == 40


def test_a_baseline_written_by_an_earlier_build_is_cleared_once(tmp_path) -> None:
    """Before listing_symbols existed the baseline went into the display table.

    Those rows are not listings; they are hundreds of pairs listed years ago,
    shown on the New listings page as if they had just appeared.
    """
    path = tmp_path / "journal.sqlite3"
    first = Storage(path)
    first.record_listings(
        [
            {"symbol": f"OLD{i}USDC", "baseAsset": f"OLD{i}", "quoteAsset": "USDC",
             "firstSeenAt": "2026-08-01 19:32:53"}
            for i in range(200)
        ]
    )
    # Undo the flag the constructor set, to stand in for a journal written
    # before this repair existed.
    first.connection.execute("delete from schema_flags")
    first.connection.commit()
    first.connection.close()

    repaired = Storage(path)

    assert repaired.get_recent_listings(500) == []


def test_the_repair_does_not_run_a_second_time(tmp_path) -> None:
    """A genuine listing recorded after the repair must survive a restart."""
    path = tmp_path / "journal.sqlite3"
    Storage(path).record_listings(
        [{"symbol": "GENUINEUSDC", "baseAsset": "GENUINE", "quoteAsset": "USDC",
          "firstSeenAt": "2026-08-02 10:00:00"}]
    )

    reopened = Storage(path)

    assert [row["symbol"] for row in reopened.get_recent_listings()] == ["GENUINEUSDC"]


def test_the_repair_leaves_the_detection_baseline_alone(tmp_path) -> None:
    """Clearing what is shown must not make every pair look new again."""
    path = tmp_path / "journal.sqlite3"
    first = Storage(path)
    first.remember_listing_symbols([(f"C{i}USDC", "2026-08-01 20:00:00") for i in range(50)])
    first.connection.execute("delete from schema_flags")
    first.connection.commit()
    first.connection.close()

    repaired = Storage(path)

    assert len(repaired.known_listing_symbols()) == 50
