"""DesktopStore must keep reading the schema Storage actually writes.

The other DesktopStore tests hand-build a cut-down schema, so a column renamed in
Storage._migrate would slip past them: the reader degrades to `null as <column>`
and the UI quietly shows blanks. These tests point the reader at a journal
produced by a genuine AgentRunner run instead, which is the only way that drift
shows up as a failure.
"""

from dataclasses import replace
from pathlib import Path
import sqlite3

import pytest

from coinductor.desktop_store import DesktopStore
from trading_agent.config import load_config
from trading_agent.runner import AgentRunner
from trading_agent.storage import column_or_null, table_columns, table_exists

_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def journal(tmp_path: Path) -> tuple[Path, Path]:
    """A real run's journal, relabelled so the desktop treats it as live data."""
    config = load_config(_ROOT / "config.example.toml")
    raw = dict(config.raw)
    raw["app"] = {**raw["app"], "mock_data": True}
    database = tmp_path / "journal.sqlite3"
    reports = tmp_path / "reports"
    raw["app"]["database_path"] = str(database)
    raw["app"]["reports_dir"] = str(reports)

    runner = AgentRunner(replace(config, raw=raw))
    runner.run()
    # _latest_real_run ignores runs whose market research is MOCK, so flip it.
    runner.storage.connection.execute("update market_research_reports set status = 'OK'")
    runner.storage.connection.commit()
    return database, reports


def test_the_desktop_can_read_a_journal_written_by_a_real_run(journal) -> None:
    database, reports = journal

    snapshot = DesktopStore(database, reports).load()

    assert snapshot.latest_run is not None
    assert snapshot.portfolio_assets, "no portfolio rows reached the desktop"
    assert snapshot.run_history, "no run history reached the desktop"


def test_portfolio_rows_are_fully_populated_rather_than_silently_blank(journal) -> None:
    database, reports = journal

    snapshot = DesktopStore(database, reports).load()

    for row in snapshot.portfolio_assets:
        assert row["asset"], "asset column did not survive the read"
        assert row["value"], f"{row['asset']} has no value: a column may have been renamed"
        assert row["allocation"], f"{row['asset']} has no allocation"


def test_every_column_the_reader_falls_back_on_exists_in_a_current_journal(journal) -> None:
    """The null-fallbacks are for old journals; none should trigger on a fresh one."""
    database, _ = journal
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        expectations = {
            "grid_recommendations": (
                "range_low",
                "range_high",
                "grid_count",
                "stop_loss_price",
                "take_profit_price",
                "estimated_grid_spacing_pct",
                "blockers",
            ),
            "active_grid_evaluations": (
                "binance_bot_id",
                "grid_count",
                "grid_type",
                "entry_price",
                "stop_loss_price",
                "take_profit_price",
                "age_days",
            ),
            "oco_status_checks": ("run_id",),
        }
        for table, columns in expectations.items():
            assert table_exists(connection, table), f"{table} is missing from the schema"
            present = table_columns(connection, table)
            for column in columns:
                assert column_or_null(present, column) == column, (
                    f"{table}.{column} no longer exists, so the desktop would read NULL"
                )
    finally:
        connection.close()
