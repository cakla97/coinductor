from pathlib import Path

from trading_agent.storage import Storage, run_scoped_tables


def _storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "journal.sqlite3")


def test_every_run_scoped_table_is_indexed_on_run_id(tmp_path: Path) -> None:
    storage = _storage(tmp_path)

    indexes = {
        str(row["name"])
        for row in storage.connection.execute(
            "select name from sqlite_master where type = 'index'"
        )
    }

    for table in run_scoped_tables(storage.connection):
        assert f"idx_{table}_run_id" in indexes, f"{table} is missing its run_id index"


def test_order_tables_are_indexed_on_intent_id(tmp_path: Path) -> None:
    storage = _storage(tmp_path)

    indexes = {
        str(row["name"])
        for row in storage.connection.execute(
            "select name from sqlite_master where type = 'index'"
        )
    }

    for table in ("paper_orders", "testnet_orders", "live_orders", "oco_protection_orders"):
        assert f"idx_{table}_intent_id" in indexes


def test_journal_uses_wal_so_the_desktop_can_read_during_a_run(tmp_path: Path) -> None:
    storage = _storage(tmp_path)

    mode = storage.connection.execute("pragma journal_mode").fetchone()[0]

    assert str(mode).lower() == "wal"


def test_retention_prunes_old_run_rows(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    for _ in range(4):
        run_id = storage.start_run("MOCK")
        storage.connection.execute(
            "insert into balances(run_id, asset, spot_free) values (?, 'BTC', '1')", (run_id,)
        )
    storage.connection.commit()

    removed = storage.cleanup_old_runs(keep_last=2)

    assert removed == 2
    assert storage.connection.execute("select count(*) from runs").fetchone()[0] == 2
    assert storage.connection.execute("select count(*) from balances").fetchone()[0] == 2


def test_retention_never_prunes_the_tables_that_guard_against_double_submits(tmp_path: Path) -> None:
    """Intent ids must outlive run retention or a filled order could be re-sent."""
    storage = _storage(tmp_path)
    first_run = storage.start_run("MOCK")
    storage.connection.execute(
        "insert into first_portfolio_tranches(run_id, mode, intent_id, submitted, status) "
        "values (?, 'LIVE', 'tranche-1', 1, 'FILLED')",
        (first_run,),
    )
    storage.connection.execute(
        "insert into oco_protection_orders(run_id, intent_id, submitted, status) "
        "values (?, 'oco-1', 1, 'FILLED')",
        (first_run,),
    )
    storage.connection.commit()
    for _ in range(3):
        storage.start_run("MOCK")

    storage.cleanup_old_runs(keep_last=1)

    assert storage.get_existing_first_portfolio_intents("LIVE") == {"tranche-1"}
    assert storage.get_existing_oco_intents() == {"oco-1"}
