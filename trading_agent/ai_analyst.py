from __future__ import annotations

from decimal import Decimal
import json
import os
import urllib.request

from .decimal_utils import display
from .models import ActiveStrategiesReport, AiCommentary, AiDecisionMemory, CapitalSourcingPlan, GridRecommendation, LivePositionSummary, MarketResearchReport, MarketSnapshot, NextRunRecommendation, PortfolioAnalysis, RebalancingBotRecommendation, RecommendedAction, ResearchBundle, ResearchStatus, RiskDecision, StrategyDecision, TradeProposal


_TREND_PHRASES = {
    "RISK_ON": "risk-on trend",
    "RISK_OFF": "risk-off trend",
    "NEUTRAL": "neutral trend",
}


def _trend_phrase(regime: str) -> str:
    """`trend=RISK_OFF` is a field name and an enum; this is what it means."""
    return _TREND_PHRASES.get(str(regime).upper(), f"{str(regime).replace('_', '-').lower()} trend")


class AiProviderNotConfigured(RuntimeError):
    """No AI endpoint is set, so nothing was ever sent.

    Told apart from a genuine call failure because the two need opposite
    responses: one is a setting the user never filled in, the other is a
    provider that answered badly. Reporting the first as the second sent a
    reader looking for a broken model they had not configured.
    """


def commentary_failure_summary(exc: BaseException) -> str:
    """Say why there is no commentary, in terms of what the reader can act on.

    The old wording blamed "the model response" and appended the exception's
    class name, so an unconfigured provider - by far the most common case, and
    the default state - was reported as a model that had answered badly. A
    reader with no provider went looking for a broken one.
    """
    if isinstance(exc, AiProviderNotConfigured):
        return (
            "AI commentary was requested, but no AI provider is configured, so nothing was asked. "
            "Set one up in Settings, or leave it off - it is optional, and the deterministic "
            "analysis below never uses it."
        )
    return f"AI commentary could not be generated: {exc}. Deterministic analysis below is unaffected."


def proposal_fallback_reason(exc: BaseException, fallback_reason: str) -> str:
    """Same distinction for the trade proposal, which falls back deterministically."""
    if isinstance(exc, AiProviderNotConfigured):
        prefix = (
            "AI proposals were requested, but no AI provider is configured, so the deterministic "
            "analyst decided this"
        )
    else:
        prefix = f"The AI proposal failed ({exc}), so the deterministic analyst decided this"
    return f"{prefix}. {fallback_reason}"


def _string_list(value: object, limit: int = 5) -> tuple[str, ...]:
    """Coerce a model-supplied field into a short tuple of strings.

    Models do not always honour the requested JSON shape: a list may come back
    as a bare string or as a dict. Slicing those directly raised (a dict lookup
    with a slice key fails with ``KeyError: slice(None, 5, None)``) and threw
    away the whole commentary, so normalize instead of trusting the shape.
    """
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, dict):
        items: list[object] = list(value.values())
    elif isinstance(value, (list, tuple)):
        items = list(value)
    else:
        return ()
    rendered = [str(item).strip() for item in items]
    return tuple(item for item in rendered if item)[:limit]


class AiAnalyst:
    def __init__(self, config: dict):
        self.config = config

    def propose_trade(
        self,
        snapshots: list[MarketSnapshot],
        live_positions: LivePositionSummary | None = None,
        decision_memory: AiDecisionMemory | None = None,
        market_research: MarketResearchReport | None = None,
    ) -> TradeProposal:
        if self._open_live_position_blocks_buy(live_positions):
            return self._hold_proposal(
                snapshots,
                "Open live position guard: an existing live position is being monitored, so no new BUY is proposed.",
            )
        ai_config = self.config.get("ai", {})
        if not ai_config.get("enabled", False):
            return self._mock_proposal(snapshots)
        try:
            return self._openai_compatible_proposal(snapshots, live_positions, decision_memory, market_research)
        except Exception as exc:
            fallback = self._mock_proposal(snapshots)
            return TradeProposal(
                symbol=fallback.symbol,
                action=fallback.action,
                confidence=fallback.confidence,
                quote_amount_usdt=fallback.quote_amount_usdt,
                stop_loss_pct=fallback.stop_loss_pct,
                take_profit_pct=fallback.take_profit_pct,
                reason=proposal_fallback_reason(exc, fallback.reason),
            )

    def propose_manual_override(
        self,
        symbol: str,
        snapshots: list[MarketSnapshot],
        live_positions: LivePositionSummary | None = None,
    ) -> TradeProposal:
        if self._open_live_position_blocks_buy(live_positions):
            return self._hold_proposal(
                snapshots,
                "Open live position guard: an existing live position is being monitored, so no new BUY is "
                "proposed, including manual overrides.",
            )
        allowed_symbols = [str(item).upper() for item in self.config.get("strategy", {}).get("allowed_symbols", [])]
        normalized = symbol.strip().upper()
        if normalized not in allowed_symbols:
            return self._hold_proposal(
                snapshots,
                f"Manual override requested {normalized}, which is not in strategy.allowed_symbols.",
            )
        orders = self.config["orders"]
        return TradeProposal(
            symbol=normalized,
            action="BUY",
            confidence=Decimal("1"),
            quote_amount_usdt=Decimal(str(self.config["strategy"]["quote_amount_usdt"])),
            stop_loss_pct=Decimal(str(orders["default_stop_loss_pct"])),
            take_profit_pct=Decimal(str(orders["default_take_profit_pct"])),
            reason=f"Manual override: user requested a BUY evaluation for {normalized} instead of accepting HOLD.",
        )

    def comment_on_portfolio(
        self,
        portfolio: PortfolioAnalysis,
        snapshots: list[MarketSnapshot],
        proposal: TradeProposal,
        risk_decision: RiskDecision,
        grid_recommendation: GridRecommendation,
        rebalancing_bot_recommendation: RebalancingBotRecommendation,
        spot_capital_plan: CapitalSourcingPlan,
        grid_capital_plan: CapitalSourcingPlan,
        strategy_decision: StrategyDecision,
        next_run: NextRunRecommendation,
        recommended_actions: tuple[RecommendedAction, ...],
        research: ResearchBundle,
        research_status: ResearchStatus,
        active_strategies: ActiveStrategiesReport,
        decision_memory: AiDecisionMemory,
        market_research: MarketResearchReport,
    ) -> AiCommentary:
        ai_config = self.config.get("ai", {})
        if not ai_config.get("commentary_enabled", False):
            return AiCommentary(
                enabled=False,
                summary="AI commentary is disabled.",
                risks=(),
                watchlist=(),
                raw_response="",
            )

        prompt = {
            "task": (
                "Write a concise portfolio-manager commentary. Do not invent data. Do not give financial guarantees. "
                "Respect deterministic decisions and risk limits. Do not assess rebalancing in this general summary; "
                "a separate focused assessment handles it. Output JSON only."
            ),
            "ai_role_limits": [
                "The rebalancing bot proposal below is deterministic and recommend-only.",
                "Assess concentration, basket composition, threshold, and blockers; do not change target weights or unlock deployment.",
                "WBETH remains protected outside the bot. Do not recommend converting or selling it automatically.",
                "When ETH is marked FUNDED_FROM_USDC, evaluate it as a new bot allocation funded by separate USDC capital.",
                "Treat WLD as speculative and excluded unless deterministic configuration explicitly includes it.",
                "For rebalancing, the blockers field is authoritative. Do not copy Grid market status or invent any other blocker.",
                "If the rebalancing blockers do not mention market conditions, do not claim that rebalancing waits for a market regime.",
            ],
            "portfolio": {
                "total_value_usdt": str(portfolio.total_value_usdt),
                "liquid_value_usdt": str(portfolio.liquid_value_usdt),
                "locked_value_usdt": str(portfolio.locked_value_usdt),
                "locked_pct": str(portfolio.locked_pct),
                "unpriced_assets": list(portfolio.unpriced_assets),
                "top_assets": [
                    {
                        "asset": asset.asset,
                        "allocation_pct": str(asset.allocation_pct),
                        "target_pct": str(asset.target_pct) if asset.target_pct is not None else None,
                        "gap_pct": str(asset.gap_pct) if asset.gap_pct is not None else None,
                        "rebalance_action": asset.rebalance_action,
                    }
                    for asset in portfolio.assets[:8]
                ],
            },
            "market": [
                {
                    "symbol": snapshot.symbol,
                    "price": str(snapshot.price),
                    "rsi14": str(snapshot.rsi14),
                    "trend_regime": snapshot.trend_regime,
                    "volume_trend": snapshot.volume_trend,
                }
                for snapshot in snapshots
            ],
            "local_market_research": self._market_research_payload(market_research),
            "external_research_notes": [
                {
                    "source": note.source,
                    "title": note.title,
                    "content": note.content,
                }
                for note in research.notes
            ]
            if self.config.get("research", {}).get("include_in_ai_commentary", True)
            else [],
            "research_status": {
                "enabled": research_status.enabled,
                "notes_count": research_status.notes_count,
                "is_fresh": research_status.is_fresh,
                "latest_note_age_hours": str(research_status.latest_note_age_hours)
                if research_status.latest_note_age_hours is not None
                else None,
                "summary": research_status.summary,
                "request_path": research_status.request.path if research_status.request else None,
            },
            "active_strategies": {
                "summary": active_strategies.summary,
                "grid_bots": [
                    {
                        "name": item.bot.name,
                        "symbol": item.bot.symbol,
                        "range_low": str(item.bot.range_low),
                        "range_high": str(item.bot.range_high),
                        "current_price": str(item.current_price) if item.current_price is not None else None,
                        "state": item.state,
                        "recommendation": item.recommendation,
                    }
                    for item in active_strategies.grid_bots
                ],
                "rebalancing_bots": [
                    {
                        "name": item.bot.name,
                        "assets": list(item.bot.assets),
                        "target_weights_pct": [str(value) for value in item.bot.target_weights_pct],
                        "current_weights_pct": [str(value) for value in item.current_weights_pct],
                        "threshold_pct": str(item.bot.threshold_pct),
                        "max_drift_pct": str(item.max_drift_pct) if item.max_drift_pct is not None else None,
                        "state": item.state,
                        "recommendation": item.recommendation,
                    }
                    for item in active_strategies.rebalancing_bots
                ],
            },
            "decision_memory": self._memory_payload(decision_memory, include_small_sample=True),
            "memory_usage_rules": [
                "Do not claim a recurring or similar historical pattern unless pattern_inference_allowed is true.",
                "With a smaller sample, describe closed cycles only as isolated observations.",
            ],
            "deterministic_outputs": {
                "trade_proposal": proposal.__dict__,
                "risk_decision": risk_decision.__dict__,
                "grid_recommendation": grid_recommendation.__dict__,
                "rebalancing_bot_recommendation": self._rebalancing_payload(rebalancing_bot_recommendation),
                "spot_capital_plan": spot_capital_plan.__dict__,
                "grid_capital_plan": grid_capital_plan.__dict__,
                "strategy_decision": {
                    "decision_type": strategy_decision.decision_type,
                    "priority": strategy_decision.priority,
                    "summary": strategy_decision.summary,
                },
                "next_run": next_run.__dict__,
                "recommended_actions": [action.__dict__ for action in recommended_actions],
            },
            "schema": {
                "summary": "2-4 sentence concise commentary",
                "risks": ["risk bullet 1", "risk bullet 2"],
                "watchlist": ["what to monitor next"],
            },
        }
        try:
            content = self._chat_json(
                system="You are a cautious crypto portfolio assistant. Output valid JSON only.",
                user=json.dumps(prompt, default=str),
            )
            data = json.loads(content)
            rebalancing_assessment = self._focused_rebalancing_assessment(rebalancing_bot_recommendation)
            return AiCommentary(
                enabled=True,
                summary=str(data.get("summary", "")).strip() or "AI commentary returned no summary.",
                risks=_string_list(data.get("risks")),
                watchlist=_string_list(data.get("watchlist")),
                raw_response=content,
                rebalancing_assessment=rebalancing_assessment,
            )
        except Exception as exc:
            return AiCommentary(
                enabled=True,
                summary=commentary_failure_summary(exc),
                risks=(),
                watchlist=(),
                raw_response="",
            )

    def _focused_rebalancing_assessment(self, recommendation: RebalancingBotRecommendation) -> str:
        payload = self._rebalancing_payload(recommendation)
        prompt = {
            "task": (
                "Evaluate only this deterministic Binance Rebalancing Bot proposal in 1-3 concise sentences. "
                "Discuss concentration, target composition, threshold, and the listed blockers. "
                "Do not mention Grid bots, market status, RSI, trend regimes, or any blocker absent from blockers. "
                "Do not alter weights or deployment_allowed. Do not recompute funding arithmetic; use the supplied "
                "funding summary and precomputed totals exactly. Output JSON only."
            ),
            "proposal": payload,
            "schema": {"assessment": "1-3 concise sentences"},
        }
        try:
            content = self._chat_json(
                system="You are reviewing one deterministic rebalancing proposal. Use only supplied facts. Output valid JSON only.",
                user=json.dumps(prompt, default=str),
            )
            assessment = str(json.loads(content).get("assessment", "")).strip()
        except Exception:
            assessment = ""
        return self._validate_rebalancing_assessment(assessment, recommendation)

    def _validate_rebalancing_assessment(
        self,
        assessment: str,
        recommendation: RebalancingBotRecommendation,
    ) -> str:
        unsupported_markers = (
            "grid",
            "market status",
            "market state",
            "rsi",
            "trend regime",
            "suitable",
            "watch",
            "only covers",
        )
        blockers_text = " ".join(recommendation.blockers).lower()
        lowered = assessment.lower()
        unsupported = any(marker in lowered and marker not in blockers_text for marker in unsupported_markers)
        unsupported = unsupported or ("exceed" in lowered and "threshold" in lowered)
        if not assessment or unsupported:
            basket = ", ".join(f"{item.asset} {item.target_weight_pct}%" for item in recommendation.assets) or "no eligible basket"
            blocker = "; ".join(item.rstrip(".") for item in recommendation.blockers) or "none"
            return (
                f"Focused AI assessment was rejected or unavailable because it introduced unsupported context. "
                f"Deterministic proposal remains {basket}; authoritative blockers: {blocker}."
            )
        return assessment

    def _rebalancing_payload(self, recommendation: RebalancingBotRecommendation) -> dict:
        conversion_total = (
            sum((item.value_usdt for item in recommendation.funding_plan.items), Decimal("0"))
            if recommendation.funding_plan is not None
            else Decimal("0")
        )
        covered_total = (
            recommendation.funding_plan.available_usdt + conversion_total
            if recommendation.funding_plan is not None
            else Decimal("0")
        )
        uncovered_total = max(Decimal("0"), recommendation.investment_usdt - covered_total)
        return {
            "enabled": recommendation.enabled,
            "recommended": recommendation.recommended,
            "deployment_allowed": recommendation.deployment_allowed,
            "mode": recommendation.mode,
            "threshold_pct": str(recommendation.threshold_pct),
            "investment_usdt": str(recommendation.investment_usdt),
            "assets": [
                {
                    "asset": item.asset,
                    "current_value_usdt": str(item.current_value_usdt),
                    "current_weight_pct": str(item.current_weight_pct),
                    "target_weight_pct": str(item.target_weight_pct),
                    "role": item.role,
                    "status": item.status,
                    "reason": item.reason,
                }
                for item in recommendation.assets
            ],
            "excluded_assets": list(recommendation.excluded_assets),
            "blockers": list(recommendation.blockers),
            "summary": recommendation.summary,
            "funding_plan": {
                "needed_usdt": str(recommendation.funding_plan.needed_usdt),
                "available_usdt": str(recommendation.funding_plan.available_usdt),
                "missing_usdt": str(recommendation.funding_plan.missing_usdt),
                "conversion_total_usdt": str(conversion_total),
                "covered_total_usdt": str(covered_total),
                "uncovered_total_usdt": str(uncovered_total),
                "summary": recommendation.funding_plan.summary,
                "items": [item.__dict__ for item in recommendation.funding_plan.items],
            }
            if recommendation.funding_plan is not None
            else None,
        }

    def _mock_proposal(self, snapshots: list[MarketSnapshot]) -> TradeProposal:
        allowed_symbols = [str(symbol).upper() for symbol in self.config.get("strategy", {}).get("allowed_symbols", [])]
        candidates = [snapshot for snapshot in snapshots if snapshot.symbol.upper() in allowed_symbols]
        if not candidates:
            return self._hold_proposal(snapshots, "None of your allowed symbols appear in current market data.")
        buy_candidates = [snapshot for snapshot in candidates if self._is_fallback_buy_candidate(snapshot)]
        if not buy_candidates:
            # Written as a sentence, not key=value with raw Decimals: this is
            # the line on the Trade card that explains a HOLD, and an RSI
            # printed to twenty decimals made it unreadable.
            observed = ". ".join(
                f"{item.symbol}: {_trend_phrase(item.trend_regime)}, RSI {display(item.rsi14)}"
                for item in candidates
            )
            return self._hold_proposal(
                snapshots,
                f"No symbol passed the conservative BUY filters. {observed}.",
            )
        best = sorted(buy_candidates, key=self._fallback_score, reverse=True)[0]
        orders = self.config["orders"]
        return TradeProposal(
            symbol=best.symbol,
            action="BUY",
            confidence=Decimal("0.68"),
            quote_amount_usdt=Decimal(str(self.config["strategy"]["quote_amount_usdt"])),
            stop_loss_pct=Decimal(str(orders["default_stop_loss_pct"])),
            take_profit_pct=Decimal(str(orders["default_take_profit_pct"])),
            reason=(
                f"{best.symbol} passed the conservative filters: {_trend_phrase(best.trend_regime)}, "
                f"RSI {display(best.rsi14)}, price above its 200-day average."
            ),
        )

    def _openai_compatible_proposal(
        self,
        snapshots: list[MarketSnapshot],
        live_positions: LivePositionSummary | None,
        decision_memory: AiDecisionMemory | None,
        market_research: MarketResearchReport | None,
    ) -> TradeProposal:
        ai_config = self.config["ai"]
        base_url = os.getenv(ai_config["base_url_env"], "").rstrip("/")
        if not base_url:
            # Returning the deterministic proposal here swallowed the fact that
            # the model was never asked: the user ticked "AI proposals", got a
            # verdict, and nothing in it said where the verdict came from.
            # propose_trade still falls back - it just says so now.
            raise AiProviderNotConfigured("No AI provider is configured.")

        prompt = {
            "task": (
                "Rank the allowed symbols and return one conservative spot action as JSON only. "
                "You choose only action, symbol, confidence, and reason. Position size and exits are deterministic."
            ),
            "allowed_actions": ["BUY", "HOLD"],
            "allowed_symbols": self.config.get("strategy", {}).get("allowed_symbols", []),
            "guardrails": [
                "Prefer HOLD when market context is unclear.",
                "Do not propose symbols outside allowed_symbols.",
                "Use BUY only for a clearly favorable setup; execution still requires deterministic guards.",
                "Do not propose SELL; exits are handled by the separate OCO/position workflow.",
                "Historical outcomes are limited context, not proof that the same setup will repeat.",
                "Do not overfit to one win or loss and do not use martingale or revenge-trading logic.",
                "Do not claim a recurring or similar historical pattern unless decision_memory.pattern_inference_allowed is true.",
                "Market breadth, top gainers, and volume rankings are context only, never standalone BUY signals.",
                "If local market research is PARTIAL, explicitly reduce reliance on missing fields.",
            ],
            "open_live_positions": [
                {
                    "symbol": position.symbol,
                    "quantity": str(position.quantity),
                    "entry_price": str(position.entry_price),
                    "current_price": str(position.current_price) if position.current_price is not None else None,
                    "pnl_pct": str(position.pnl_pct) if position.pnl_pct is not None else None,
                    "exit_preview_status": position.exit_preview_status,
                }
                for position in (live_positions.open_positions if live_positions is not None else ())
            ],
            "snapshots": [snapshot.__dict__ for snapshot in snapshots],
            "local_market_research": self._market_research_payload(market_research),
            "decision_memory": self._memory_payload(decision_memory, include_small_sample=False),
            "schema": {
                "symbol": str(self.config.get("strategy", {}).get("allowed_symbols", ["BTCUSDT"])[0]),
                "action": "BUY",
                "confidence": 0.65,
                "reason": "short explanation",
            },
        }
        content = self._chat_json(
            system="You are a cautious crypto market analyst. Output JSON only.",
            user=json.dumps(prompt, default=str),
        )
        data = json.loads(content)
        allowed_symbols = [str(symbol).upper() for symbol in self.config.get("strategy", {}).get("allowed_symbols", [])]
        action = str(data.get("action", "HOLD")).upper()
        symbol = str(data.get("symbol", allowed_symbols[0] if allowed_symbols else "")).upper()
        confidence = self._bounded_decimal(data.get("confidence", "0"), Decimal("0"), Decimal("1"))
        if action not in {"BUY", "HOLD"}:
            return self._hold_proposal(snapshots, f"Local AI returned unsupported action {action}.")
        if symbol not in allowed_symbols:
            return self._hold_proposal(snapshots, f"Local AI returned non-whitelisted symbol {symbol}.")
        if action == "HOLD":
            return self._hold_proposal(snapshots, f"Local AI: {str(data.get('reason', 'No favorable setup.')).strip()}")
        orders = self.config["orders"]
        return TradeProposal(
            symbol=symbol,
            action=action,
            confidence=confidence,
            quote_amount_usdt=Decimal(str(self.config["strategy"]["quote_amount_usdt"])),
            stop_loss_pct=Decimal(str(orders["default_stop_loss_pct"])),
            take_profit_pct=Decimal(str(orders["default_take_profit_pct"])),
            reason=f"Local AI ranking: {str(data.get('reason', '')).strip()}",
        )

    def _market_research_payload(self, research: MarketResearchReport | None) -> dict:
        if research is None or not research.enabled:
            return {"enabled": False, "status": "DISABLED", "summary": "No local market research supplied."}
        breadth = research.breadth
        return {
            "enabled": True,
            "source": "Binance public market-data endpoints collected by the local Python runtime",
            "status": research.status,
            "summary": research.summary,
            "warnings": list(research.errors),
            "breadth": {
                "quote_asset": breadth.quote_asset,
                "symbols_analyzed": breadth.symbols_analyzed,
                "advancing": breadth.advancing,
                "declining": breadth.declining,
                "advance_pct": str(breadth.advance_pct),
                "median_change_24h_pct": str(breadth.median_change_24h_pct),
                "top_gainers": [item.__dict__ for item in breadth.top_gainers],
                "top_losers": [item.__dict__ for item in breadth.top_losers],
                "top_volume": [item.__dict__ for item in breadth.top_volume],
            }
            if breadth is not None
            else None,
            "allowed_symbol_research": [
                {
                    "symbol": item.symbol,
                    "change_24h_pct": str(item.change_24h_pct),
                    "return_7d_pct": str(item.return_7d_pct) if item.return_7d_pct is not None else None,
                    "return_30d_pct": str(item.return_30d_pct) if item.return_30d_pct is not None else None,
                    "quote_volume_24h": str(item.quote_volume_24h),
                    "trades_24h": item.trades_24h,
                    "range_24h_pct": str(item.range_24h_pct),
                    "atr_pct": str(item.atr_pct),
                    "price_vs_ema200_pct": str(item.price_vs_ema200_pct),
                    "relative_strength_vs_btc_24h_pct": (
                        str(item.relative_strength_vs_btc_24h_pct)
                        if item.relative_strength_vs_btc_24h_pct is not None
                        else None
                    ),
                    "support_30d": str(item.support_30d) if item.support_30d is not None else None,
                    "resistance_30d": str(item.resistance_30d) if item.resistance_30d is not None else None,
                    "volume_trend": item.volume_trend,
                    "trend_regime": item.trend_regime,
                }
                for item in research.symbols
            ],
        }

    def _memory_payload(self, memory: AiDecisionMemory | None, include_small_sample: bool = True) -> dict:
        if memory is None or not memory.enabled:
            return {"enabled": False, "summary": "No decision memory supplied.", "recent_closed_cycles": []}
        min_cycles = int(self.config.get("ai_memory", {}).get("min_cycles_for_pattern_inference", 3))
        pattern_allowed = len(memory.recent_cycles) >= min_cycles
        if not pattern_allowed and not include_small_sample:
            return {
                "enabled": True,
                "summary": (
                    f"{len(memory.recent_cycles)} closed cycle(s) exist, below the minimum sample "
                    f"of {min_cycles}; outcomes are withheld from trade ranking."
                ),
                "sample_size": len(memory.recent_cycles),
                "min_cycles_for_pattern_inference": min_cycles,
                "pattern_inference_allowed": False,
                "recent_closed_cycles": [],
            }
        return {
            "enabled": True,
            "summary": memory.summary,
            "sample_size": len(memory.recent_cycles),
            "min_cycles_for_pattern_inference": min_cycles,
            "pattern_inference_allowed": pattern_allowed,
            "wins": memory.wins,
            "losses": memory.losses,
            "total_realized_pnl_quote": str(memory.total_realized_pnl_quote),
            "recent_closed_cycles": [
                {
                    "symbol": cycle.symbol,
                    "buy_run_id": cycle.buy_run_id,
                    "entry_price": str(cycle.entry_price),
                    "exit_price": str(cycle.exit_price),
                    "pnl_quote": str(cycle.pnl_quote),
                    "pnl_pct": str(cycle.pnl_pct),
                    "entry_trend_regime": cycle.entry_trend_regime,
                    "entry_rsi14": str(cycle.entry_rsi14) if cycle.entry_rsi14 is not None else None,
                    "entry_price_vs_ema200_pct": (
                        str(cycle.entry_price_vs_ema200_pct)
                        if cycle.entry_price_vs_ema200_pct is not None
                        else None
                    ),
                    "proposal_reason": cycle.proposal_reason,
                }
                for cycle in memory.recent_cycles
            ],
        }

    def _bounded_decimal(self, value: object, minimum: Decimal, maximum: Decimal) -> Decimal:
        parsed = Decimal(str(value))
        return min(max(parsed, minimum), maximum)

    def _open_live_position_blocks_buy(self, live_positions: LivePositionSummary | None) -> bool:
        guard = self.config.get("live_position_guard", {})
        if not guard.get("block_new_buy_when_open", True):
            return False
        return live_positions is not None and bool(live_positions.open_positions)

    def _hold_proposal(self, snapshots: list[MarketSnapshot], reason: str) -> TradeProposal:
        allowed_symbols = [str(symbol).upper() for symbol in self.config.get("strategy", {}).get("allowed_symbols", [])]
        symbol = allowed_symbols[0] if allowed_symbols else (snapshots[0].symbol if snapshots else "BTCUSDC")
        orders = self.config["orders"]
        return TradeProposal(
            symbol=symbol,
            action="HOLD",
            confidence=Decimal("1"),
            quote_amount_usdt=Decimal("0"),
            stop_loss_pct=Decimal(str(orders["default_stop_loss_pct"])),
            take_profit_pct=Decimal(str(orders["default_take_profit_pct"])),
            reason=reason,
        )

    def _is_fallback_buy_candidate(self, snapshot: MarketSnapshot) -> bool:
        return (
            snapshot.trend_regime == "RISK_ON"
            and snapshot.price > snapshot.ema200
            and Decimal("45") <= snapshot.rsi14 <= Decimal("68")
        )

    def _fallback_score(self, snapshot: MarketSnapshot) -> Decimal:
        score = Decimal("0")
        if snapshot.volume_trend == "rising":
            score += Decimal("1")
        score += max(Decimal("0"), Decimal("68") - abs(snapshot.rsi14 - Decimal("56")))
        score += (snapshot.price - snapshot.ema200) / snapshot.ema200 * Decimal("10")
        return score

    def _chat_json(self, system: str, user: str) -> str:
        ai_config = self.config["ai"]
        base_url = os.getenv(ai_config["base_url_env"], "").rstrip("/")
        api_key = os.getenv(ai_config["api_key_env"], "")
        model = os.getenv(ai_config["model_env"], "qwen3:14b")
        if not base_url:
            raise AiProviderNotConfigured("No AI provider is configured.")

        body = json.dumps(
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": float(ai_config.get("temperature", 0.2)),
                "response_format": {"type": "json_object"},
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        request = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=body,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=int(ai_config.get("timeout_seconds", 60))) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return str(payload["choices"][0]["message"]["content"])
