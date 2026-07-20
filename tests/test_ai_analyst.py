from decimal import Decimal

from trading_agent.ai_analyst import AiAnalyst
from trading_agent.models import (
    AiDecisionMemory,
    LivePositionCycle,
    LivePositionSummary,
    LiveRiskState,
    MarketSnapshot,
    RebalancingBotAsset,
    RebalancingBotRecommendation,
)
from trading_agent.risk_engine import RiskEngine


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


def test_manual_override_builds_a_buy_proposal_for_an_allowed_symbol() -> None:
    analyst = AiAnalyst(_config())

    proposal = analyst.propose_manual_override("ethusdc", _snapshots())

    assert proposal.action == "BUY"
    assert proposal.symbol == "ETHUSDC"
    assert proposal.confidence == Decimal("1")
    assert proposal.quote_amount_usdt == Decimal("25")
    assert proposal.stop_loss_pct == Decimal("1.5")
    assert proposal.take_profit_pct == Decimal("3.0")
    assert "Manual override" in proposal.reason


def test_manual_override_refuses_a_symbol_outside_the_whitelist() -> None:
    analyst = AiAnalyst(_config())

    proposal = analyst.propose_manual_override("DOGEUSDC", _snapshots())

    assert proposal.action == "HOLD"
    assert proposal.quote_amount_usdt == Decimal("0")
    assert "not in strategy.allowed_symbols" in proposal.reason


def test_manual_override_is_blocked_while_a_live_position_is_open() -> None:
    analyst = AiAnalyst(_config())
    open_position = LivePositionCycle(
        intent_id="abc123",
        symbol="BTCUSDC",
        buy_order_id="1",
        sell_order_id=None,
        buy_quote=Decimal("500"),
        sell_quote=None,
        quantity=Decimal("0.01"),
        entry_price=Decimal("50000"),
        current_price=Decimal("51000"),
        current_value=Decimal("510"),
        pnl_quote=Decimal("10"),
        pnl_pct=Decimal("2"),
        stop_loss_price=Decimal("47500"),
        take_profit_price=Decimal("54000"),
        status="OPEN",
        exit_preview_status="MONITORING",
        exit_preview_reason="",
    )
    live_positions = LivePositionSummary(
        enabled=True,
        open_positions=(open_position,),
        closed_positions=(),
        total_realized_pnl_quote=Decimal("0"),
        summary="",
    )

    proposal = analyst.propose_manual_override("ETHUSDC", _snapshots(), live_positions=live_positions)

    assert proposal.action == "HOLD"
    assert "Open live position guard" in proposal.reason


def test_manual_override_proposal_still_fails_the_consensus_gate() -> None:
    # This is the core safety guarantee: a manual override is not a raw BUY button.
    # It still has to pass the same deterministic consensus/risk checks as any
    # AI-proposed trade.
    config = _config()
    config["risk"] = {"min_ai_confidence": "0", "max_trades_per_day": 10, "max_daily_loss_pct": "5", "max_weekly_loss_pct": "10"}
    config["orders"] = {**config["orders"], "require_stop_loss": True}
    config["consensus"] = {"enabled": True, "require_risk_on": True, "min_rsi14": "45", "max_rsi14": "68"}
    analyst = AiAnalyst(config)
    risk_engine = RiskEngine(config)
    risk_state = LiveRiskState(
        enabled=True,
        loss_basis_quote=Decimal("100"),
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
    overbought_snapshot = [
        MarketSnapshot(
            symbol="BTCUSDC",
            price=Decimal("65000"),
            ema20=Decimal("64000"),
            ema50=Decimal("63000"),
            ema200=Decimal("60000"),
            rsi14=Decimal("90"),  # far outside the 45-68 consensus band
            atr14=Decimal("1000"),
            volume_trend="rising",
            trend_regime="RISK_ON",
        )
    ]

    proposal = analyst.propose_manual_override("BTCUSDC", overbought_snapshot)
    decision = risk_engine.evaluate(proposal=proposal, risk_state=risk_state, snapshots=overbought_snapshot)

    assert proposal.action == "BUY"  # the override itself was accepted as a candidate...
    assert decision.approved is False  # ...but the deterministic risk engine still rejects it
    assert "Consensus gate" in decision.reason
    assert "RSI14" in decision.reason


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
                status="FUNDED_FROM_USDC",
                reason="WBETH remains protected and ETH is funded from USDC.",
            ),
        ),
        excluded_assets=("WLD",),
        blockers=(),
        manual_steps=(),
        summary="ETH allocation is funded from separate USDC.",
    )

    payload = analyst._rebalancing_payload(recommendation)

    assert payload["deployment_allowed"] is False
    assert payload["assets"][0]["status"] == "FUNDED_FROM_USDC"
    assert payload["excluded_assets"] == ["WLD"]
    assert payload["blockers"] == []


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


def test_rebalancing_assessment_rejects_funding_recalculation_phrase() -> None:
    analyst = AiAnalyst(_config())
    recommendation = RebalancingBotRecommendation(
        enabled=True,
        recommended=False,
        deployment_allowed=False,
        mode="THRESHOLD",
        threshold_pct=Decimal("5"),
        investment_usdt=Decimal("200"),
        assets=(),
        excluded_assets=(),
        blockers=("Safe funding gap remains.",),
        manual_steps=(),
        summary="test",
    )

    result = analyst._validate_rebalancing_assessment(
        "The funding plan only covers 11.80 USDC.",
        recommendation,
    )

    assert "rejected" in result


def test_rebalancing_assessment_rejects_target_weight_as_threshold_drift() -> None:
    analyst = AiAnalyst(_config())
    recommendation = RebalancingBotRecommendation(
        enabled=True,
        recommended=False,
        deployment_allowed=False,
        mode="THRESHOLD",
        threshold_pct=Decimal("5"),
        investment_usdt=Decimal("200"),
        assets=(),
        excluded_assets=(),
        blockers=("Safe funding gap remains.",),
        manual_steps=(),
        summary="test",
    )

    result = analyst._validate_rebalancing_assessment(
        "The target allocation exceeds the 5% threshold.",
        recommendation,
    )

    assert "rejected" in result
