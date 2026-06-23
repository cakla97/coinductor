from decimal import Decimal

from trading_agent.models import MarketSnapshot, TradeProposal
from trading_agent.shadow_evaluator import ShadowEvaluator
from trading_agent.storage import Storage


class HistoricalClient:
    def __init__(self, prices: dict[str, Decimal]):
        self.prices = prices

    def get_historical_close(self, symbol: str, timestamp_ms: int) -> Decimal:
        assert timestamp_ms > 0
        return self.prices[symbol]


def _config() -> dict:
    return {
        "ai": {"enabled": True},
        "shadow_evaluation": {
            "enabled": True,
            "require_ai_enabled": True,
            "horizon_hours": 24,
            "decision_threshold_pct": 0.5,
        },
    }


def _snapshots(btc: str = "100", eth: str = "100") -> list[MarketSnapshot]:
    return [
        _snapshot("BTCUSDC", btc),
        _snapshot("ETHUSDC", eth),
    ]


def _snapshot(symbol: str, price: str) -> MarketSnapshot:
    value = Decimal(price)
    return MarketSnapshot(
        symbol=symbol,
        price=value,
        ema20=value,
        ema50=value,
        ema200=value,
        rsi14=Decimal("50"),
        atr14=Decimal("2"),
        volume_trend="flat",
        trend_regime="NEUTRAL",
    )


def _proposal(action: str, symbol: str = "BTCUSDC") -> TradeProposal:
    return TradeProposal(
        symbol=symbol,
        action=action,
        confidence=Decimal("0.8"),
        quote_amount_usdt=Decimal("25") if action == "BUY" else Decimal("0"),
        stop_loss_pct=Decimal("1.5"),
        take_profit_pct=Decimal("3"),
        reason="Shadow test.",
    )


def _age_run(storage: Storage, run_id: int) -> None:
    storage.connection.execute(
        "update runs set started_at = datetime('now', '-25 hours') where id = ?",
        (run_id,),
    )
    storage.connection.commit()


def test_buy_signal_uses_historical_horizon_price(tmp_path) -> None:
    storage = Storage(tmp_path / "agent.sqlite3")
    evaluator = ShadowEvaluator(
        _config(),
        storage,
        HistoricalClient({"BTCUSDC": Decimal("101"), "ETHUSDC": Decimal("100.5")}),
    )
    first_run = storage.start_run("DRY_RUN")
    first = evaluator.process(first_run, _proposal("BUY"), _snapshots())
    storage.finish_run(first_run, "OK", "done")
    _age_run(storage, first_run)

    second_run = storage.start_run("DRY_RUN")
    second = evaluator.process(second_run, _proposal("HOLD"), _snapshots("90", "90"))

    assert first.current_signal is not None
    assert len(second.newly_evaluated) == 1
    evaluation = second.newly_evaluated[0]
    assert evaluation.symbol_return_pct == Decimal("1.00")
    assert evaluation.verdict == "BUY_GAIN"
    assert evaluation.score == "CORRECT"
    assert evaluation.price_source == "BINANCE_1M_AT_HORIZON"


def test_hold_is_wrong_when_allowed_universe_had_gain(tmp_path) -> None:
    storage = Storage(tmp_path / "agent.sqlite3")
    evaluator = ShadowEvaluator(
        _config(),
        storage,
        HistoricalClient({"BTCUSDC": Decimal("99"), "ETHUSDC": Decimal("102")}),
    )
    first_run = storage.start_run("DRY_RUN")
    evaluator.process(first_run, _proposal("HOLD"), _snapshots())
    storage.finish_run(first_run, "OK", "done")
    _age_run(storage, first_run)

    second_run = storage.start_run("DRY_RUN")
    report = evaluator.process(second_run, _proposal("HOLD"), _snapshots())

    evaluation = report.newly_evaluated[0]
    assert evaluation.best_universe_symbol == "ETHUSDC"
    assert evaluation.best_universe_return_pct == Decimal("2.00")
    assert evaluation.verdict == "HOLD_MISSED_GAIN"
    assert evaluation.score == "WRONG"


def test_shadow_signal_is_not_recorded_when_ai_is_disabled(tmp_path) -> None:
    config = _config()
    config["ai"]["enabled"] = False
    storage = Storage(tmp_path / "agent.sqlite3")
    evaluator = ShadowEvaluator(config, storage)
    run_id = storage.start_run("DRY_RUN")

    report = evaluator.process(run_id, _proposal("HOLD"), _snapshots())

    assert report.current_signal is None
    assert report.pending_count == 0
