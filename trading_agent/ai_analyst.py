from __future__ import annotations

from decimal import Decimal
import json
import os
import urllib.request

from .models import ActiveStrategiesReport, AiCommentary, CapitalSourcingPlan, GridRecommendation, LivePositionSummary, MarketSnapshot, NextRunRecommendation, PortfolioAnalysis, RecommendedAction, ResearchBundle, ResearchStatus, RiskDecision, StrategyDecision, TradeProposal


class AiAnalyst:
    def __init__(self, config: dict):
        self.config = config

    def propose_trade(self, snapshots: list[MarketSnapshot], live_positions: LivePositionSummary | None = None) -> TradeProposal:
        if self._open_live_position_blocks_buy(live_positions):
            return self._hold_proposal(
                snapshots,
                "Open live position guard: an existing live position is being monitored, so no new BUY is proposed.",
            )
        ai_config = self.config.get("ai", {})
        if not ai_config.get("enabled", False):
            return self._mock_proposal(snapshots)
        return self._openai_compatible_proposal(snapshots, live_positions)

    def comment_on_portfolio(
        self,
        portfolio: PortfolioAnalysis,
        snapshots: list[MarketSnapshot],
        proposal: TradeProposal,
        risk_decision: RiskDecision,
        grid_recommendation: GridRecommendation,
        spot_capital_plan: CapitalSourcingPlan,
        grid_capital_plan: CapitalSourcingPlan,
        strategy_decision: StrategyDecision,
        next_run: NextRunRecommendation,
        recommended_actions: tuple[RecommendedAction, ...],
        research: ResearchBundle,
        research_status: ResearchStatus,
        active_strategies: ActiveStrategiesReport,
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
                "Respect deterministic decisions and risk limits. Output JSON only."
            ),
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
            },
            "deterministic_outputs": {
                "trade_proposal": proposal.__dict__,
                "risk_decision": risk_decision.__dict__,
                "grid_recommendation": grid_recommendation.__dict__,
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
            return AiCommentary(
                enabled=True,
                summary=str(data.get("summary", "")).strip() or "AI commentary returned no summary.",
                risks=tuple(str(item) for item in data.get("risks", [])[:5]),
                watchlist=tuple(str(item) for item in data.get("watchlist", [])[:5]),
                raw_response=content,
            )
        except Exception as exc:
            return AiCommentary(
                enabled=True,
                summary=f"AI commentary failed: {exc}",
                risks=(),
                watchlist=(),
                raw_response="",
            )

    def _mock_proposal(self, snapshots: list[MarketSnapshot]) -> TradeProposal:
        allowed_symbols = [str(symbol).upper() for symbol in self.config.get("strategy", {}).get("allowed_symbols", [])]
        candidates = [snapshot for snapshot in snapshots if snapshot.symbol.upper() in allowed_symbols]
        if not candidates:
            return self._hold_proposal(snapshots, "Fallback analyst: no allowed symbols are present in market snapshots.")
        buy_candidates = [snapshot for snapshot in candidates if self._is_fallback_buy_candidate(snapshot)]
        if not buy_candidates:
            observed = "; ".join(f"{item.symbol}: trend={item.trend_regime}, RSI={item.rsi14}" for item in candidates)
            return self._hold_proposal(
                snapshots,
                "Fallback analyst: no allowed symbol passed conservative BUY filters. Observed: " + observed,
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
                f"Fallback analyst: {best.symbol} passed conservative filters "
                f"(trend={best.trend_regime}, RSI={best.rsi14}, price above EMA200)."
            ),
        )

    def _openai_compatible_proposal(self, snapshots: list[MarketSnapshot], live_positions: LivePositionSummary | None) -> TradeProposal:
        ai_config = self.config["ai"]
        base_url = os.getenv(ai_config["base_url_env"], "").rstrip("/")
        api_key = os.getenv(ai_config["api_key_env"], "")
        model = os.getenv(ai_config["model_env"], "qwen3:14b")
        if not base_url:
            return self._mock_proposal(snapshots)

        prompt = {
            "task": "Return one conservative spot trade proposal as JSON only.",
            "allowed_actions": ["BUY", "SELL", "HOLD"],
            "allowed_symbols": self.config.get("strategy", {}).get("allowed_symbols", []),
            "guardrails": [
                "Prefer HOLD when market context is unclear.",
                "Do not propose symbols outside allowed_symbols.",
                "Use BUY only for a clearly favorable setup; execution still requires deterministic guards.",
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
            "schema": {
                "symbol": str(self.config.get("strategy", {}).get("allowed_symbols", ["BTCUSDT"])[0]),
                "action": "BUY",
                "confidence": 0.65,
                "quote_amount_usdt": 25,
                "stop_loss_pct": 1.5,
                "take_profit_pct": 3.0,
                "reason": "short explanation",
            },
        }
        content = self._chat_json(
            system="You are a cautious crypto market analyst. Output JSON only.",
            user=json.dumps(prompt, default=str),
        )
        data = json.loads(content)
        return TradeProposal(
            symbol=str(data["symbol"]).upper(),
            action=str(data["action"]).upper(),
            confidence=Decimal(str(data["confidence"])),
            quote_amount_usdt=Decimal(str(data["quote_amount_usdt"])),
            stop_loss_pct=Decimal(str(data["stop_loss_pct"])),
            take_profit_pct=Decimal(str(data["take_profit_pct"])),
            reason=str(data["reason"]),
        )

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
            raise RuntimeError("LLM_BASE_URL is not set.")

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
