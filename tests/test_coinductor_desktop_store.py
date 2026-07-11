import sqlite3

from coinductor.desktop_store import DesktopStore


def test_desktop_store_prefers_latest_real_run_over_newer_mock(tmp_path) -> None:
    database = tmp_path / "agent.sqlite3"
    report = tmp_path / "real_run.md"
    report.write_text(
        """# Trading Agent Report

## Recommended Actions

1. **LOW** - Review portfolio.
   Reason: Test action.

## AI Commentary

- Summary: Test summary.

## Executive Summary

- Total portfolio value: `500.00 USDC`
- Liquid value: `100.00 USDC`
- Locked value: `400.00 USDC`

## Strategy Decision

- Decision: `HOLD`
- Summary: Real run selected.

## Risk Decision

- Approved: `True`
- Reason: Within limits.
""",
        encoding="utf-8",
    )
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        create table runs (id integer primary key, started_at text, mode text, status text, summary text);
        create table market_research_reports (run_id integer, status text);
        create table portfolio_valuations (
            run_id integer, asset text, role text, total_value_usdt text, allocation_pct text,
            spot_value_usdt text, flexible_value_usdt text, locked_value_usdt text,
            rebalance_action text
        );
        create table grid_recommendations (
            run_id integer, symbol text, market_status text, deployment_allowed integer,
            score text, investment_usdt text, reason text, range_low text, range_high text,
            grid_count integer, stop_loss_price text, take_profit_price text,
            estimated_grid_spacing_pct text, blockers text
        );
        create table rebalancing_bot_recommendations (
            run_id integer, deployment_allowed integer, mode text, threshold_pct text,
            investment_usdt text, summary text, blockers text
        );
        create table rebalancing_bot_assets (
            run_id integer, asset text, target_weight_pct text, status text
        );
        create table ai_proposals (
            run_id integer, symbol text, action text, confidence text, quote_amount_usdt text, reason text
        );
        create table strategy_decisions (
            run_id integer, decision_type text, summary text
        );
        """
    )
    connection.execute(
        "insert into runs values (1, '2026-06-25T10:00:00', 'DRY_RUN', 'OK', ?)",
        (f"Report written to {report}",),
    )
    connection.execute(
        "insert into runs values (2, '2026-06-25T11:00:00', 'DRY_RUN', 'OK', 'Mock run')"
    )
    connection.executemany(
        "insert into market_research_reports values (?, ?)",
        [(1, "OK"), (2, "MOCK")],
    )
    connection.execute(
        "insert into portfolio_valuations values (1, 'BTC', 'PROTECTED', '500', '100', '0', '500', '0', 'HOLD')"
    )
    connection.execute(
        "insert into grid_recommendations values (1, 'BTCUSDC', 'WATCH', 0, '40', '25', 'Wait for range conditions.', '90000', '110000', 40, '85000', '115000', '0.5', 'Market status is WATCH.')"
    )
    connection.execute(
        "insert into rebalancing_bot_recommendations values (1, 0, 'BY_RATIO', '10', '200', 'Funding gap remains.', 'Funding gap.')"
    )
    connection.executemany(
        "insert into strategy_decisions values (?, ?, ?)",
        [(1, "HOLD", "Real run selected."), (2, "BUY", "Mock only.")],
    )
    connection.executemany(
        "insert into rebalancing_bot_assets values (?, ?, ?, ?)",
        [(1, "BTC", "60", "INCLUDED"), (1, "ETH", "40", "INCLUDED")],
    )
    connection.execute(
        "insert into ai_proposals values (1, 'BTCUSDC', 'HOLD', '0.7', '15', 'Wait.')"
    )
    connection.commit()
    connection.close()

    snapshot = DesktopStore(database, tmp_path).load()

    assert snapshot.latest_run is not None
    assert snapshot.latest_run.run_id == 1
    assert snapshot.portfolio_assets[0]["asset"] == "BTC"
    assert snapshot.latest_run.trade_proposal["symbol"] == "BTCUSDC"
    assert snapshot.strategies[0]["type"] == "Spot Grid"
    assert snapshot.strategies[0]["allowed"] == "Watched"
    assert snapshot.strategies[0]["parameters"][1]["value"] == "90000 - 110000"
    assert snapshot.strategies[1]["allowed"] == "Blocked"
    assert snapshot.strategies[1]["parameters"][2]["label"] == "Trigger"
    assert snapshot.strategies[1]["parameters"][2]["value"] == "By ratio 10.00%"
    assert "BTC 60.00%" in snapshot.strategies[1]["parameters"][3]["value"]
    assert snapshot.run_history[0]["dataMode"] == "MOCK"
    assert snapshot.run_history[1]["dataMode"] == "REAL"
