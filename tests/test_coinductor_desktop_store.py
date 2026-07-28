from datetime import datetime, timedelta, timezone, UTC
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
        create table market_snapshots (
            run_id integer, symbol text, price text
        );
        create table oco_protection_orders (
            run_id integer, intent_id text, symbol text, side text, status text,
            quantity text, adjusted_quantity text, available_base text,
            take_profit_price text, stop_loss_stop_price text,
            estimated_take_profit_quote text, estimated_stop_quote text,
            submitted integer, order_list_id text, confirmation_required text,
            reason text, message text
        );
        create table live_orders (
            run_id integer, status text, submitted integer
        );
        create table next_run_recommendations (
            run_id integer, run_again_in_hours integer, urgency text,
            reason text, triggers text
        );
        create table earn_redeem_plans (
            run_id integer, intent_id text, enabled integer, asset text, amount text,
            status text, product_id text, redeem_type text, can_redeem integer,
            submitted integer, confirmation_required text, message text
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
    connection.executemany(
        "insert into market_snapshots values (?, ?, ?)",
        [(1, "BTCUSDC", "100000"), (1, "ETHUSDC", "3000"), (2, "BTCUSDC", "999999")],
    )
    connection.execute(
        "insert into oco_protection_orders values (1, 'oco-live-1', 'BTCUSDC', 'SELL', 'READY', '0.001', '0.001', '0.001', '110000', '90000', '110', '90', 0, '', 'CONFIRM_MAINNET_OCO', 'SELL OCO protection preview is valid.', '')"
    )
    connection.execute("insert into live_orders values (1, 'PREVIEW_READY', 0)")
    connection.execute(
        "insert into earn_redeem_plans values "
        "(1, 'earn-live-1', 1, 'USDC', '25.00', 'PREVIEW_READY', 'prod-1', 'FAST', 1, 0, 'CONFIRM_EARN_REDEEM', 'Flexible Earn redeem is ready but was not submitted.')"
    )
    connection.execute(
        "insert into next_run_recommendations values (1, 24, 'NORMAL', ?, ?)",
        (
            "No action was recommended in this run.",
            "Run sooner after a large BTC move.\nRun sooner after changing the portfolio.",
        ),
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
    assert snapshot.strategies[0]["registrationSuggestion"]["rangeLow"] == "90000"
    assert snapshot.strategies[0]["registrationSuggestion"]["entryPrice"] == "100000"
    assert snapshot.strategies[0]["registrationSuggestion"]["takeProfit"] == "115000"
    assert snapshot.strategies[1]["allowed"] == "Blocked"
    assert snapshot.strategies[1]["parameters"][2]["label"] == "Trigger"
    assert snapshot.strategies[1]["parameters"][2]["value"] == "By ratio 10.00%"
    assert "BTC 60.00%" in snapshot.strategies[1]["parameters"][3]["value"]
    assert snapshot.strategies[1]["registrationSuggestion"]["assets"] == "BTC, ETH"
    assert snapshot.strategies[1]["registrationSuggestion"]["targetWeights"] == "60, 40"
    assert snapshot.strategies[1]["registrationSuggestion"]["entryPrices"] == "100000, 3000"
    assert snapshot.position_protection is not None
    assert snapshot.position_protection["status"] == "Ready"
    assert snapshot.position_protection["canSubmitOco"] is True
    assert snapshot.position_protection["parameters"][2]["value"] == "110000"
    assert snapshot.has_ready_live_preview is True
    assert snapshot.next_review is not None
    assert snapshot.next_review["status"] == "Manual step before rerun"
    assert snapshot.next_review["tone"] == "blocked"
    assert snapshot.next_review["timing"] == "After the manual step"
    assert isinstance(snapshot.next_review["triggers"], list)
    assert isinstance(snapshot.next_review["manualSteps"], list)
    assert "Rebalancing: Funding gap." in snapshot.next_review["manualSteps"]
    assert "Spot Grid: Market status is WATCH." in snapshot.next_review["triggers"]
    assert snapshot.next_review["sourceRun"] == "1"
    assert snapshot.run_history[0]["dataMode"] == "MOCK"
    assert snapshot.run_history[1]["dataMode"] == "REAL"
    assert snapshot.earn_redeem is not None
    assert snapshot.earn_redeem["status"] == "Ready"
    assert snapshot.earn_redeem["canSubmitEarnRedeem"] is True
    assert snapshot.earn_redeem["parameters"][0]["value"] == "USDC"
    assert snapshot.earn_redeem["parameters"][1]["value"] == "25.00 USDC"
    assert snapshot.earn_redeem["confirmationRequired"] == "CONFIRM_EARN_REDEEM"


def test_earn_redeem_not_needed_is_hidden_from_the_snapshot(tmp_path) -> None:
    database = tmp_path / "agent.sqlite3"
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        create table earn_redeem_plans (
            run_id integer, intent_id text, enabled integer, asset text, amount text,
            status text, product_id text, redeem_type text, can_redeem integer,
            submitted integer, confirmation_required text, message text
        );
        """
    )
    connection.execute(
        "insert into earn_redeem_plans values "
        "(1, '', 0, null, '0.00', 'NOT_NEEDED', '', '', 0, 0, 'CONFIRM_EARN_REDEEM', 'No Flexible Earn redeem is needed for this run.')"
    )
    connection.commit()

    result = DesktopStore(database, tmp_path)._earn_redeem(connection, 1)

    assert result is None
    connection.close()


def test_next_review_waits_for_market_conditions_without_manual_blocker(tmp_path) -> None:
    database = tmp_path / "agent.sqlite3"
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        create table next_run_recommendations (
            run_id integer, run_again_in_hours integer, urgency text,
            reason text, triggers text
        )
        """
    )
    connection.execute(
        "insert into next_run_recommendations values (7, 24, 'NORMAL', ?, ?)",
        ("No immediate action is needed.", "Run sooner after a material price move."),
    )
    strategies = (
        {
            "type": "Spot Grid",
            "parameters": (),
            "blockers": ("Market status is WATCH.",),
        },
    )

    review = DesktopStore(database, tmp_path)._next_review(
        connection,
        7,
        datetime.now(UTC).isoformat(),
        strategies,
    )
    connection.close()

    assert review is not None
    assert review["status"] == "Check again in 24 hours"
    assert review["timing"] == "In 24 hours"
    assert review["manualSteps"] == []
    assert "Spot Grid: Market status is WATCH." in review["triggers"]


def test_scheduled_review_uses_stable_numeric_utc_offset(tmp_path) -> None:
    store = DesktopStore(tmp_path / "agent.sqlite3", tmp_path)
    value = datetime(2026, 7, 14, 22, 43, tzinfo=timezone(timedelta(hours=2)))

    formatted = store._format_scheduled_review(value)
    local_value = value.astimezone()
    compact_offset = local_value.strftime("%z")
    expected_offset = f"UTC{compact_offset[:3]}:{compact_offset[3:]}"

    assert formatted == f"{local_value:%Y-%m-%d %H:%M} {expected_offset}"
    assert formatted.isascii()


def test_desktop_store_builds_protected_and_closed_live_lifecycle(tmp_path) -> None:
    database = tmp_path / "agent.sqlite3"
    report = tmp_path / "live_run.md"
    report.write_text(
        """# Trading Agent Report

## Executive Summary

- Total portfolio value: `500.00 USDC`
- Liquid value: `100.00 USDC`
- Locked value: `400.00 USDC`

## Strategy Decision

- Decision: `HOLD`
- Summary: Existing position is monitored.

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
        create table strategy_decisions (run_id integer, decision_type text, summary text);
        create table market_snapshots (
            run_id integer, symbol text, price text, rsi14 text, ema20 text, ema50 text,
            ema200 text, atr14 text, trend_regime text
        );
        create table live_orders (
            run_id integer, intent_id text, symbol text, side text, order_type text,
            quote_amount_usdt text, quote_asset text, status text, submitted integer,
            order_id text, executed_quantity text, cumulative_quote_qty text,
            validation_summary text, message text
        );
        create table oco_protection_orders (
            run_id integer, intent_id text, symbol text, side text, status text,
            quantity text, adjusted_quantity text, available_base text,
            take_profit_price text, stop_loss_stop_price text,
            estimated_take_profit_quote text, estimated_stop_quote text,
            submitted integer, order_list_id text, confirmation_required text,
            reason text, message text
        );
        create table oco_status_checks (
            run_id integer, intent_id text, symbol text, order_list_id text,
            list_order_status text, list_status_type text, filled_order_id text,
            filled_quantity text, filled_quote text, reconciled integer, message text
        );
        """
    )
    connection.executemany(
        "insert into runs values (?, ?, 'REAL', 'OK', ?)",
        [
            (1, "2026-07-10T10:00:00+00:00", f"Report written to {report}"),
            (2, "2026-07-10T10:05:00+00:00", "OCO synchronized"),
        ],
    )
    connection.executemany("insert into market_research_reports values (?, 'OK')", [(1,), (2,)])
    connection.executemany(
        "insert into strategy_decisions values (?, 'HOLD', 'Existing position is monitored.')",
        [(1,), (2,)],
    )
    connection.execute(
        "insert into market_snapshots values (2, 'BTCUSDC', '110000', '50', '0', '0', '0', '0', 'RANGE')"
    )
    connection.execute(
        "insert into live_orders values (1, 'buy-live-1', 'BTCUSDC', 'BUY', 'MARKET', '100', 'USDC', 'FILLED', 1, 'buy-123', '0.001', '100', 'valid', 'filled')"
    )
    connection.execute(
        "insert into oco_protection_orders values (1, 'oco-buy-live-1', 'BTCUSDC', 'SELL', 'PROTECTED', '0.001', '0.001', '0.001', '115000', '95000', '115', '95', 1, 'oco-456', 'CONFIRM_MAINNET_OCO', 'valid', 'submitted')"
    )
    connection.execute(
        "insert into oco_status_checks values (2, 'oco-buy-live-1', 'BTCUSDC', 'oco-456', 'EXECUTING', 'EXEC_STARTED', '', '0', '0', 0, 'active')"
    )
    connection.commit()
    connection.close()

    protected = DesktopStore(database, tmp_path).load().live_action_lifecycle

    assert protected is not None
    assert protected["status"] == "Protected"
    assert protected["parameters"][1]["value"] == "buy-123"
    assert protected["parameters"][5]["value"] == "+10.0000 USDC (+10.00%)"
    assert protected["lifecycleSteps"][2]["status"] == "Done"
    assert protected["lifecycleSteps"][3]["status"] == "Pending"

    connection = sqlite3.connect(database)
    connection.execute(
        "insert into runs values (3, '2026-07-10T11:00:00+00:00', 'REAL', 'OK', 'OCO sell reconciled')"
    )
    connection.execute("insert into market_research_reports values (3, 'OK')")
    connection.execute("insert into strategy_decisions values (3, 'HOLD', 'Position closed.')")
    connection.execute(
        "insert into live_orders values (3, 'sell-buy-live-1', 'BTCUSDC', 'SELL', 'OCO', '0', 'USDC', 'FILLED', 1, 'sell-789', '0.001', '112', 'reconciled', 'closed')"
    )
    connection.commit()
    connection.close()

    closed = DesktopStore(database, tmp_path).load().live_action_lifecycle

    assert closed is not None
    assert closed["status"] == "Closed"
    assert closed["parameters"][4]["value"] == "112000"
    assert closed["parameters"][5]["value"] == "+12.0000 USDC (+12.00%)"
    assert closed["lifecycleSteps"][3]["status"] == "Done"
    assert "sell-789" in closed["lifecycleSteps"][3]["detail"]


def test_desktop_store_maps_active_strategy_health(tmp_path) -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        create table active_grid_evaluations (
            run_id integer, name text, symbol text, range_low text, range_high text,
            investment_usdt text, current_price text, state text,
            distance_to_lower_pct text, distance_to_upper_pct text, recommendation text,
            binance_bot_id text, grid_count integer, grid_type text, entry_price text,
            stop_loss_price text, take_profit_price text, age_days text
        );
        create table active_rebalancing_evaluations (
            run_id integer, name text, binance_bot_id text, assets text,
            target_weights_pct text, current_weights_pct text, entry_prices_usdt text,
            investment_usdt text, threshold_pct text, max_drift_pct text,
            state text, age_days text, recommendation text
        );
        """
    )
    connection.execute(
        "insert into active_grid_evaluations values (1, 'btc-grid', 'BTCUSDC', '90000', '115000', '250', '103000', 'IN_RANGE', '14.44', '10.43', 'Continue monitoring.', 'grid-123', 20, 'ARITHMETIC', '100000', '88000', '118000', '3.5')"
    )
    connection.execute(
        "insert into active_rebalancing_evaluations values (1, 'core-basket', 'reb-456', 'BTC\nETH', '60\n40', '52\n48', '100000\n3000', '300', '5', '8', 'THRESHOLD_REACHED', '7', 'Verify Binance rebalance activity.')"
    )

    items, summary = DesktopStore(tmp_path / "unused.sqlite3", tmp_path)._active_strategies(connection, 1)

    assert len(items) == 2
    assert items[0]["type"] == "Spot Grid"
    assert items[0]["health"] == "Healthy"
    assert items[0]["parameters"][4]["value"] == "20 / ARITHMETIC"
    assert items[1]["type"] == "Rebalancing"
    assert items[1]["health"] == "Action required"
    assert items[1]["parameters"][1]["value"] == "BTC 60.00%, ETH 40.00%"
    assert summary == "2 active strategy(s): 1 healthy, 0 to review, 1 requiring action."
    connection.close()
