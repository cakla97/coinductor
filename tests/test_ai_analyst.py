from decimal import Decimal

from trading_agent.ai_analyst import AiAnalyst
from trading_agent.models import AiDecisionMemory, MarketSnapshot, RebalancingBotAsset, RebalancingBotRecommendation


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


def test_small_memory_sample_is_withheld_from_trade_ranking() -> None:
    config = _config()
    config["ai_memory"] = {"min_cycles_for_pattern_inference": 3}
    analyst = AiAnalyst(config)

    payload = analyst._memory_payload(_memory(), include_small_sample=False)

    assert payload["pattern_inference_allowed"] is False
    assert payload["recent_closed_cycles"] == []
    assert "withheld from trade ranking" in payload["summary"]


def test_rebalancing_payload_preserves_deterministic_blocker() -> None:
    analyst = AiAnalyst(_config())
    recommendation = RebalancingBotRecommendation(
        enabled=True,
        recommended=False,
        deployment_allowed=False,
        mode="THRESHOLD",
        threshold_pct=Decimal("5"),
        investment_usdt=Decimal("100"),
        assets=(
            RebalancingBotAsset(
                asset="ETH",
                current_value_usdt=Decimal("95"),
                current_weight_pct=Decimal("12"),
                target_weight_pct=Decimal("23.4"),
                role="PROTECTED",
                status="REQUIRES_CONVERSION",
                reason="WBETH conversion is manual.",
            ),
        ),
        excluded_assets=("WLD",),
        blockers=("Do not convert protected WBETH automatically.",),
        manual_steps=(),
        summary="Blocked pending manual WBETH decision.",
    )

    payload = analyst._rebalancing_payload(recommendation)

    assert payload["deployment_allowed"] is False
    assert payload["assets"][0]["status"] == "REQUIRES_CONVERSION"
    assert payload["excluded_assets"] == ["WLD"]
    assert payload["blockers"] == ["Do not convert protected WBETH automatically."]


def test_rebalancing_payload_has_no_inferred_market_blocker() -> None:
    analyst = AiAnalyst(_config())
    recommendation = RebalancingBotRecommendation(
        enabled=True,
        recommended=False,
        deployment_allowed=False,
        mode="THRESHOLD",
        threshold_pct=Decimal("5"),
        investment_usdt=Decimal("100"),
        assets=(),
        excluded_assets=(),
        blockers=("Manual WBETH decision required.",),
        manual_steps=(),
        summary="Blocked by WBETH decision.",
    )

    payload = analyst._rebalancing_payload(recommendation)

    assert payload["blockers"] == ["Manual WBETH decision required."]
    assert "market_status" not in payload


def test_rebalancing_assessment_rejects_grid_market_contamination() -> None:
    analyst = AiAnalyst(_config())
    recommendation = RebalancingBotRecommendation(
        enabled=True,
        recommended=False,
        deployment_allowed=False,
        mode="THRESHOLD",
        threshold_pct=Decimal("5"),
        investment_usdt=Decimal("100"),
        assets=(
            RebalancingBotAsset(
                asset="BTC",
                current_value_usdt=Decimal("200"),
                current_weight_pct=Decimal("25"),
                target_weight_pct=Decimal("60"),
                role="CORE",
                status="ELIGIBLE",
                reason="test",
            ),
        ),
        excluded_assets=("WLD",),
        blockers=("Manual WBETH decision required.",),
        manual_steps=(),
        summary="test",
    )

    result = analyst._validate_rebalancing_assessment(
        "Wait for Grid market status to become SUITABLE.",
        recommendation,
    )

    assert "rejected" in result
    assert "Manual WBETH decision required." in result
