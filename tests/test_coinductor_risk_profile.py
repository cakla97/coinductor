from decimal import Decimal as D
from pathlib import Path
import shutil
import tomllib

from coinductor.risk_profile import (
    STYLE_GATES,
    apply_bots_to_config,
    apply_drawdown_to_config,
    apply_style_to_config,
    describe_gates,
    gates_for,
)
from trading_agent.models import LiveRiskState, MarketSnapshot, TradeProposal
from trading_agent.risk_engine import RiskEngine

TEMPLATE = Path(__file__).resolve().parent.parent / "config.example.toml"


def _config(tmp_path):
    """The tracked neutral template, so the engine sees a complete config."""
    path = tmp_path / "config.toml"
    shutil.copy(TEMPLATE, path)
    text = path.read_text(encoding="utf-8") + "\n# keep this comment\n"
    path.write_text(text, encoding="utf-8")
    apply_style_to_config(path, "CONSERVATIVE")  # known baseline
    return path


def _proposal():
    return TradeProposal(
        symbol="BTCUSDC", action="BUY", confidence=D("0.8"), quote_amount_usdt=D("25"),
        stop_loss_pct=D("1.5"), take_profit_pct=D("3.0"), reason="test",
    )


def _state():
    return LiveRiskState(
        True, D("1000"), 0, D("0"), D("0"), D("0"), D("0"), 0, None, D("999"),
        False, False, False, False, False, "ok",
    )


def _snapshot(regime, price, ema50, ema200, rsi):
    return MarketSnapshot("BTCUSDC", D(price), D(price), D(ema50), D(ema200), D(rsi), D("500"), "rising", regime)


def _approves(config_path, snapshot) -> bool:
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    return RiskEngine(config).evaluate(_proposal(), _state(), [snapshot], portfolio_value=None, spendable_quote=None).approved


def test_every_style_only_moves_the_trend_filter() -> None:
    """Loss protection must not be reachable from the onboarding style."""
    for gates in STYLE_GATES.values():
        assert set(gates) == {"require_risk_on", "min_rsi14", "max_rsi14"}
        # The EMA200 gate is the main downtrend protection and is never mapped.
        assert "require_price_above_ema200" not in gates


def test_applying_a_style_leaves_the_rest_of_the_config_alone(tmp_path) -> None:
    path = _config(tmp_path)
    before = tomllib.loads(path.read_text(encoding="utf-8"))

    apply_style_to_config(path, "ACTIVE")

    after_text = path.read_text(encoding="utf-8")
    after = tomllib.loads(after_text)
    assert after["risk"] == before["risk"], "risk limits were touched"
    assert after["orders"] == before["orders"]
    assert after["strategy"] == before["strategy"]
    assert after["consensus"]["require_price_above_ema200"] is True
    assert "# keep this comment" in after_text, "comments were lost"


def test_style_changes_are_reported(tmp_path) -> None:
    path = _config(tmp_path)

    changed = apply_style_to_config(path, "ACTIVE")

    assert changed["require_risk_on"] == "true -> false"
    # Re-applying the same style is a no-op, so nothing is reported twice.
    assert apply_style_to_config(path, "ACTIVE") == {}


def test_styles_produce_different_decisions(tmp_path) -> None:
    path = _config(tmp_path)
    neutral_uptrend = _snapshot("NEUTRAL", "110000", "105000", "95000", "58")
    weak_rsi = _snapshot("RISK_ON", "110000", "105000", "95000", "42")

    apply_style_to_config(path, "CONSERVATIVE")
    assert _approves(path, neutral_uptrend) is False
    assert _approves(path, weak_rsi) is False

    apply_style_to_config(path, "BALANCED")
    assert _approves(path, neutral_uptrend) is True
    assert _approves(path, weak_rsi) is False

    apply_style_to_config(path, "ACTIVE")
    assert _approves(path, neutral_uptrend) is True
    assert _approves(path, weak_rsi) is True


def test_no_style_buys_into_a_downtrend(tmp_path) -> None:
    """The EMA200 gate must hold at every level, including Active."""
    path = _config(tmp_path)
    downtrend = _snapshot("RISK_OFF", "64358", "65037", "72705", "52.6")

    for style in ("CONSERVATIVE", "BALANCED", "ACTIVE"):
        apply_style_to_config(path, style)
        assert _approves(path, downtrend) is False, style


def test_unknown_style_falls_back_to_balanced() -> None:
    assert gates_for("nonsense") == STYLE_GATES["BALANCED"]
    assert gates_for("active") == STYLE_GATES["ACTIVE"]


def test_the_wizard_hint_matches_the_gates_it_writes() -> None:
    """The hint is generated, so it can never promise the wrong numbers."""
    for language in ("en", "cs"):
        for style, gates in STYLE_GATES.items():
            hint = describe_gates(style, language)
            assert str(int(gates["min_rsi14"])) in hint, (style, language)
            assert str(int(gates["max_rsi14"])) in hint, (style, language)
            assert ("RISK_ON" in hint) is gates["require_risk_on"], style
            # Every level must keep advertising the protections it cannot move.
            assert "EMA200" in hint
            assert "{" not in hint, "unformatted placeholder"


def test_missing_config_is_not_an_error(tmp_path) -> None:
    assert apply_style_to_config(tmp_path / "absent.toml", "ACTIVE") == {}
    assert apply_drawdown_to_config(tmp_path / "absent.toml", 20) == {}
    assert apply_bots_to_config(tmp_path / "absent.toml", True) == {}


def test_drawdown_moves_only_the_loss_caps(tmp_path) -> None:
    path = _config(tmp_path)
    before = tomllib.loads(path.read_text(encoding="utf-8"))

    apply_drawdown_to_config(path, 20)

    after = tomllib.loads(path.read_text(encoding="utf-8"))
    assert after["risk"]["max_daily_loss_pct"] == 2.0
    assert after["risk"]["max_weekly_loss_pct"] == 6.0
    # The rest of the loss protection is not reachable from the wizard.
    assert after["risk"]["kill_switch_enabled"] == before["risk"]["kill_switch_enabled"]
    assert after["risk"]["max_risk_per_trade_pct"] == before["risk"]["max_risk_per_trade_pct"]
    assert after["risk"]["max_position_pct_per_asset"] == before["risk"]["max_position_pct_per_asset"]
    assert after["consensus"] == before["consensus"]


def test_drawdown_off_leaves_the_loss_caps_alone(tmp_path) -> None:
    path = _config(tmp_path)
    apply_drawdown_to_config(path, 20)
    armed = tomllib.loads(path.read_text(encoding="utf-8"))["risk"]

    assert apply_drawdown_to_config(path, 0) == {}

    assert tomllib.loads(path.read_text(encoding="utf-8"))["risk"] == armed


def test_no_drawdown_level_exceeds_the_table(tmp_path) -> None:
    """The wizard must never be able to push the daily cap past the table."""
    path = _config(tmp_path)
    for level in (-100, 0, 5, 10, 15, 20, 999):
        apply_drawdown_to_config(path, level)
        risk = tomllib.loads(path.read_text(encoding="utf-8"))["risk"]
        assert risk["max_daily_loss_pct"] <= 2.0, level
        assert risk["max_weekly_loss_pct"] <= 6.0, level


def test_bots_toggle_moves_only_the_enabled_flag(tmp_path) -> None:
    path = _config(tmp_path)
    before = tomllib.loads(path.read_text(encoding="utf-8"))["grid_bot"]

    changed = apply_bots_to_config(path, False)

    after = tomllib.loads(path.read_text(encoding="utf-8"))["grid_bot"]
    assert changed == {"enabled": "true -> false"}
    assert after["enabled"] is False
    # recommend_only and the capital caps must stay put: turning bots on must
    # never turn a recommendation into something that places an order.
    assert after["recommend_only"] == before["recommend_only"] is True
    assert after["max_grid_capital_usdt"] == before["max_grid_capital_usdt"]
    assert apply_bots_to_config(path, False) == {}
