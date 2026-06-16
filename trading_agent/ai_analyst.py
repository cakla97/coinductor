from __future__ import annotations

from decimal import Decimal
import json
import os
import urllib.request

from .models import MarketSnapshot, TradeProposal


class AiAnalyst:
    def __init__(self, config: dict):
        self.config = config

    def propose_trade(self, snapshots: list[MarketSnapshot]) -> TradeProposal:
        ai_config = self.config.get("ai", {})
        if not ai_config.get("enabled", False):
            return self._mock_proposal(snapshots)
        return self._openai_compatible_proposal(snapshots)

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
        body = json.dumps(
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a cautious crypto market analyst. Output JSON only."},
                    {"role": "user", "content": json.dumps(prompt, default=str)},
                ],
                "temperature": 0.2,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=int(ai_config.get("timeout_seconds", 60))) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = payload["choices"][0]["message"]["content"]
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

