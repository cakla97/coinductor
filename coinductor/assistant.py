from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import unicodedata
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from trading_agent.config import load_config
from trading_agent.env import load_env_file

from .ai_provider import AiProviderService
from .models import DesktopSnapshot
from .ui_knowledge import UiKnowledgeService, is_czech


@dataclass(frozen=True)
class AssistantResponse:
    text: str
    proposed_action: dict[str, object] | None = None


class ContextualHelpService:
    def answer(self, question: str, app_context: dict[str, object]) -> str | None:
        query = _normalize(question)
        czech = is_czech(question)
        page_name = str(app_context.get("context_page", "AI Assistant"))

        if any(
            phrase in query
            for phrase in (
                "binance not checked", "box binance", "binance status", "stav binance",
                "binance v levem spodnim", "binance vlevo dole",
            )
        ):
            connection = app_context.get("binance_read_only", {})
            status = str(connection.get("status", "Not checked"))
            detail = str(connection.get("detail", ""))
            if czech:
                return (
                    f"Box BINANCE ukazuje stav read-only API připojení v aktuální session. Stav {status} znamená, "
                    "že aplikace zatím nespustila nebo nedokončila síťovou kontrolu read-only klíče; sám o sobě "
                    "neříká, že klíč chybí nebo je neplatný. Kontrolu spustíte v Settings v části Binance read-only "
                    f"connection. Aktuální detail aplikace: {detail}"
                )
            return (
                f"The BINANCE box shows the read-only API connection state for this app session. {status} means "
                "the read-only key has not yet completed a network check; it does not by itself mean the key is "
                f"missing or invalid. Run the check in Settings > Binance read-only connection. Current detail: {detail}"
            )

        if any(
            phrase in query
            for phrase in ("o sobe reknes", "kdo jsi", "co umis", "who are you", "about yourself", "what can you do")
        ):
            summary = UiKnowledgeService().page_summary("AI Assistant", czech=czech)
            if summary is not None:
                return summary

        if any(
            phrase in query
            for phrase in (
                "shrn tuto stranku", "shrn tuhle stranku", "shrn tuto sekci", "co je tady",
                "co je na teto strance", "summarize this page", "summarize this section", "what is on this page",
            )
        ):
            summary = UiKnowledgeService().page_summary(page_name, czech=czech)
            if summary is not None:
                return summary

        if any(
            phrase in query
            for phrase in (
                "brani obchodu", "blokuje obchod", "proc je trade hold", "proc je obchod hold",
                "what blocks the trade", "why is the trade hold", "why is trading blocked",
            )
        ):
            trade = next(
                (
                    item
                    for item in app_context.get("action_plan", [])
                    if str(item.get("title", "")) == "Trade"
                ),
                None,
            )
            if trade is None:
                return "Trade zatím nebyl vyhodnocen." if czech else "Trade has not been evaluated yet."
            status = str(trade.get("status", "Unknown"))
            detail = str(trade.get("detail", "No detail is available."))
            submit_blocker = str(trade.get("submitBlockedReason", "")).strip()
            if czech:
                response = f"Aktuální stav Trade je {status}. Důvod z posledního běhu: {detail}"
                if submit_blocker:
                    response += f" Live odeslání navíc blokuje: {submit_blocker}"
                return response
            response = f"The current Trade status is {status}. Latest-run reason: {detail}"
            if submit_blocker:
                response += f" Live submission is also blocked by: {submit_blocker}"
            return response

        if any(
            phrase in query
            for phrase in (
                "co mam udelat dal", "jaky je dalsi krok", "co je dalsi krok", "what should i do next",
                "what is the next step", "next step here",
            )
        ):
            readiness = app_context.get("readiness", {})
            next_step = str(readiness.get("next_step", "")).strip()
            action_label = str(readiness.get("action_label", "")).strip()
            if not next_step:
                return "Aplikace nyní nemá uložený jednoznačný další krok." if czech else "The app has no single stored next step right now."
            if czech:
                suffix = f" Doporučená akce v UI: {action_label}." if action_label else ""
                return f"Podle aktuální readiness je další krok: {next_step}{suffix}"
            suffix = f" Recommended UI action: {action_label}." if action_label else ""
            return f"According to current readiness, the next step is: {next_step}{suffix}"
        return None

    def proposed_action(self, question: str, app_context: dict[str, object]) -> dict[str, object] | None:
        query = _normalize(question)
        if any(
            phrase in query
            for phrase in ("binance not checked", "box binance", "binance status", "stav binance")
        ):
            czech = is_czech(question)
            return {
                "type": "NAVIGATE",
                "title": "Otevřít Settings" if czech else "Open Settings",
                "description": (
                    "Přejde k Binance read-only connection kontrole. Samotný přechod žádnou kontrolu nespustí."
                    if czech
                    else "Navigate to the Binance read-only connection check. Navigation does not run the check."
                ),
                "confirmLabel": "Otevřít Settings" if czech else "Open Settings",
                "page": 8,
            }
        if not any(
            phrase in query
            for phrase in (
                "co mam udelat dal", "jaky je dalsi krok", "co je dalsi krok", "what should i do next",
                "what is the next step", "next step here",
            )
        ):
            return None
        readiness = app_context.get("readiness", {})
        code = str(readiness.get("action_code", ""))
        page = {
            "GUIDE_PROFILE": 8,
            "CHECK_BINANCE": 8,
            "OPEN_SETTINGS": 8,
            "RUN_CLASSIFICATION": 0,
            "OPEN_PORTFOLIO": 2,
        }.get(code)
        if page is None:
            return None
        label = {0: "Overview", 2: "Portfolio", 8: "Settings"}[page]
        czech = is_czech(question)
        return {
            "type": "NAVIGATE",
            "title": f"Otevřít {label}" if czech else f"Open {label}",
            "description": (
                f"Přejde do sekce {label}, kde můžete doporučený krok zkontrolovat. Nic se neprovede automaticky."
                if czech
                else f"Navigate to {label} so you can review the recommended step. Nothing is executed automatically."
            ),
            "confirmLabel": "Otevřít sekci" if czech else "Open page",
            "page": page,
        }


class AssistantIntentService:
    _PAGES = {
        "overview": (0, "Overview"),
        "prehled": (0, "Overview"),
        "live actions": (1, "Live Actions"),
        "live akce": (1, "Live Actions"),
        "portfolio": (2, "Portfolio"),
        "action plan": (3, "Action Plan"),
        "akcni plan": (3, "Action Plan"),
        "active strategies": (4, "Active Strategies"),
        "aktivni strategie": (4, "Active Strategies"),
        "run history": (5, "Run History"),
        "historie behu": (5, "Run History"),
        "help": (7, "Help & Guides"),
        "navody": (7, "Help & Guides"),
        "settings": (8, "Settings"),
        "nastaveni": (8, "Settings"),
    }
    _ROLE_ALIASES = {
        "system default": "SYSTEM_DEFAULT",
        "default": "SYSTEM_DEFAULT",
        "protected core": "PROTECTED_CORE",
        "protected utility": "PROTECTED_UTILITY",
        "trading allowed": "TRADING_ALLOWED",
        "trading": "TRADING_ALLOWED",
        "grid candidate": "GRID_CANDIDATE",
        "grid": "GRID_CANDIDATE",
        "rebalancing candidate": "REBALANCING_CANDIDATE",
        "rebalancing": "REBALANCING_CANDIDATE",
        "funding source": "FUNDING_SOURCE",
        "funding": "FUNDING_SOURCE",
        "dust airdrop funding": "DUST_AIRDROP_FUNDING",
        "dust": "DUST_AIRDROP_FUNDING",
        "active strategy": "ACTIVE_STRATEGY",
        "stable": "STABLE",
        "unclassified": "UNCLASSIFIED",
    }

    def propose(self, question: str, snapshot: DesktopSnapshot) -> AssistantResponse | None:
        query = _normalize(question)
        if self._requests_live_execution(query):
            return AssistantResponse(
                "I cannot prepare or execute BUY, SELL, OCO, Earn redeem, or other live actions from chat. "
                "Use Action Plan and Live Actions, where deterministic checks and a separate confirmation remain mandatory."
            )

        if self._has_command_verb(query):
            for page_name, (page, label) in self._PAGES.items():
                if page_name in query:
                    return AssistantResponse(
                        f"I can open {label} for you.",
                        {
                            "type": "NAVIGATE",
                            "title": f"Open {label}",
                            "description": f"Navigate to the {label} page. This does not change portfolio or exchange state.",
                            "confirmLabel": "Open page",
                            "page": page,
                        },
                    )

        if self._requests_report(query):
            if snapshot.latest_run is None or not snapshot.latest_run.report_path:
                return AssistantResponse("No detailed report is available yet.")
            return AssistantResponse(
                "The latest detailed report is available locally.",
                {
                    "type": "OPEN_REPORT",
                    "title": "Open latest detailed report",
                    "description": "Open the local report generated by the latest completed real-data run.",
                    "confirmLabel": "Open report",
                },
            )

        if self._requests_analysis(query):
            return AssistantResponse(
                "I can start a fresh real-data analysis. It may prepare recommendations, but live preview and submission stay off.",
                {
                    "type": "RUN_READ_ONLY_ANALYSIS",
                    "title": "Run read-only analysis",
                    "description": "Refresh market and portfolio data, AI commentary, and bounded recommendations without previewing or submitting an order.",
                    "confirmLabel": "Run analysis",
                },
            )

        role_action = self._role_action(query, snapshot)
        if role_action is not None:
            return role_action
        return None

    def _role_action(self, query: str, snapshot: DesktopSnapshot) -> AssistantResponse | None:
        if not any(word in query for word in ("role", "policy", "reclass", "classif", "presun", "zmen", "nastav")):
            return None
        assets = {str(item.get("asset", "")).upper() for item in snapshot.portfolio_assets}
        asset = next((item for item in sorted(assets, key=len, reverse=True) if re.search(rf"\b{re.escape(item.lower())}\b", query)), "")
        role = next((value for alias, value in self._ROLE_ALIASES.items() if alias in query), "")
        if not asset or not role:
            return AssistantResponse(
                "To prepare a role change, name one asset from the loaded portfolio and one exact role, for example: "
                "Change BNB role to Grid candidate."
            )
        label = role.replace("_", " ").title()
        return AssistantResponse(
            f"I can change {asset} to the {label} role after confirmation.",
            {
                "type": "SET_ASSET_ROLE",
                "title": f"Change {asset} role",
                "description": f"Set the local portfolio policy override for {asset} to {label}. No Binance order is placed.",
                "confirmLabel": "Change role",
                "asset": asset,
                "role": role,
            },
        )

    def _requests_live_execution(self, query: str) -> bool:
        return any(
            phrase in query
            for phrase in (
                "buy ", "sell ", "koup", "prodej", "execute trade", "proved trade",
                "place order", "submit order", "oco", "redeem", "vyber z earn", "convert ",
            )
        )

    def _has_command_verb(self, query: str) -> bool:
        return any(word in query for word in ("open", "show", "go to", "navigate", "otevr", "ukaz", "prejdi"))

    def _requests_report(self, query: str) -> bool:
        return self._has_command_verb(query) and any(word in query for word in ("report", "zpravu", "vysledek behu"))

    def _requests_analysis(self, query: str) -> bool:
        return any(
            phrase in query
            for phrase in ("run analysis", "start analysis", "spust analyzu", "proved analyzu", "novou analyzu")
        )


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

    def answer(
        self,
        question: str,
        snapshot: DesktopSnapshot,
        app_context: dict[str, object] | None = None,
        conversation: tuple[dict[str, str], ...] = (),
        image_path: str = "",
    ) -> str:
        try:
            return self._provider_answer(question, snapshot, app_context or {}, conversation, image_path)
        except Exception as exc:
            if is_czech(question):
                return (
                    "Lokální AI model tentokrát nevrátil použitelnou odpověď. "
                    "Zdokumentované funkce aplikace mohu vysvětlit přímo; u obecného dotazu jej zkuste formulovat konkrétněji. "
                    f"Technický detail: {exc}"
                )
            offline = self.fallback.answer(question, snapshot)
            return f"{offline}\n\nAI provider fallback: {exc}"

    def respond(
        self,
        question: str,
        snapshot: DesktopSnapshot,
        app_context: dict[str, object] | None = None,
        conversation: tuple[dict[str, str], ...] = (),
        image_path: str = "",
    ) -> AssistantResponse:
        deterministic = AssistantIntentService().propose(question, snapshot)
        if deterministic is not None:
            return deterministic
        contextual = ContextualHelpService().answer(question, app_context or {})
        if contextual is not None:
            proposal = ContextualHelpService().proposed_action(question, app_context or {})
            return AssistantResponse(contextual, proposal)
        ui_answer = UiKnowledgeService().answer(question)
        if ui_answer is not None:
            return AssistantResponse(ui_answer)
        return AssistantResponse(self.answer(question, snapshot, app_context, conversation, image_path))

    def _provider_answer(
        self,
        question: str,
        snapshot: DesktopSnapshot,
        app_context: dict[str, object],
        conversation: tuple[dict[str, str], ...],
        image_path: str,
    ) -> str:
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
        if image_path:
            vision_available, vision_detail = AiProviderService(self.config_path, self.env_path).vision_support()
            if not vision_available:
                raise RuntimeError(vision_detail)

        response_language = "Czech" if is_czech(question) else "English"
        payload = {
            "task": "Answer a user question about Coinductor in a concise, read-only way.",
            "response_language": response_language,
            "strict_boundaries": [
                f"Answer exclusively in {response_language}; do not mix languages except exact UI labels and technical identifiers.",
                "Do not claim that you changed settings, placed orders, redeemed Earn, or created Binance bots.",
                "Do not provide financial guarantees.",
                "Do not invent live market prices. If asked for current prices and no market-data payload is present, explain that this milestone cannot fetch standalone live prices yet.",
                "For documented UI behavior, answer directly from ui_component_catalog. Never hedge with likely, probably, may, or might.",
                "If a component is absent from the catalog, say that its exact behavior is not in the supplied context instead of guessing.",
                "If the user asks to change app state, explain that supported command intents require deterministic validation plus confirmation.",
                "Use only the supplied context. Say when data is unavailable.",
            ],
            "project_context": AiProviderService(self.config_path, self.env_path).inspect().context_sections,
            "ui_component_catalog": UiKnowledgeService().context(),
            "current_app_context": app_context,
            "recent_conversation": list(conversation[-8:]),
            "snapshot": self._snapshot_payload(snapshot),
            "question": question,
            "image_attached": bool(image_path),
            "schema": {"answer": "plain-language answer, max 180 words"},
        }
        user_content: str | list[dict[str, object]] = json.dumps(payload, default=str)
        if image_path:
            image_file = Path(image_path)
            if not image_file.is_file() or image_file.stat().st_size > 10 * 1024 * 1024:
                raise RuntimeError("The attached image is missing or exceeds the 10 MB limit.")
            mime_type = mimetypes.guess_type(image_file.name)[0] or "image/png"
            encoded = base64.b64encode(image_file.read_bytes()).decode("ascii")
            user_content = [
                {"type": "text", "text": json.dumps(payload, default=str)},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded}"}},
            ]
        body = json.dumps(
            {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are Coinductor's read-only assistant. You explain the app, reports, portfolio state, "
                            "risk controls, and setup from supplied authoritative context. Match the user's language exactly, "
                            "never guess undocumented behavior, and never use uncertain wording for catalogued controls. "
                            "You cannot execute actions. Return JSON only."
                        ),
                    },
                    {"role": "user", "content": user_content},
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


def _normalize(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value.strip().lower())
        if not unicodedata.combining(character)
    )
