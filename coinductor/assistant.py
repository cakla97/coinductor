from __future__ import annotations

import unicodedata

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
            "Grid/Rebalancing recommendations, and local data locations. External or local LLM providers arrive in the next AI milestone."
        )
