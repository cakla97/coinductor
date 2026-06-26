from __future__ import annotations

import json
import os
import unicodedata
import urllib.request

from trading_agent.config import load_config
from trading_agent.env import load_env_file

from .ai_provider import AiProviderService
from .models import DesktopSnapshot


class LocalHelpAssistant:
    def answer(self, question: str, snapshot: DesktopSnapshot) -> str:
        query = "".join(
            character
            for character in unicodedata.normalize("NFKD", question.strip().lower())
            if not unicodedata.combining(character)
        )
        if not query:
            return "Ask about the latest run, portfolio roles, risk controls, Grid, Rebalancing, or where data is stored."
        latest = snapshot.latest_run
        if any(word in query for word in ("last run", "latest run", "poslední", "dnes", "provedl")):
            if latest is None:
                return "No completed real-data run is available yet."
            top_action = latest.actions[0].action if latest.actions else "No follow-up action was recorded."
            return (
                f"Run {latest.run_id} ended with {latest.decision}. {latest.decision_summary} "
                f"Highest-priority follow-up: {top_action}"
            )
        if any(word in query for word in ("risk", "bezpe", "guard", "limit")):
            return (
                "Coinductor keeps execution deterministic: AI cannot bypass symbol allowlists, protected assets, "
                "position limits, daily/weekly loss limits, cooldowns, liquidity checks, or explicit submit confirmations."
            )
        if "grid" in query:
            strategy = next((item for item in snapshot.strategies if item["type"] == "Spot Grid"), None)
            return strategy["detail"] if strategy else "No Grid recommendation is stored for the latest real run."
        if any(word in query for word in ("rebalanc", "koš", "basket")):
            strategy = next((item for item in snapshot.strategies if item["type"] == "Rebalancing"), None)
            return strategy["detail"] if strategy else "No Rebalancing recommendation is stored for the latest real run."
        if any(word in query for word in ("portfolio", "asset", "token", "coin")):
            if not snapshot.portfolio_assets:
                return "Portfolio data is not loaded."
            top = ", ".join(
                f"{item['asset']} {item['allocation']}" for item in snapshot.portfolio_assets[:5]
            )
            return f"Largest assets in the latest real run: {top}. Open Portfolio for role and liquidity details."
        if any(word in query for word in ("report", "file", "database", "sqlite", "kde")):
            return (
                "Detailed reports are in outputs/reports and structured history is in work/trading_agent.sqlite3. "
                "Use Open detailed report from Overview for the latest real run."
            )
        return (
            "I am currently the offline project-help assistant. I can explain the latest run, portfolio, risk controls, "
            "Grid/Rebalancing recommendations, and local data locations. Configure an AI provider in Settings for broader read-only Q&A."
        )


class ProviderBackedAssistant:
    def __init__(
        self,
        config_path: str = "config.example.toml",
        env_path: str = ".env",
        fallback: LocalHelpAssistant | None = None,
    ):
        self.config_path = config_path
        self.env_path = env_path
        self.fallback = fallback or LocalHelpAssistant()

    def answer(self, question: str, snapshot: DesktopSnapshot) -> str:
        try:
            return self._provider_answer(question, snapshot)
        except Exception as exc:
            offline = self.fallback.answer(question, snapshot)
            return f"{offline}\n\nAI provider fallback: {exc}"

    def _provider_answer(self, question: str, snapshot: DesktopSnapshot) -> str:
        load_env_file(self.env_path)
        config = load_config(self.config_path).raw
        ai = config.get("ai", {})
        base_url = os.getenv(str(ai.get("base_url_env", "LLM_BASE_URL")), "").rstrip("/")
        api_key = os.getenv(str(ai.get("api_key_env", "LLM_API_KEY")), "")
        model = os.getenv(str(ai.get("model_env", "LLM_MODEL")), "")
        if not base_url:
            raise RuntimeError("LLM_BASE_URL is not set.")
        if not model:
            raise RuntimeError("LLM_MODEL is not set.")

        payload = {
            "task": "Answer a user question about Coinductor in a concise, read-only way.",
            "strict_boundaries": [
                "Do not claim that you changed settings, placed orders, redeemed Earn, or created Binance bots.",
                "Do not provide financial guarantees.",
                "Do not invent live market prices. If asked for current prices and no market-data payload is present, explain that this milestone cannot fetch standalone live prices yet.",
                "If the user asks to change app state, explain that command intents are planned and require deterministic validation plus confirmation.",
                "Use only the supplied context. Say when data is unavailable.",
            ],
            "project_context": AiProviderService(self.config_path, self.env_path).inspect().context_sections,
            "snapshot": self._snapshot_payload(snapshot),
            "question": question,
            "schema": {"answer": "plain-language answer, max 180 words"},
        }
        body = json.dumps(
            {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are Coinductor's read-only assistant. You explain the app, reports, portfolio state, "
                            "risk controls, and setup. You cannot execute actions. Return JSON only."
                        ),
                    },
                    {"role": "user", "content": json.dumps(payload, default=str)},
                ],
                "temperature": 0.2,
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
        with urllib.request.urlopen(request, timeout=int(ai.get("timeout_seconds", 60))) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
        content = str(response_payload["choices"][0]["message"]["content"])
        data = json.loads(content)
        answer = str(data.get("answer", "")).strip()
        if not answer:
            raise RuntimeError("AI provider returned an empty answer.")
        return answer

    def _snapshot_payload(self, snapshot: DesktopSnapshot) -> dict:
        latest = snapshot.latest_run
        return {
            "latest_run": {
                "run_id": latest.run_id,
                "status": latest.status,
                "decision": latest.decision,
                "decision_summary": latest.decision_summary,
                "risk_approved": latest.risk_approved,
                "risk_reason": latest.risk_reason,
                "portfolio_value": str(latest.portfolio_value),
                "liquid_value": str(latest.liquid_value),
                "locked_value": str(latest.locked_value),
                "ai_summary": latest.ai_summary,
                "actions": [item.__dict__ for item in latest.actions],
                "report_path": latest.report_path,
            }
            if latest is not None
            else None,
            "portfolio_assets": list(snapshot.portfolio_assets[:12]),
            "strategies": list(snapshot.strategies),
            "run_history": list(snapshot.run_history[:10]),
        }
