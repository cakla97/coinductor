from decimal import Decimal

from trading_agent.models import MarketSnapshot, TradeProposal
from trading_agent.storage import Storage


def test_memory_uses_proportional_cost_basis_for_partial_oco_sell(tmp_path) -> None:
    storage = Storage(tmp_path / "agent.sqlite3")
    run_id = storage.start_run("DRY_RUN")
    storage.save_market_snapshots(
        run_id,
        [
            MarketSnapshot(
                symbol="BTCUSDC",
                price=Decimal("64610.75"),
                ema20=Decimal("65000"),
                ema50=Decimal("66000"),
                ema200=Decimal("62000"),
                rsi14=Decimal("47.5"),
                atr14=Decimal("1200"),
                volume_trend="falling",
                trend_regime="RISK_OFF",
            )
        ],
    )
    storage.save_proposal(
        run_id,
        TradeProposal(
            symbol="BTCUSDC",
            action="BUY",
            confidence=Decimal("0.68"),
            quote_amount_usdt=Decimal("10"),
            stop_loss_pct=Decimal("1.5"),
            take_profit_pct=Decimal("3"),
            reason="Test entry.",
        ),
    )
    storage.connection.execute(
        """
        insert into live_orders (
            run_id, intent_id, symbol, side, order_type, quote_amount_usdt, quote_asset,
            status, submitted, order_id, executed_quantity, cumulative_quote_qty,
            validation_summary, message
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (run_id, "cycle-1", "BTCUSDC", "BUY", "MARKET", "10", "USDC", "FILLED", 1, "buy-1", "0.00015", "9.69161250", "", ""),
    )
    storage.connection.execute(
        """
        insert into live_orders (
            run_id, intent_id, symbol, side, order_type, quote_amount_usdt, quote_asset,
            status, submitted, order_id, executed_quantity, cumulative_quote_qty,
            validation_summary, message
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (run_id, "sell-cycle-1", "BTCUSDC", "SELL", "OCO", "0", "USDC", "FILLED", 1, "sell-1", "0.00014", "8.909712", "", ""),
    )
    storage.connection.commit()

    memory = storage.get_ai_decision_memory({"ai_memory": {"enabled": True, "max_closed_cycles": 10}})

    assert len(memory.recent_cycles) == 1
    cycle = memory.recent_cycles[0]
    assert cycle.pnl_quote.quantize(Decimal("0.000001")) == Decimal("-0.135793")
    assert cycle.entry_trend_regime == "RISK_OFF"
    assert cycle.entry_rsi14 == Decimal("47.5")
