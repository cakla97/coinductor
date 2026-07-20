from decimal import Decimal

from trading_agent.models import LiveRiskState, MarketSnapshot, TradeProposal
from trading_agent.risk_engine import RiskEngine
from trading_agent.storage import Storage


def _config() -> dict:
    return {
        "risk": {
            "max_trades_per_day": 1,
            "max_daily_loss_pct": 1,
            "max_weekly_loss_pct": 3,
            "min_ai_confidence": 0.65,
            "cooldown_after_loss_hours": 24,
            "max_consecutive_losses": 2,
            "kill_switch_enabled": True,
        },
        "trading_bankroll": {"initial_seed_usdc": 12},
        "strategy": {"allowed_symbols": ["BTCUSDC", "ETHUSDC"]},
        "consensus": {
            "enabled": True,
            "require_risk_on": True,
            "require_price_above_ema200": True,
            "min_rsi14": 45,
            "max_rsi14": 68,
            "require_rising_volume": False,
        },
        "orders": {"require_stop_loss": True},
        "earn": {"max_redeem_per_run_usdt": 50},
    }


def _insert_live_order(
    storage: Storage,
    run_id: int,
    intent_id: str,
    side: str,
    quantity: str,
    quote: str,
) -> None:
    storage.connection.execute(
        """
        insert into live_orders (
            run_id, intent_id, symbol, side, order_type, quote_amount_usdt, quote_asset,
            status, submitted, order_id, executed_quantity, cumulative_quote_qty,
            validation_summary, message
        ) values (?, ?, 'BTCUSDC', ?, 'MARKET', '10', 'USDC', 'FILLED', 1, ?, ?, ?, '', '')
        """,
        (run_id, intent_id, side, f"{side.lower()}-{run_id}", quantity, quote),
    )
    storage.connection.commit()


def _risk_on_snapshot() -> MarketSnapshot:
    return MarketSnapshot(
        symbol="BTCUSDC",
        price=Decimal("100"),
        ema20=Decimal("98"),
        ema50=Decimal("95"),
        ema200=Decimal("90"),
        rsi14=Decimal("55"),
        atr14=Decimal("3"),
        volume_trend="falling",
        trend_regime="RISK_ON",
    )


def _buy_proposal() -> TradeProposal:
    return TradeProposal(
        symbol="BTCUSDC",
        action="BUY",
        confidence=Decimal("0.8"),
        quote_amount_usdt=Decimal("10"),
        stop_loss_pct=Decimal("1.5"),
        take_profit_pct=Decimal("3"),
        reason="Test.",
    )


def test_realized_loss_uses_sell_day_and_partial_cost_basis(tmp_path) -> None:
    storage = Storage(tmp_path / "agent.sqlite3")
    buy_run = storage.start_run("LIVE")
    _insert_live_order(storage, buy_run, "cycle-1", "BUY", "0.00015", "9.69161250")
    storage.finish_run(buy_run, "OK", "buy")
    sell_run = storage.start_run("LIVE")
    _insert_live_order(storage, sell_run, "sell-cycle-1", "SELL", "0.00014", "8.909712")
    storage.finish_run(sell_run, "OK", "sell")
    current_run = storage.start_run("DRY_RUN")

    state = storage.get_live_risk_state(current_run, _config())

    assert state.daily_realized_pnl_quote.quantize(Decimal("0.000001")) == Decimal("-0.135793")
    assert state.daily_loss_pct.quantize(Decimal("0.0001")) == Decimal("1.1316")
    assert state.weekly_loss_pct.quantize(Decimal("0.0001")) == Decimal("1.1316")
    assert state.trades_today == 1
    assert state.consecutive_losses == 1
    assert state.cooldown_active is True
    assert state.daily_limit_reached is True
    assert state.kill_switch_active is True


def test_daily_limit_resets_but_weekly_history_remains(tmp_path) -> None:
    storage = Storage(tmp_path / "agent.sqlite3")
    buy_run = storage.start_run("LIVE")
    _insert_live_order(storage, buy_run, "cycle-1", "BUY", "1", "10")
    storage.finish_run(buy_run, "OK", "buy")
    sell_run = storage.start_run("LIVE")
    _insert_live_order(storage, sell_run, "sell-cycle-1", "SELL", "1", "9.8")
    storage.connection.execute(
        "update runs set started_at = datetime('now', '-1 day') where id in (?, ?)",
        (buy_run, sell_run),
    )
    storage.finish_run(sell_run, "OK", "sell")
    current_run = storage.start_run("DRY_RUN")

    state = storage.get_live_risk_state(current_run, _config())

    assert state.daily_realized_pnl_quote == 0
    assert state.daily_loss_pct == 0
    assert state.weekly_realized_pnl_quote == Decimal("-0.2")
    assert state.weekly_loss_pct.quantize(Decimal("0.0001")) == Decimal("1.6667")
    assert state.cooldown_active is False
    assert state.kill_switch_active is False


def test_risk_engine_blocks_kill_switch_before_trade() -> None:
    state = LiveRiskState(
        enabled=True,
        loss_basis_quote=Decimal("12"),
        trades_today=0,
        daily_realized_pnl_quote=Decimal("-0.2"),
        weekly_realized_pnl_quote=Decimal("-0.2"),
        daily_loss_pct=Decimal("1.6667"),
        weekly_loss_pct=Decimal("1.6667"),
        consecutive_losses=1,
        last_loss_at="2026-06-23 10:00:00",
        hours_since_last_loss=Decimal("2"),
        cooldown_active=True,
        daily_limit_reached=True,
        weekly_limit_reached=False,
        consecutive_loss_limit_reached=False,
        kill_switch_active=True,
        summary="blocked",
    )

    decision = RiskEngine(_config()).evaluate(_buy_proposal(), state, [_risk_on_snapshot()])

    assert decision.approved is False
    assert "kill switch" in decision.reason


def test_consensus_rejects_buy_outside_risk_on() -> None:
    state = LiveRiskState(
        enabled=True,
        loss_basis_quote=Decimal("12"),
        trades_today=0,
        daily_realized_pnl_quote=Decimal("0"),
        weekly_realized_pnl_quote=Decimal("0"),
        daily_loss_pct=Decimal("0"),
        weekly_loss_pct=Decimal("0"),
        consecutive_losses=0,
        last_loss_at=None,
        hours_since_last_loss=None,
        cooldown_active=False,
        daily_limit_reached=False,
        weekly_limit_reached=False,
        consecutive_loss_limit_reached=False,
        kill_switch_active=False,
        summary="clear",
    )
    snapshot = _risk_on_snapshot()
    snapshot = MarketSnapshot(
        symbol=snapshot.symbol,
        price=snapshot.price,
        ema20=snapshot.ema20,
        ema50=snapshot.ema50,
        ema200=snapshot.ema200,
        rsi14=snapshot.rsi14,
        atr14=snapshot.atr14,
        volume_trend=snapshot.volume_trend,
        trend_regime="RISK_OFF",
    )

    decision = RiskEngine(_config()).evaluate(_buy_proposal(), state, [snapshot])

    assert decision.approved is False
    assert "Consensus gate" in decision.reason


def test_skip_consensus_lets_a_risk_off_proposal_through() -> None:
    # First-portfolio basket deployment intentionally skips market-timing checks
    # (it is establishing a pre-approved template, not chasing a trade setup).
    state = LiveRiskState(
        enabled=True,
        loss_basis_quote=Decimal("12"),
        trades_today=0,
        daily_realized_pnl_quote=Decimal("0"),
        weekly_realized_pnl_quote=Decimal("0"),
        daily_loss_pct=Decimal("0"),
        weekly_loss_pct=Decimal("0"),
        consecutive_losses=0,
        last_loss_at=None,
        hours_since_last_loss=None,
        cooldown_active=False,
        daily_limit_reached=False,
        weekly_limit_reached=False,
        consecutive_loss_limit_reached=False,
        kill_switch_active=False,
        summary="clear",
    )
    snapshot = _risk_on_snapshot()
    risk_off_snapshot = MarketSnapshot(
        symbol=snapshot.symbol,
        price=snapshot.price,
        ema20=snapshot.ema20,
        ema50=snapshot.ema50,
        ema200=snapshot.ema200,
        rsi14=snapshot.rsi14,
        atr14=snapshot.atr14,
        volume_trend=snapshot.volume_trend,
        trend_regime="RISK_OFF",
    )

    decision = RiskEngine(_config()).evaluate(_buy_proposal(), state, [risk_off_snapshot], skip_consensus=True)

    assert decision.approved is True
    assert "intentionally skipped" in decision.reason


def test_skip_consensus_still_enforces_every_other_guard() -> None:
    # skip_consensus must only bypass the market-timing check, nothing else:
    # kill switch, whitelist, stop-loss requirement, and confidence floor all
    # still have to hold for a first-portfolio tranche to be approved.
    kill_switch_state = LiveRiskState(
        enabled=True,
        loss_basis_quote=Decimal("12"),
        trades_today=0,
        daily_realized_pnl_quote=Decimal("0"),
        weekly_realized_pnl_quote=Decimal("0"),
        daily_loss_pct=Decimal("0"),
        weekly_loss_pct=Decimal("0"),
        consecutive_losses=0,
        last_loss_at=None,
        hours_since_last_loss=None,
        cooldown_active=False,
        daily_limit_reached=True,
        weekly_limit_reached=False,
        consecutive_loss_limit_reached=False,
        kill_switch_active=True,
        summary="blocked",
    )

    decision = RiskEngine(_config()).evaluate(
        _buy_proposal(), kill_switch_state, [_risk_on_snapshot()], skip_consensus=True
    )

    assert decision.approved is False
    assert "kill switch" in decision.reason


def test_allowed_symbols_override_lets_a_non_strategy_symbol_through() -> None:
    # First-portfolio basket assets (e.g. BNB, SOL) are not necessarily in
    # strategy.allowed_symbols, which is specifically the tactical-trading
    # universe. The caller can substitute a different explicit whitelist.
    state = LiveRiskState(
        enabled=True,
        loss_basis_quote=Decimal("12"),
        trades_today=0,
        daily_realized_pnl_quote=Decimal("0"),
        weekly_realized_pnl_quote=Decimal("0"),
        daily_loss_pct=Decimal("0"),
        weekly_loss_pct=Decimal("0"),
        consecutive_losses=0,
        last_loss_at=None,
        hours_since_last_loss=None,
        cooldown_active=False,
        daily_limit_reached=False,
        weekly_limit_reached=False,
        consecutive_loss_limit_reached=False,
        kill_switch_active=False,
        summary="clear",
    )
    proposal = TradeProposal(
        symbol="BNBUSDC",
        action="BUY",
        confidence=Decimal("1"),
        quote_amount_usdt=Decimal("10"),
        stop_loss_pct=Decimal("1.5"),
        take_profit_pct=Decimal("3"),
        reason="First portfolio basket.",
    )

    without_override = RiskEngine(_config()).evaluate(proposal, state, [], skip_consensus=True)
    with_override = RiskEngine(_config()).evaluate(
        proposal, state, [], skip_consensus=True, allowed_symbols={"BNBUSDC"}
    )

    assert without_override.approved is False
    assert "not whitelisted" in without_override.reason
    assert with_override.approved is True


def test_consensus_approves_valid_buy() -> None:
    state = LiveRiskState(
        enabled=True,
        loss_basis_quote=Decimal("12"),
        trades_today=0,
        daily_realized_pnl_quote=Decimal("0"),
        weekly_realized_pnl_quote=Decimal("0"),
        daily_loss_pct=Decimal("0"),
        weekly_loss_pct=Decimal("0"),
        consecutive_losses=0,
        last_loss_at=None,
        hours_since_last_loss=None,
        cooldown_active=False,
        daily_limit_reached=False,
        weekly_limit_reached=False,
        consecutive_loss_limit_reached=False,
        kill_switch_active=False,
        summary="clear",
    )

    decision = RiskEngine(_config()).evaluate(_buy_proposal(), state, [_risk_on_snapshot()])

    assert decision.approved is True
    assert decision.adjusted_quote_amount_usdt == Decimal("10")
