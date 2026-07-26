"""End-to-end characterisation of a full agent run.

AgentRunner.run() is the orchestrator every other module hangs off, and mock mode
exercises it without touching the network. These tests pin what a run produces so
the phase split inside run() stays behaviour-preserving.
"""

from dataclasses import replace
from pathlib import Path

import pytest

from trading_agent.config import AppConfig, load_config
from trading_agent.runner import AgentRunner

_ROOT = Path(__file__).resolve().parent.parent

# Every table a successful mock run is expected to write at least one row into.
_EXPECTED_TABLES = (
    "balances",
    "portfolio_valuations",
    "portfolio_summaries",
    "market_snapshots",
    "ai_proposals",
    "risk_decisions",
    "live_risk_states",
    "paper_orders",
    "grid_recommendations",
    "strategy_decisions",
    "next_run_recommendations",
    "recommended_actions",
    "execution_checklist_items",
    "ai_commentaries",
    "trading_bankroll_reports",
)


@pytest.fixture
def mock_config(tmp_path: Path) -> AppConfig:
    config = load_config(_ROOT / "config.example.toml")
    raw = dict(config.raw)
    raw["app"] = {**raw["app"], "mock_data": True}
    raw["app"]["database_path"] = str(tmp_path / "journal.sqlite3")
    raw["app"]["reports_dir"] = str(tmp_path / "reports")
    return replace(config, raw=raw)


def test_a_mock_run_completes_and_writes_a_report(mock_config: AppConfig) -> None:
    result = AgentRunner(mock_config).run()

    assert result.status == "OK"
    assert result.run_id == 1
    report = Path(result.report_path)
    assert report.exists()
    assert report.read_text(encoding="utf-8").strip()


def test_a_mock_run_populates_every_journal_table(mock_config: AppConfig) -> None:
    runner = AgentRunner(mock_config)

    runner.run()

    for table in _EXPECTED_TABLES:
        count = runner.storage.connection.execute(f"select count(*) from {table}").fetchone()[0]
        assert count > 0, f"{table} received no rows"


def test_the_run_is_recorded_as_finished(mock_config: AppConfig) -> None:
    runner = AgentRunner(mock_config)

    result = runner.run()

    row = runner.storage.connection.execute(
        "select status, summary from runs where id = ?", (result.run_id,)
    ).fetchone()
    assert row["status"] == "OK"
    assert "Report written to" in row["summary"]


def test_consecutive_runs_stay_independent(mock_config: AppConfig) -> None:
    first = AgentRunner(mock_config).run()
    second = AgentRunner(mock_config).run()

    assert (first.run_id, second.run_id) == (1, 2)
    assert first.report_path != second.report_path


def test_a_failing_step_marks_the_run_as_errored(mock_config: AppConfig) -> None:
    runner = AgentRunner(mock_config)
    runner.client.get_balances = lambda: (_ for _ in ()).throw(RuntimeError("binance is down"))

    with pytest.raises(RuntimeError, match="binance is down"):
        runner.run()

    row = runner.storage.connection.execute("select status, summary from runs order by id desc limit 1").fetchone()
    assert row["status"] == "ERROR"
    assert "binance is down" in row["summary"]
