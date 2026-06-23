from decimal import Decimal

from trading_agent.ai_analyst import AiAnalyst
from trading_agent.models import AiDecisionMemory, MarketSnapshot


def _config() -> dict:
    return {
        "ai": {
            "enabled": True,
            "base_url_env": "LLM_BASE_URL",
            "api_key_env": "LLM_API_KEY",
            "model_env": "LLM_MODEL",
            "temperature": 0.2,
        },
        "strategy": {
            "allowed_symbols": ["BTCUSDC", "ETHUSDC"],
            "quote_amount_usdt": 25,
        },
        "orders": {
            "default_stop_loss_pct": 1.5,
            "default_take_profit_pct": 3.0,
        },
        "live_position_guard": {"block_new_buy_when_open": True},
    }


def _snapshots() -> list[MarketSnapshot]:
    return [
        MarketSnapshot(
            symbol="BTCUSDC",
            price=Decimal("65000"),
            ema20=Decimal("64000"),
            ema50=Decimal("63000"),
            ema200=Decimal("60000"),
            rsi14=Decimal("55"),
            atr14=Decimal("1000"),
            volume_trend="rising",
            trend_regime="RISK_ON",
        )
    ]


def _memory() -> AiDecisionMemory:
    return AiDecisionMemory(True, 0, 0, 0, Decimal("0"), (), "No closed cycles.")


def test_qwen_only_ranks_action_and_symbol(monkeypatch) -> None:
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    analyst = AiAnalyst(_config())
    monkeypatch.setattr(
        analyst,
        "_chat_json",
        lambda **_: '{"symbol":"BTCUSDC","action":"BUY","confidence":0.72,'
        '"quote_amount_usdt":999,"stop_loss_pct":99,"take_profit_pct":99,"reason":"best allowed setup"}',
    )

    proposal = analyst.propose_trade(_snapshots(), decision_memory=_memory())

    assert proposal.action == "BUY"
    assert proposal.symbol == "BTCUSDC"
    assert proposal.quote_amount_usdt == Decimal("25")
    assert proposal.stop_loss_pct == Decimal("1.5")
    assert proposal.take_profit_pct == Decimal("3.0")


def test_non_whitelisted_symbol_becomes_hold(monkeypatch) -> None:
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    analyst = AiAnalyst(_config())
    monkeypatch.setattr(
        analyst,
        "_chat_json",
        lambda **_: '{"symbol":"DOGEUSDC","action":"BUY","confidence":0.99,"reason":"outside universe"}',
    )

    proposal = analyst.propose_trade(_snapshots(), decision_memory=_memory())

    assert proposal.action == "HOLD"
    assert proposal.quote_amount_usdt == Decimal("0")
    assert "non-whitelisted" in proposal.reason


def test_sell_action_becomes_hold(monkeypatch) -> None:
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    analyst = AiAnalyst(_config())
    monkeypatch.setattr(
        analyst,
        "_chat_json",
        lambda **_: '{"symbol":"BTCUSDC","action":"SELL","confidence":0.99,"reason":"unsupported exit"}',
    )

    proposal = analyst.propose_trade(_snapshots(), decision_memory=_memory())

    assert proposal.action == "HOLD"
    assert "unsupported action SELL" in proposal.reason
