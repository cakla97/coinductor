from decimal import Decimal

import pytest

from coinductor.first_portfolio_executor import FirstPortfolioExecutor
from trading_agent.binance_client import BinanceApiError, BinanceClient
from trading_agent.storage import Storage

CONFIG = """
[app]
mode = "DRY_RUN"
mock_data = true
database_path = "work/test.sqlite3"
reports_dir = "outputs/reports"

[binance]
api_base_url = "https://api.binance.com"
testnet_api_base_url = "https://testnet.binance.vision"

[strategy]
allowed_symbols = ["BTCUSDC"]

[orders]
default_stop_loss_pct = 5
default_take_profit_pct = 10
require_stop_loss = true

[risk]
max_trades_per_day = 10
max_daily_loss_pct = 5
max_weekly_loss_pct = 10
min_ai_confidence = 0.5
# Without this the default is 0, and "0 consecutive losses >= 0" arms the kill
# switch on a clean slate. That default is deliberate - the gate fails closed -
# so the config is what has to say otherwise.
max_consecutive_losses = 2

[consensus]
enabled = true
require_risk_on = true
require_price_above_ema200 = true
min_rsi14 = 45
max_rsi14 = 68

[earn]
max_redeem_per_run_usdt = 1000

[live_confirm]
quote_asset = "USDC"
max_quote_amount_usdt = 1000

[testnet_execution]
max_quote_amount_usdt = 1000

[trading_bankroll]
initial_seed_usdc = 0
"""


def _write_config(tmp_path) -> None:
    (tmp_path / "config.toml").write_text(CONFIG, encoding="utf-8")


def _executor(tmp_path) -> FirstPortfolioExecutor:
    return FirstPortfolioExecutor(str(tmp_path / "config.toml"), str(tmp_path / ".env"))


def test_run_tranche_rejects_an_unknown_mode(tmp_path) -> None:
    executor = _executor(tmp_path)

    with pytest.raises(ValueError):
        executor.run_tranche("BNB", Decimal("10"), Decimal("500"), 1, 3, mode="LOCAL")


@pytest.mark.parametrize("tranche_index,tranches_total", [(0, 3), (4, 3), (1, 0)])
def test_run_tranche_rejects_an_out_of_range_tranche_index(tmp_path, tranche_index, tranches_total) -> None:
    executor = _executor(tmp_path)

    with pytest.raises(ValueError):
        executor.run_tranche("BNB", Decimal("10"), Decimal("500"), tranche_index, tranches_total, mode="TESTNET")


def test_tranche_amount_is_target_pct_of_budget_split_across_tranches(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_config(tmp_path)
    executor = _executor(tmp_path)

    # BNB is not in strategy.allowed_symbols for TESTNET's BNBUSDT pair either, so
    # this will end up BLOCKED by a symbol-rules lookup failure/whitelist somewhere
    # downstream, but the quote_amount on the result must still reflect the plan
    # math: 10% of 500 budget, split across 4 tranches = 12.50 per tranche.
    monkeypatch.setattr(
        BinanceClient,
        "get_symbol_rules",
        lambda self, symbol: (_ for _ in ()).throw(BinanceApiError("not found")),
    )

    result = executor.run_tranche("BNB", Decimal("10"), Decimal("500"), 1, 4, mode="TESTNET")

    assert result.quote_amount == Decimal("12.50")


def test_run_tranche_is_idempotent_and_never_touches_binance_once_done(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_config(tmp_path)
    executor = _executor(tmp_path)

    def fail_if_called(self, symbol):
        raise AssertionError("must not contact Binance for an already-completed tranche")

    # Seed a completed tranche directly via Storage, mirroring what a prior
    # successful run_tranche call would have persisted.
    from trading_agent.config import load_config
    from trading_agent.models import FirstPortfolioTrancheResult
    from trading_agent.order_journal import OrderIntentFactory

    config = load_config(str(tmp_path / "config.toml"))
    storage = Storage(config.database_path)
    intent_id = OrderIntentFactory(config.raw).first_portfolio_intent_id("BNB", "TESTNET", 1)
    run_id = storage.start_run("FIRST_PORTFOLIO")
    storage.save_first_portfolio_tranche(
        run_id,
        FirstPortfolioTrancheResult(
            intent_id=intent_id,
            mode="TESTNET",
            asset="BNB",
            symbol="BNBUSDT",
            tranche_index=1,
            tranches_total=4,
            quote_amount=Decimal("12.50"),
            status="SUBMITTED",
            validation_summary="ok",
            confirmation_required="CONFIRM_TESTNET_ORDER",
            submitted=True,
        ),
    )
    storage.finish_run(run_id, "OK", "seeded")

    monkeypatch.setattr(BinanceClient, "get_symbol_rules", fail_if_called)

    result = executor.run_tranche("BNB", Decimal("10"), Decimal("500"), 1, 4, mode="TESTNET")

    assert result.status == "ALREADY_DONE"
    assert result.intent_id == intent_id


def test_run_tranche_blocked_by_kill_switch_never_touches_binance(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_config(tmp_path)
    executor = _executor(tmp_path)

    def fail_if_called(self, symbol):
        raise AssertionError("must not contact Binance when the risk engine already blocked the tranche")

    monkeypatch.setattr(BinanceClient, "get_symbol_rules", fail_if_called)
    monkeypatch.setattr(
        Storage,
        "get_live_risk_state",
        lambda self, run_id, config: _kill_switch_state(),
    )

    result = executor.run_tranche("BTC", Decimal("50"), Decimal("500"), 1, 3, mode="MAINNET")

    assert result.status == "BLOCKED"
    assert "kill switch" in result.validation_summary


def test_run_tranche_testnet_uses_usdt_and_mainnet_uses_configured_quote_asset(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_config(tmp_path)
    executor = _executor(tmp_path)
    monkeypatch.setattr(
        BinanceClient,
        "get_symbol_rules",
        lambda self, symbol: (_ for _ in ()).throw(BinanceApiError("not found: " + symbol)),
    )

    testnet_result = executor.run_tranche("BTC", Decimal("50"), Decimal("500"), 1, 2, mode="TESTNET")
    mainnet_result = executor.run_tranche("BTC", Decimal("50"), Decimal("500"), 1, 2, mode="MAINNET")

    assert testnet_result.symbol == "BTCUSDT"
    assert mainnet_result.symbol == "BTCUSDC"


def _kill_switch_state():
    from trading_agent.models import LiveRiskState

    return LiveRiskState(
        enabled=True,
        loss_basis_quote=Decimal("100"),
        trades_today=0,
        daily_realized_pnl_quote=Decimal("0"),
        weekly_realized_pnl_quote=Decimal("0"),
        daily_loss_pct=Decimal("0"),
        weekly_loss_pct=Decimal("0"),
        consecutive_losses=3,
        last_loss_at="2026-07-19 10:00:00",
        hours_since_last_loss=Decimal("1"),
        cooldown_active=False,
        daily_limit_reached=False,
        weekly_limit_reached=False,
        consecutive_loss_limit_reached=True,
        kill_switch_active=True,
        summary="kill switch triggered by consecutive losses",
    )


def _testnet_rules():
    from trading_agent.models import SymbolRules

    return SymbolRules(
        symbol="BNBUSDT",
        status="TRADING",
        base_asset="BNB",
        quote_asset="USDT",
        quote_order_qty_market_allowed=True,
        min_qty=Decimal("0.001"),
        max_qty=Decimal("1000"),
        step_size=Decimal("0.001"),
        min_notional=Decimal("5"),
        tick_size=Decimal("0.01"),
    )


def test_validate_only_never_asks_the_submit_gate_about_an_empty_confirmation(tmp_path, monkeypatch) -> None:
    """Validate-only used to report itself as a failed confirmation.

    It called submit() with an empty string and passed the answer along:
    "Confirmation string did not match CONFIRM_TESTNET_ORDER". True, and
    completely misleading - nobody had asked it to submit - and it read as if
    the tranche could never be sent at all.
    """
    monkeypatch.chdir(tmp_path)
    _write_config(tmp_path)
    executor = _executor(tmp_path)

    from trading_agent.models import OrderValidation
    from trading_agent.testnet_executor import TestnetExecutor

    monkeypatch.setattr(BinanceClient, "get_symbol_rules", lambda self, symbol: _testnet_rules())
    monkeypatch.setattr(
        TestnetExecutor,
        "validate_market_buy",
        lambda self, symbol, amount, rules, require_whitelist=True: OrderValidation(
            True, "BNBUSDT filters passed.", amount
        ),
    )

    def refuse(self, request, confirm):
        raise AssertionError("submit() must not be consulted when submit=False")

    monkeypatch.setattr(TestnetExecutor, "submit", refuse)

    result = executor.run_tranche("BNB", Decimal("10"), Decimal("500"), 1, 4, mode="TESTNET", submit=False)

    assert result.status == "VALIDATED"
    assert result.submitted is False
    assert "did not match" not in (result.message or "")
    assert result.validation_summary == "BNBUSDT filters passed."


def test_a_correct_confirmation_reaches_the_submit_gate_unchanged(tmp_path, monkeypatch) -> None:
    """The other half: what the user types must arrive verbatim."""
    monkeypatch.chdir(tmp_path)
    _write_config(tmp_path)
    executor = _executor(tmp_path)

    from trading_agent.models import OrderValidation, TestnetOrderResult
    from trading_agent.testnet_executor import TestnetExecutor

    seen: dict[str, str] = {}

    monkeypatch.setattr(BinanceClient, "get_symbol_rules", lambda self, symbol: _testnet_rules())
    monkeypatch.setattr(
        TestnetExecutor,
        "validate_market_buy",
        lambda self, symbol, amount, rules, require_whitelist=True: OrderValidation(True, "ok", amount),
    )

    def capture(self, request, confirm):
        seen["confirm"] = confirm
        return TestnetOrderResult(submitted=True, status="SUBMITTED", message="", response="{}")

    monkeypatch.setattr(TestnetExecutor, "submit", capture)

    executor.run_tranche(
        "BNB", Decimal("10"), Decimal("500"), 1, 4,
        mode="TESTNET", submit=True, confirm="CONFIRM_TESTNET_ORDER",
    )

    assert seen["confirm"] == "CONFIRM_TESTNET_ORDER"
