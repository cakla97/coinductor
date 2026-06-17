from __future__ import annotations

from decimal import Decimal
import json
import os
import urllib.request

from .models import ActiveStrategiesReport, AiCommentary, CapitalSourcingPlan, GridRecommendation, MarketSnapshot, NextRunRecommendation, PortfolioAnalysis, RecommendedAction, ResearchBundle, ResearchStatus, RiskDecision, StrategyDecision, TradeProposal


class AiAnalyst:
    def __init__(self, config: dict):
        self.config = config

    def propose_trade(self, snapshots: list[MarketSnapshot]) -> TradeProposal:
        ai_config = self.config.get("ai", {})
        if not ai_config.get("enabled", False):
            return self._mock_proposal(snapshots)
        return self._openai_compatible_proposal(snapshots)

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
        best = next((item for item in snapshots if item.symbol == "BTCUSDT"), snapshots[0])
        orders = self.config["orders"]
        return TradeProposal(
            symbol=best.symbol,
            action="BUY",
            confidence=Decimal("0.68"),
            quote_amount_usdt=Decimal(str(self.config["strategy"]["quote_amount_usdt"])),
            stop_loss_pct=Decimal(str(orders["default_stop_loss_pct"])),
            take_profit_pct=Decimal(str(orders["default_take_profit_pct"])),
            reason="Mock analyst: trend regime is RISK_ON and BTC is above long-term trend filter.",
        )

    def _openai_compatible_proposal(self, snapshots: list[MarketSnapshot]) -> TradeProposal:
        ai_config = self.config["ai"]
        base_url = os.getenv(ai_config["base_url_env"], "").rstrip("/")
        api_key = os.getenv(ai_config["api_key_env"], "")
        model = os.getenv(ai_config["model_env"], "qwen3:14b")
        if not base_url:
            return self._mock_proposal(snapshots)

        prompt = {
            "task": "Return one conservative spot trade proposal as JSON only.",
            "allowed_actions": ["BUY", "SELL", "HOLD"],
            "snapshots": [snapshot.__dict__ for snapshot in snapshots],
            "schema": {
                "symbol": "BTCUSDT",
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
