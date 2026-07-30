from decimal import Decimal

import pytest

from trading_agent.ai_analyst import (
    AiAnalyst,
    AiProviderNotConfigured,
    commentary_failure_summary,
    proposal_fallback_reason,
)
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
    assert "not among your allowed symbols" in proposal.reason
    assert proposal.reason_message.key == "trade_model_symbol_not_allowed"


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
    assert "unsupported action (SELL)" in proposal.reason
    assert proposal.reason_message.key == "trade_model_unsupported_action"


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
    assert "not among your allowed symbols" in proposal.reason


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
    assert "existing live position is being monitored" in proposal.reason


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


def test_string_list_tolerates_shapes_models_actually_return() -> None:
    from trading_agent.ai_analyst import _string_list

    # A dict here used to raise KeyError: slice(None, 5, None), which discarded
    # the entire AI commentary and surfaced the raw Python artifact to the user.
    assert _string_list({"r1": "alpha", "r2": "beta"}) == ("alpha", "beta")
    assert _string_list("single risk") == ("single risk",)
    assert _string_list(["a", "b", "c", "d", "e", "f"]) == ("a", "b", "c", "d", "e")
    assert _string_list(None) == ()
    assert _string_list(42) == ()
    assert _string_list(["", "   ", "ok"]) == ("ok",)


def test_missing_provider_is_told_apart_from_a_failed_call() -> None:
    """The default state is "no provider", and it was reported as a bad answer.

    The old wording blamed "the model response was not usable" and appended the
    exception class name, so a user who had never configured AI went looking
    for a broken model instead of an empty setting.
    """
    not_configured = commentary_failure_summary(AiProviderNotConfigured("No AI provider is configured."))
    failed = commentary_failure_summary(TimeoutError("read timed out"))

    assert "no AI provider is configured" in not_configured
    assert "optional" in not_configured
    assert "model response" not in not_configured
    assert "read timed out" in failed, "a real failure must keep its cause"
    assert "RuntimeError" not in failed and "TimeoutError" not in failed


def test_proposal_fallback_reason_keeps_the_deterministic_verdict() -> None:
    fallback = "Fallback analyst: no allowed symbol passed conservative BUY filters."

    not_configured = proposal_fallback_reason(AiProviderNotConfigured("x"), fallback)
    failed = proposal_fallback_reason(ValueError("bad json"), fallback)

    assert not_configured.endswith(fallback) and failed.endswith(fallback)
    assert "no AI provider is configured" in not_configured
    assert "bad json" in failed


def test_unset_endpoint_raises_the_dedicated_error(monkeypatch) -> None:
    monkeypatch.delenv("LLM_BASE_URL", raising=False)

    with pytest.raises(AiProviderNotConfigured):
        AiAnalyst(_config())._chat_json(system="s", user="u")


def test_enabled_ai_without_a_provider_still_returns_a_deterministic_proposal(monkeypatch) -> None:
    monkeypatch.delenv("LLM_BASE_URL", raising=False)

    proposal = AiAnalyst(_config()).propose_trade(_snapshots(), decision_memory=_memory())

    assert proposal.action in {"HOLD", "BUY"}, "the run must not be lost with the model"
    assert "no AI provider is configured" in proposal.reason


def test_indicator_values_are_rounded_for_the_sentence_a_person_reads() -> None:
    """RSI comes out of division at full precision.

    Printed raw it ran to twenty-odd decimals in the middle of the line that
    explains a HOLD on the Trade card.
    """
    noisy = MarketSnapshot(
        symbol="BTCUSDC", price=Decimal("65000"), ema20=Decimal("64000"), ema50=Decimal("63000"),
        ema200=Decimal("60000"), rsi14=Decimal("43.384672227767928463538468495"),
        atr14=Decimal("1000"), volume_trend="rising", trend_regime="RISK_OFF",
    )

    reason = AiAnalyst(_config())._mock_proposal([noisy]).reason

    assert "RSI 43.4" in reason
    assert "43.3846" not in reason
    # Field names and enums are not sentences.
    assert "trend=" not in reason and "RISK_OFF" not in reason
    assert "risk-off trend" in reason


def test_commentary_asks_the_model_for_the_readers_language() -> None:
    """Commentary is the model's own prose.

    Unlike our own text it cannot be translated at the display boundary, so it
    came back in English beside a Czech screen; it has to be asked up front.
    """
    config = _config()
    config["ai"]["response_language"] = "cs"

    assert "in Czech" in AiAnalyst(config)._language_instruction()
    assert "JSON keys in English" in AiAnalyst(config)._language_instruction()
    assert "in English" in AiAnalyst(_config())._language_instruction()


def test_every_model_call_asks_for_the_readers_language() -> None:
    """Only the commentary call carried the instruction.

    The trade proposal and the rebalancing assessment did not, so the Trade
    card read "AI uvedla: Market context remains unclear..." on a Czech screen.
    Asserting per call site rather than on one prompt, because the gap was a
    call site nobody had looked at.
    """
    import re
    from pathlib import Path

    source = Path(__file__).resolve().parents[1].joinpath("trading_agent", "ai_analyst.py").read_text(encoding="utf-8")
    # Each _chat_json(...) up to its user= argument, which always follows system=.
    calls = re.findall(r"_chat_json\(\s*system=(.*?)user=", source, re.DOTALL)
    assert len(calls) >= 3, f"the extraction pattern is stale: found {len(calls)} call sites"
    missing = [call.strip()[:60] for call in calls if "_language_instruction()" not in call]
    assert missing == [], f"model calls that do not ask for the reader's language: {missing}"


def test_product_names_are_pinned_so_the_model_cannot_translate_them() -> None:
    """A model asked for Czech rendered "Grid" as "sit" - Czech for network.

    It names nothing a reader can find in Binance's interface, and it hides a
    stray Grid mention from _validate_rebalancing_assessment, which matches on
    the word itself.
    """
    config = _config()
    config["ai"]["response_language"] = "cs"
    instruction = AiAnalyst(config)._language_instruction()

    for name in ("Grid", "Rebalancing Bot", "Binance", "USDC"):
        assert name in instruction, f"{name} is not pinned"
    assert "untranslated" in instruction


def test_a_non_numeric_field_does_not_throw_the_whole_proposal_away() -> None:
    """Models return "high" where a number was asked for.

    Decimal(str(value)) raised ConversionSyntax on that, losing the entire
    proposal over one field - and reporting the loss as
    "[<class 'decimal.ConversionSyntax'>]" on the Trade card.
    """
    analyst = AiAnalyst(_config())
    low, high = Decimal("0"), Decimal("1")

    assert analyst._bounded_decimal("0.72", low, high) == Decimal("0.72")
    assert analyst._bounded_decimal("0.72 (strong)", low, high) == Decimal("0.72")
    # Nothing numeric at all: take the conservative end rather than raising.
    assert analyst._bounded_decimal("high", low, high) == low
    assert analyst._bounded_decimal(None, low, high) == low
    assert analyst._bounded_decimal("85%", low, high) == high


def test_a_failure_is_described_by_its_cause_not_its_class_internals() -> None:
    from decimal import InvalidOperation

    from trading_agent.ai_analyst import _describe_exception

    # This is what a Decimal error stringifies to, and it reached the screen.
    assert "class" not in _describe_exception(InvalidOperation())
    assert _describe_exception(TimeoutError("read timed out")) == "read timed out"


def test_a_summary_is_salvaged_from_whatever_shape_the_model_returned() -> None:
    """Models answer with their own structure and ignore the requested key.

    That left the card reading "AI commentary returned no summary" next to
    1300 characters of perfectly usable prose.
    """
    from trading_agent.ai_analyst import _salvaged_summary

    own_shape = {
        "trade_proposal": {
            "pair": "BTCUSDC",
            "reasoning": "Market trend is RISK_OFF with falling volume and price below EMA200.",
        },
        "urgency": "low",
    }

    assert "RISK_OFF with falling volume" in _salvaged_summary(own_shape)
    assert _salvaged_summary({"summary": "All good."}) == "All good."
    # Enums and numbers are not sentences; nothing usable means saying so.
    nothing = _salvaged_summary({"action": "HOLD", "confidence": 1})
    assert "not in the format" in nothing
