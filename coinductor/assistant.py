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
from urllib.parse import urlparse

from trading_agent.binance_client import BinanceApiError, BinanceClient
from trading_agent.config import default_config_path, load_config

from .ai_provider import AiProviderService, _describe_provider_error  # noqa: F401
from .guide_service import GuideService
from .models import DesktopSnapshot
from .secret_store import load_secrets
from .service_strings import service_text
from .ui_knowledge import UiKnowledgeService, is_czech


def _fold(value: str) -> str:
    """Lowercase and strip diacritics, so "poslední" matches "posledni"."""
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value.strip().lower())
        if not unicodedata.combining(character)
    )


@dataclass(frozen=True)
class AssistantResponse:
    text: str
    proposed_action: dict[str, object] | None = None


# Letters that exist in Slovak but never in Czech, plus common Slovak function
# words with no Czech spelling. Used to catch a model drifting into Slovak on a
# Czech question, which instructions alone do not reliably prevent.
_SLOVAK_ONLY_LETTERS = "ôľŕĺä"
_SLOVAK_ONLY_WORDS = frozenset(
    {
        "nie", "sú", "aj", "iba", "ktorý", "ktoré", "ktorá", "ktorých",
        "môže", "podľa", "veľmi", "žiadne", "žiadny", "odporúčané", "súčasnosti",
    }
)


def looks_slovak(text: str) -> bool:
    """Heuristic: does this Czech-intended answer read as Slovak?

    Conservative on purpose - a false positive costs one extra request, while a
    false negative shows the user the wrong language.
    """
    if not text:
        return False
    lowered = text.lower()
    if any(letter in lowered for letter in _SLOVAK_ONLY_LETTERS):
        return True
    words = {word.strip(".,;:!?()\"'") for word in lowered.split()}
    return len(words & _SLOVAK_ONLY_WORDS) >= 2


def _open_guide_action(guide_id: str, czech: bool) -> dict[str, object] | None:
    if not guide_id:
        return None
    title = next(
        (guide["title"] for guide in GuideService().list_guides() if guide["id"] == guide_id),
        "",
    )
    if not title:
        return None
    return {
        "type": "OPEN_GUIDE",
        "title": (f"Otevřít návod: {title}" if czech else f"Open guide: {title}"),
        "description": (
            "Otevře podrobný návod k této části aplikace v sekci Help & Guides."
            if czech
            else "Opens the detailed guide for this part of the app in Help & Guides."
        ),
        "confirmLabel": "Otevřít návod" if czech else "Open guide",
        "guide_id": guide_id,
    }


# Pure pleasantries. Matched only when the message contains nothing else, so
# "Ahoj, jak funguje Grid?" still reaches the real answer path.
_GREETING_PHRASES_CS = ("dobry den", "dobre rano", "dobry vecer", "jak se mas", "jak se mate", "ahoj", "cau", "cus", "zdravim", "nazdar")
_GREETING_PHRASES_EN = ("hello", "hi", "hey", "good morning", "good afternoon", "good evening", "how are you", "whats up")
_THANKS_PHRASES_CS = ("dekuji", "dekuju", "diky", "dik")
_THANKS_PHRASES_EN = ("thanks", "thank you", "thx", "cheers")
_GREETING_PHRASES = _GREETING_PHRASES_CS + _GREETING_PHRASES_EN
_THANKS_PHRASES = _THANKS_PHRASES_CS + _THANKS_PHRASES_EN
_CZECH_SMALL_TALK = frozenset(_GREETING_PHRASES_CS + _THANKS_PHRASES_CS)
# Words that may surround a greeting without turning it into a question.
_SMALL_TALK_FILLER = frozenset({
    "a", "ty", "tobe", "vam", "te", "se", "moc", "vsem", "pekne", "mockrat",
    "there", "you", "so", "much", "very", "ok", "okay", "again", "all",
})


def _small_talk_kind(query: str) -> tuple[str, bool] | None:
    """(kind, is_czech) or None when the message carries real content.

    The language comes from the phrase that matched: is_czech() keys off Czech
    letters and words, so a bare "Ahoj" would otherwise be answered in English.
    """
    stripped = re.sub(r"[^\w\s]", " ", query)
    remainder = f" {stripped} "
    matched_thanks = False
    matched_greeting = False
    czech = False
    # Longest first so "jak se mas" is consumed before "ahoj"-style fragments.
    for phrase in sorted(_THANKS_PHRASES + _GREETING_PHRASES, key=len, reverse=True):
        padded = f" {phrase} "
        if padded in remainder:
            remainder = remainder.replace(padded, " ")
            if phrase in _THANKS_PHRASES:
                matched_thanks = True
            else:
                matched_greeting = True
            if phrase in _CZECH_SMALL_TALK:
                czech = True
    if not (matched_thanks or matched_greeting):
        return None
    # Anything left that is not filler means the user asked something as well.
    if any(word not in _SMALL_TALK_FILLER for word in remainder.split()):
        return None
    kind = "thanks" if matched_thanks and not matched_greeting else "greeting"
    return kind, czech


class ContextualHelpService:
    def answer(self, question: str, app_context: dict[str, object]) -> str | None:
        query = _normalize(question)
        czech = is_czech(question)
        page_name = str(app_context.get("context_page", "AI Assistant"))

        # Meta question about language. Answered deterministically so it never
        # reaches the model, which otherwise treats it as a portfolio question.
        # Matched on stems so both "česky" and "v češtině" are covered, in
        # questions ("můžu s tebou mluvit...") and imperatives ("mluv česky").
        language_mentioned = any(stem in query for stem in ("cesky", "cestin", "czech"))
        language_context = any(
            word in query
            for word in (
                "mluv", "povid", "odpovid", "umis", "umite", "bavit", "dorozum", "rozumis",
                "komunik", "pis ", "napis", "speak", "talk", "answer", "write", "reply",
            )
        )
        if language_mentioned and language_context:
            if czech:
                return (
                    "Ano, můžeme se bavit česky. Ptejte se česky a odpovím česky. "
                    "Jazyk rozhraní aplikace přepnete v Nastavení přepínačem Jazyk aplikace."
                )
            return (
                "Yes, I can answer in Czech. Ask in Czech and I will reply in Czech. "
                "The app interface language is switched in Settings under App language."
            )

        # Pleasantries would otherwise fall through to the model together with
        # the portfolio prompt, which tells it to answer from that context - so
        # "Jak se mas?" came back as a lecture about HOLD strategies.
        small_talk = _small_talk_kind(query)
        if small_talk is not None:
            kind, small_talk_czech = small_talk
            czech = czech or small_talk_czech
        if small_talk is not None and kind == "thanks":
            return (
                "Rádo se stalo. Kdyby bylo potřeba cokoliv dalšího, stačí se zeptat."
                if czech
                else "You're welcome. Ask any time if you need something else."
            )
        if small_talk is not None and kind == "greeting":
            if czech:
                return (
                    "Zdravím, mám se dobře. Jsem asistent Coinductoru pro čtení a vysvětlování. "
                    "Zeptejte se třeba na poslední běh, role v portfoliu, bezpečnostní fáze nebo na to, "
                    "co dělá konkrétní obrazovka."
                )
            return (
                "Hello, I'm doing well. I'm Coinductor's read-only assistant. "
                "Ask me about the latest run, portfolio roles, safety stages, or what a particular screen does."
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
        "ai assistant": (6, "AI Assistant"),
        "asistent": (6, "AI Assistant"),
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
        # "role"/"classif" name the feature outright. The verbs below do not:
        # "nastav" matches any Czech phrasing about settings, so on its own it
        # made unrelated questions ("je to dobre nastavene?") return canned
        # role-change instructions instead of falling through to a real answer.
        names_feature = any(word in query for word in ("role", "policy", "reclass", "classif"))
        verb_only = any(word in query for word in ("presun", "zmen", "nastav"))
        if not (names_feature or verb_only):
            return None
        assets = {str(item.get("asset", "")).upper() for item in snapshot.portfolio_assets}
        asset = next((item for item in sorted(assets, key=len, reverse=True) if re.search(rf"\b{re.escape(item.lower())}\b", query)), "")
        role = next((value for alias, value in self._ROLE_ALIASES.items() if alias in query), "")
        if not asset or not role:
            # Only claim the question when a role change was plainly intended;
            # otherwise let the rest of the pipeline answer it.
            if not (names_feature or asset or role):
                return None
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


class MarketDataAssistant:
    """Deterministic, standalone market-data answers backed by Binance public endpoints.

    This never runs a full analysis and never requires Binance API credentials
    (public endpoints are unauthenticated). It only answers a narrow, recognized
    question shape; anything else falls through to the next assistant layer.
    """

    _ASSET_ALIASES = {
        "btc": "BTC",
        "bitcoin": "BTC",
        "eth": "ETH",
        "ethereum": "ETH",
        "ether": "ETH",
        "wbeth": "WBETH",
        "bnb": "BNB",
        "binance coin": "BNB",
        "sol": "SOL",
        "solana": "SOL",
        "wld": "WLD",
        "worldcoin": "WLD",
        "pepe": "PEPE",
        "ada": "ADA",
        "cardano": "ADA",
        "doge": "DOGE",
        "dogecoin": "DOGE",
        "dot": "DOT",
        "polkadot": "DOT",
    }
    _TRIGGER_WORDS = (
        "price", "cena", "kolik stoji", "jak si vede", "how is",
        "co dela", "trend", "kurz", "hodnota", "how much is",
    )

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or default_config_path()

    def answer(self, question: str, snapshot: DesktopSnapshot) -> AssistantResponse | None:
        query = _normalize(question)
        if not any(word in query for word in self._TRIGGER_WORDS):
            return None
        asset = self._match_asset(query)
        if asset is None:
            return None
        czech = is_czech(question)
        try:
            symbol, quote, ticker = self._fetch(asset)
        except Exception as exc:
            return AssistantResponse(
                f"Nepodařilo se načíst aktuální data pro {asset} z veřejného Binance API: {exc}"
                if czech
                else f"Could not fetch current data for {asset} from the Binance public API: {exc}"
            )
        last_price = str(ticker.get("lastPrice", "?"))
        change_pct = str(ticker.get("priceChangePercent", "?"))
        high = str(ticker.get("highPrice", "?"))
        low = str(ticker.get("lowPrice", "?"))
        if czech:
            text = (
                f"{asset} ({symbol}): aktuální cena {last_price} {quote}, změna za 24h {change_pct} %, "
                f"rozpětí 24h {low} - {high} {quote}. Zdroj: veřejné Binance API, samostatný dotaz mimo "
                f"plný běh. Toto není obchodní doporučení."
            )
        else:
            text = (
                f"{asset} ({symbol}): current price {last_price} {quote}, 24h change {change_pct}%, "
                f"24h range {low} - {high} {quote}. Source: Binance public API, standalone lookup "
                f"outside a full run. This is not a trade recommendation."
            )
        return AssistantResponse(text)

    def _match_asset(self, query: str) -> str | None:
        for alias, asset in sorted(self._ASSET_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
            if re.search(rf"\b{re.escape(alias)}\b", query):
                return asset
        return None

    def _fetch(self, asset: str) -> tuple[str, str, dict]:
        load_secrets()
        config = load_config(self.config_path).raw
        client = BinanceClient(config)
        quote_assets = [str(item).upper() for item in config.get("portfolio", {}).get("pricing_quote_assets", ["USDC", "USDT"])]
        last_error: Exception | None = None
        for quote in quote_assets:
            if quote == asset:
                continue
            symbol = f"{asset}{quote}"
            try:
                ticker = client.get_symbol_market_snapshot(symbol)
                return symbol, quote, ticker
            except BinanceApiError as exc:
                last_error = exc
                continue
        raise last_error or BinanceApiError(f"No tradable pair was found for {asset}.")


class LocalHelpAssistant:
    """The built-in help, used whenever no model answers.

    Every reply used to be an English literal, so a Czech question got a Czech
    greeting from the layer above and an English answer from here. And matching
    was done with `in`, which is how "Co mam delat v sekci Profile?" was
    answered with the location of the report files: "profile" contains "file".
    """

    # Topic, then the words that mean it. Matched on whole words, so a topic
    # cannot be triggered by a word that merely contains it.
    _TOPICS: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("last_run", ("last run", "latest run", "posledni", "posledniho", "beh", "behu", "dnes", "provedl")),
        ("risk", ("risk", "risks", "riziko", "rizika", "bezpecnost", "bezpecnostni", "guard", "guards", "limit", "limity")),
        ("grid", ("grid", "gridu", "gridy")),
        ("rebalancing", ("rebalancing", "rebalancovani", "rebalance", "kos", "kosik", "basket")),
        ("portfolio", ("portfolio", "portfolia", "asset", "assets", "aktivum", "aktiva", "token", "tokeny", "coin", "coins")),
        ("data", ("report", "reporty", "soubor", "soubory", "file", "files", "database", "databaze", "sqlite", "kde")),
    )

    def answer(self, question: str, snapshot: DesktopSnapshot) -> str:
        query = _fold(question)
        language = "cs" if is_czech(question) else "en"
        if not query:
            return service_text("help_no_question", language)

        topic = self._topic(query)
        if topic is None:
            # An answer to a question nobody asked is worse than admitting the
            # question was not understood: it reads as a confident non-sequitur.
            return service_text("help_not_understood", language)
        return getattr(self, f"_{topic}")(snapshot, language)

    def _topic(self, query: str) -> str | None:
        words = set(re.findall(r"[a-z0-9]+", query))
        for topic, keywords in self._TOPICS:
            for keyword in keywords:
                parts = keyword.split()
                if len(parts) > 1:
                    if keyword in query:
                        return topic
                elif keyword in words:
                    return topic
        return None

    def _last_run(self, snapshot: DesktopSnapshot, language: str) -> str:
        latest = snapshot.latest_run
        if latest is None:
            return service_text("help_no_run", language)
        top_action = (
            latest.actions[0].action if latest.actions else service_text("help_no_follow_up", language)
        )
        return service_text("help_last_run", language).format(
            run_id=latest.run_id,
            decision=latest.decision,
            summary=latest.decision_summary,
            action=top_action,
        )

    def _risk(self, snapshot: DesktopSnapshot, language: str) -> str:
        return service_text("help_risk", language)

    def _grid(self, snapshot: DesktopSnapshot, language: str) -> str:
        strategy = next((item for item in snapshot.strategies if item["type"] == "Spot Grid"), None)
        return strategy["detail"] if strategy else service_text("help_no_grid", language)

    def _rebalancing(self, snapshot: DesktopSnapshot, language: str) -> str:
        strategy = next((item for item in snapshot.strategies if item["type"] == "Rebalancing"), None)
        return strategy["detail"] if strategy else service_text("help_no_rebalancing", language)

    def _portfolio(self, snapshot: DesktopSnapshot, language: str) -> str:
        if not snapshot.portfolio_assets:
            return service_text("help_no_portfolio", language)
        top = ", ".join(f"{item['asset']} {item['allocation']}" for item in snapshot.portfolio_assets[:5])
        return service_text("help_portfolio", language).format(assets=top)

    def _data(self, snapshot: DesktopSnapshot, language: str) -> str:
        return service_text("help_data", language)


class ProviderBackedAssistant:
    def __init__(
        self,
        config_path: str | None = None,
        env_path: str = ".env",
        fallback: LocalHelpAssistant | None = None,
    ):
        self.config_path = config_path or default_config_path()
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
            czech = is_czech(question)
            detail = _describe_provider_error(exc, czech=czech)
            # Both languages get the offline answer. The Czech branch used to
            # return an apology only, so a Czech user lost the built-in help
            # exactly when the provider was down. "Local" is also wrong now that
            # a cloud provider is a first-class choice.
            offline = self.fallback.answer(question, snapshot)
            # "Failed" is wrong when nothing was ever asked. Naming an unset
            # environment variable to someone who never chose to have a model
            # reads as a malfunction they caused; it is simply the built-in
            # help answering, which is what this screen promises anyway.
            if _is_unconfigured(exc):
                note = (
                    "Odpovězeno bez AI modelu - žádný není připojený. Připojit ho můžete v kroku 4."
                    if czech
                    else "Answered without an AI model - none is connected. You can add one in step 4."
                )
                return f"{offline}\n\n{note}"
            label = "Poskytovatel AI selhal" if czech else "AI provider fallback"
            return f"{offline}\n\n{label}: {detail}"

    def respond(
        self,
        question: str,
        snapshot: DesktopSnapshot,
        app_context: dict[str, object] | None = None,
        conversation: tuple[dict[str, str], ...] = (),
        image_path: str = "",
    ) -> AssistantResponse:
        # With an image attached the question is about that image, so the
        # text-only matchers below must not answer it. They cannot see the
        # picture, and a keyword like "profile" or "role" would otherwise hijack
        # the question and return canned text about an unrelated feature.
        if image_path:
            return AssistantResponse(
                self.answer(question, snapshot, app_context, conversation, image_path)
            )
        deterministic = AssistantIntentService().propose(question, snapshot)
        if deterministic is not None:
            return deterministic
        market = MarketDataAssistant(self.config_path).answer(question, snapshot)
        if market is not None:
            return market
        contextual = ContextualHelpService().answer(question, app_context or {})
        if contextual is not None:
            proposal = ContextualHelpService().proposed_action(question, app_context or {})
            return AssistantResponse(contextual, proposal)
        knowledge = UiKnowledgeService()
        ui_answer = knowledge.answer(question)
        if ui_answer is not None:
            action = _open_guide_action(knowledge.matched_guide_id(question), is_czech(question))
            return AssistantResponse(ui_answer, action)
        return AssistantResponse(self.answer(question, snapshot, app_context, conversation, image_path))

    def _provider_answer(
        self,
        question: str,
        snapshot: DesktopSnapshot,
        app_context: dict[str, object],
        conversation: tuple[dict[str, str], ...],
        image_path: str,
    ) -> str:
        load_secrets(self.env_path)
        config = load_config(self.config_path).raw
        ai = config.get("ai", {})
        base_url = os.getenv(str(ai.get("base_url_env", "LLM_BASE_URL")), "").rstrip("/")
        api_key = os.getenv(str(ai.get("api_key_env", "LLM_API_KEY")), "")
        text_model = os.getenv(str(ai.get("model_env", "LLM_MODEL")), "")
        vision_model = os.getenv(str(ai.get("vision_model_env", "LLM_VISION_MODEL")), "").strip()
        model = (vision_model or text_model) if image_path else text_model
        if not base_url:
            raise RuntimeError("LLM_BASE_URL is not set.")
        if not model:
            raise RuntimeError("LLM_MODEL is not set." if not image_path else "No usable text or vision model is set.")
        if image_path:
            vision_available, vision_detail = AiProviderService(self.config_path, self.env_path).vision_support()
            if not vision_available:
                raise RuntimeError(vision_detail)

        czech = is_czech(question)
        # Name the language explicitly: smaller local models otherwise drift into
        # Slovak, which is close enough to Czech to slip past a generic "Czech".
        response_language = "Czech (čeština)" if czech else "English"
        language_rules = [
            f"Answer exclusively in {response_language}; do not mix languages except exact UI labels and technical identifiers.",
        ]
        if czech:
            language_rules.append(
                "The user writes Czech. Reply in Czech only. Slovak is a different language and is not acceptable, "
                "even though it looks similar; do not use Slovak words, spelling, or grammar."
            )
        payload = {
            "task": "Answer a user question about Coinductor in a concise, read-only way.",
            "response_language": response_language,
            "strict_boundaries": [
                *language_rules,
                "Do not claim that you changed settings, placed orders, redeemed Earn, or created Binance bots.",
                "Do not provide financial guarantees.",
                "Do not invent live market prices. Standalone price questions for a recognized asset (e.g. 'BTC price') are already answered deterministically before reaching you; if you are still asked for a current price, say you cannot fetch it yourself and suggest asking about a specific tracked asset, e.g. 'ETH price'.",
                "For documented UI behavior, answer directly from ui_component_catalog. Never hedge with likely, probably, may, or might.",
                "If a component is absent from the catalog, say that its exact behavior is not in the supplied context instead of guessing.",
                "If the user asks to change app state, explain that supported command intents require deterministic validation plus confirmation.",
                "Use only the supplied context. Say when data is unavailable.",
            ],
            "project_context": AiProviderService(self.config_path, self.env_path).inspect().context_sections,
            "ui_component_catalog": UiKnowledgeService().context(),
            "most_relevant_ui_components": UiKnowledgeService().relevant_context(question),
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
            # A far leaner payload than the text path. The full component
            # catalogue is ~15k characters and its boundaries tell the model to
            # answer *from the catalogue*, which buries a small vision model and
            # steers it away from the picture it was asked about. Keep only the
            # few relevant components so it can still name Coinductor controls.
            vision_payload = {
                "task": "Look at the attached image and answer the user's question about it.",
                "response_language": response_language,
                "guidance": [
                    *language_rules,
                    "Base the answer on what is actually visible in the image. Describe it concretely.",
                    "Do not invent screens, controls, or values that are not shown.",
                    "If it is a Coinductor screen, use most_relevant_ui_components to name controls correctly, "
                    "and say what the screen shows and what the user can do there.",
                    "If the image is not related to Coinductor, just answer the question about the image.",
                    "Do not claim that you changed settings, placed orders, or created Binance bots.",
                ],
                "most_relevant_ui_components": UiKnowledgeService().relevant_context(question),
                "current_app_context": app_context,
                "question": question,
                "image_attached": True,
                "schema": {"answer": "plain-language answer about the image, max 180 words"},
            }
            user_content = [
                {"type": "text", "text": json.dumps(vision_payload, default=str)},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded}"}},
            ]
        system_prompt = (
            "You are Coinductor's read-only assistant. Use the supplied application knowledge manifest, "
            "dynamic screen state, snapshot, and recent conversation as authoritative context. Resolve natural "
            "follow-up references from conversation. Match the user's language exactly, never guess undocumented "
            "behavior, and never use uncertain wording for documented controls. You cannot execute actions. "
            "Return JSON only."
        )
        if image_path:
            # The text-path prompt tells the model to answer from the manifest,
            # which is the wrong instinct when the user attached a picture.
            system_prompt = (
                "You are Coinductor's read-only assistant, answering about an image the user attached. "
                "Look at the image and describe what is actually in it. Do not invent content that is not visible. "
                "If it shows a Coinductor screen, explain what that screen is for using the supplied components. "
                "You cannot execute actions. Return JSON only."
            )
        request_body: dict[str, object] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        if _is_local_endpoint(base_url):
            request_body["reasoning_effort"] = "none"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        timeout = int(ai.get("timeout_seconds", 60))
        answer = self._request_answer(base_url, headers, request_body, timeout)
        if not answer:
            retry_body = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"Answer the question in {response_language} using only the supplied Coinductor context. "
                            "Return a concise plain-text answer. Do not output reasoning or JSON."
                        ),
                    },
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.1,
            }
            if _is_local_endpoint(base_url):
                retry_body["reasoning_effort"] = "none"
            answer = self._request_answer(base_url, headers, retry_body, timeout)
        if not answer:
            raise RuntimeError("AI provider returned an empty answer after one plain-text retry.")
        if czech and looks_slovak(answer):
            # Instructions alone do not reliably stop a small model drifting into
            # Slovak, so verify the output and retry once before giving up.
            czech_only_body = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Odpovídej výhradně česky. Nepoužívej slovenštinu ani slovenská slova "
                            "(nie, sú, aj, iba, ktorý, môže, podľa) a nikdy nepiš písmena ô, ľ, ŕ, ĺ, ä. "
                            "Vrať stručnou odpověď v prostém textu, bez JSON."
                        ),
                    },
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.1,
            }
            if _is_local_endpoint(base_url):
                czech_only_body["reasoning_effort"] = "none"
            retried = self._request_answer(base_url, headers, czech_only_body, timeout)
            if retried and not looks_slovak(retried):
                return retried
            # Better a clean Czech fallback than an answer in the wrong language.
            raise RuntimeError("Model odpověděl slovensky místo česky.")
        return answer

    def _request_answer(
        self,
        base_url: str,
        headers: dict[str, str],
        body: dict[str, object],
        timeout: int,
    ) -> str:
        request = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
        message = response_payload["choices"][0]["message"]
        answer = _extract_provider_answer(message.get("content"))
        if answer:
            return answer
        # Thinking models (e.g. qwen3-vl:*-thinking) return an empty `content`
        # and put the real answer in a reasoning field, so reading `content`
        # alone reported "empty answer" for a model that had in fact replied.
        for key in ("reasoning_content", "reasoning"):
            answer = _extract_provider_answer(message.get(key))
            if answer:
                return answer
        return ""

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


def _extract_provider_answer(content: object) -> str:
    if isinstance(content, list):
        content = "\n".join(
            str(item.get("text", ""))
            for item in content
            if isinstance(item, dict) and item.get("type") in {None, "text"}
        )
    if not isinstance(content, str) or not content.strip():
        return ""
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE | re.DOTALL).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return cleaned
    if isinstance(parsed, dict):
        for key in ("answer", "response", "message", "content"):
            value = parsed.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""
    return cleaned


def _is_unconfigured(exc: BaseException) -> bool:
    """Whether nothing was ever asked, as opposed to something going wrong.

    _provider_answer raises RuntimeError naming the unset variable. Matching on
    that text is not lovely, but it is raised in exactly one place and the two
    cases deserve opposite wording: one is a setting the user never filled in,
    the other is a provider that answered badly.
    """
    return isinstance(exc, RuntimeError) and "is not set" in str(exc)


def _is_local_endpoint(base_url: str) -> bool:
    return (urlparse(base_url).hostname or "").lower() in {"127.0.0.1", "localhost", "::1"}


def _normalize(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value.strip().lower())
        if not unicodedata.combining(character)
    )
