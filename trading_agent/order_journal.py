from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import hashlib
import json

from .models import RiskDecision, TradeProposal


class OrderIntentFactory:
    def __init__(self, config: dict):
        self.config = config

    def spot_intent_id(self, proposal: TradeProposal, risk_decision: RiskDecision) -> str:
        payload = {
            "window": self._window_value(),
            "kind": "SPOT",
            "symbol": proposal.symbol,
            "action": proposal.action,
            "quote_amount_usdt": str(risk_decision.adjusted_quote_amount_usdt),
            "stop_loss_pct": str(proposal.stop_loss_pct),
            "take_profit_pct": str(proposal.take_profit_pct),
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()[:24]

    def _window_value(self) -> str:
        window = str(self.config.get("paper", {}).get("idempotency_window", "daily")).lower()
        now = datetime.now()
        if window == "none":
            return now.strftime("%Y-%m-%dT%H:%M:%S")
        if window == "hourly":
            return now.strftime("%Y-%m-%dT%H")
        return now.strftime("%Y-%m-%d")

