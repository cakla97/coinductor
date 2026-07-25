from decimal import Decimal
import json

import pytest

from coinductor import assistant as assistant_module
from coinductor.assistant import (
    AssistantIntentService,
    AssistantResponse,
    ContextualHelpService,
    LocalHelpAssistant,
    MarketDataAssistant,
    ProviderBackedAssistant,
)
from trading_agent.binance_client import BinanceApiError
from coinductor.controller import AppController
from coinductor.models import ActionSummary, DesktopRunResult, DesktopSnapshot
from coinductor.ui_knowledge import UiKnowledgeService
from test_coinductor_setup_service import VALID_CONFIG


def test_local_assistant_answers_from_latest_snapshot() -> None:
    snapshot = _snapshot()
    assistant = LocalHelpAssistant()

    assert "Run 42 ended with HOLD" in assistant.answer("What happened in the latest run?", snapshot)
    assert "Run 42 ended with HOLD" in assistant.answer("Co provedl posledni beh?", snapshot)
    assert "BTC 60.00%" in assistant.answer("Describe my portfolio", snapshot)
    assert "Grid is blocked" in assistant.answer("What about grid?", snapshot)


def test_market_data_assistant_answers_a_recognized_asset_price_question(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    monkeypatch.setattr(
        assistant_module.BinanceClient,
        "get_symbol_market_snapshot",
        lambda self, symbol: {
            "lastPrice": "65000.00",
            "priceChangePercent": "2.50",
            "highPrice": "66000.00",
            "lowPrice": "63000.00",
        },
    )
    assistant = MarketDataAssistant("config.toml")

    response = assistant.answer("What's the BTC price right now?", _snapshot())

    assert response is not None
    assert "BTC (BTCUSDC)" in response.text
    assert "65000.00" in response.text
    assert "not a trade recommendation" in response.text
    assert response.proposed_action is None


def test_market_data_assistant_answers_in_czech_for_a_czech_question(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    monkeypatch.setattr(
        assistant_module.BinanceClient,
        "get_symbol_market_snapshot",
        lambda self, symbol: {
            "lastPrice": "3200.00",
            "priceChangePercent": "-1.10",
            "highPrice": "3300.00",
            "lowPrice": "3100.00",
        },
    )
    assistant = MarketDataAssistant("config.toml")

    response = assistant.answer("Jaká je aktuální cena ETH?", _snapshot())

    assert response is not None
    assert "aktuální cena" in response.text
    assert "obchodní doporučení" in response.text


def test_market_data_assistant_falls_back_to_the_next_quote_asset(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")

    def fake_snapshot(self, symbol):
        if symbol == "BTCUSDC":
            raise BinanceApiError("Invalid symbol.")
        return {"lastPrice": "65000.00", "priceChangePercent": "2.50", "highPrice": "66000.00", "lowPrice": "63000.00"}

    monkeypatch.setattr(assistant_module.BinanceClient, "get_symbol_market_snapshot", fake_snapshot)
    assistant = MarketDataAssistant("config.toml")

    response = assistant.answer("BTC price", _snapshot())

    assert response is not None
    assert "BTCUSDT" in response.text


def test_market_data_assistant_reports_an_error_when_every_quote_asset_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")

    def always_fails(self, symbol):
        raise BinanceApiError("Invalid symbol.")

    monkeypatch.setattr(assistant_module.BinanceClient, "get_symbol_market_snapshot", always_fails)
    assistant = MarketDataAssistant("config.toml")

    response = assistant.answer("BTC price", _snapshot())

    assert response is not None
    assert "Could not fetch current data" in response.text


def test_market_data_assistant_ignores_questions_without_a_recognized_asset() -> None:
    assistant = MarketDataAssistant()

    assert assistant.answer("What is the price of eggs?", _snapshot()) is None


def test_market_data_assistant_ignores_questions_without_a_price_trigger_word() -> None:
    assistant = MarketDataAssistant()

    assert assistant.answer("Tell me about BTC as an asset role.", _snapshot()) is None


def test_respond_answers_market_questions_before_reaching_the_ai_provider(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    monkeypatch.setattr(
        assistant_module.BinanceClient,
        "get_symbol_market_snapshot",
        lambda self, symbol: {"lastPrice": "65000.00", "priceChangePercent": "2.50", "highPrice": "66000.00", "lowPrice": "63000.00"},
    )
    assistant = ProviderBackedAssistant(config_path="config.toml", env_path=str(tmp_path / ".env"))

    response = assistant.respond("BTC price", _snapshot())

    assert "BTC (BTCUSDC)" in response.text


def test_provider_backed_assistant_uses_chat_completions(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_VISION_MODEL", raising=False)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / ".env").write_text(
        "LLM_BASE_URL=http://127.0.0.1:11434/v1\nLLM_MODEL=qwen3:14b\nLLM_VISION_MODEL=qwen3-vl:8b\n",
        encoding="utf-8",
    )
    called_urls: list[str] = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self) -> bytes:
            return json.dumps(
                {"choices": [{"message": {"content": json.dumps({"answer": "Provider answer."})}}]}
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        called_urls.append(request.full_url)
        body = json.loads(request.data.decode("utf-8"))
        assert body["model"] == "qwen3:14b"
        assert "chat/completions" in request.full_url
        prompt = json.loads(body["messages"][1]["content"])
        assert prompt["response_language"] == "English"
        assert any(item["component"] == "Refresh checks" for item in prompt["ui_component_catalog"])
        assert prompt["current_app_context"]["context_page"] == "Action Plan"
        assert prompt["recent_conversation"] == [{"role": "user", "text": "Earlier question"}]
        assert prompt["most_relevant_ui_components"]
        assert body["reasoning_effort"] == "none"
        return FakeResponse()

    monkeypatch.setattr(assistant_module.urllib.request, "urlopen", fake_urlopen)

    answer = ProviderBackedAssistant("config.toml", ".env").answer(
        "Explain risk",
        _snapshot(),
        {"context_page": "Action Plan"},
        ({"role": "user", "text": "Earlier question"},),
    )

    assert answer == "Provider answer."
    assert called_urls == ["http://127.0.0.1:11434/v1/chat/completions"]


def test_provider_retries_empty_answer_as_plain_text(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / ".env").write_text(
        "LLM_BASE_URL=http://127.0.0.1:11434/v1\nLLM_MODEL=qwen3:14b\n",
        encoding="utf-8",
    )
    bodies: list[dict] = []

    class FakeResponse:
        def __init__(self, content: str):
            self.content = content

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self) -> bytes:
            return json.dumps({"choices": [{"message": {"content": self.content}}]}).encode("utf-8")

    def fake_urlopen(request, timeout):
        bodies.append(json.loads(request.data.decode("utf-8")))
        return FakeResponse("") if len(bodies) == 1 else FakeResponse("Safety stage is a local execution gate.")

    monkeypatch.setattr(assistant_module.urllib.request, "urlopen", fake_urlopen)

    answer = ProviderBackedAssistant("config.toml", ".env").answer("Explain the safety status", _snapshot())

    assert answer == "Safety stage is a local execution gate."
    assert len(bodies) == 2
    assert "response_format" in bodies[0]
    assert "response_format" not in bodies[1]
    assert bodies[1]["reasoning_effort"] == "none"


def test_provider_backed_assistant_sends_image_to_vision_model(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_VISION_MODEL", raising=False)
    monkeypatch.delenv("LLM_VISION_ENABLED", raising=False)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / ".env").write_text(
        "LLM_BASE_URL=http://127.0.0.1:11434/v1\nLLM_MODEL=qwen3:14b\nLLM_VISION_MODEL=qwen3-vl:8b\n",
        encoding="utf-8",
    )
    image_path = tmp_path / "screen.png"
    image_path.write_bytes(b"fake-png-content")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self) -> bytes:
            return json.dumps(
                {"choices": [{"message": {"content": json.dumps({"answer": "Image answer."})}}]}
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        body = json.loads(request.data.decode("utf-8"))
        assert body["model"] == "qwen3-vl:8b"
        content = body["messages"][1]["content"]
        assert content[0]["type"] == "text"
        assert json.loads(content[0]["text"])["image_attached"] is True
        assert content[1]["type"] == "image_url"
        assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")
        return FakeResponse()

    monkeypatch.setattr(assistant_module.urllib.request, "urlopen", fake_urlopen)

    answer = ProviderBackedAssistant("config.toml", ".env").answer(
        "Explain this screenshot",
        _snapshot(),
        image_path=str(image_path),
    )

    assert answer == "Image answer."


def test_provider_backed_assistant_falls_back_when_provider_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")

    answer = ProviderBackedAssistant("config.toml", ".env").answer("Explain risk", _snapshot())

    assert "Coinductor keeps execution deterministic" in answer
    assert "AI provider fallback" in answer


def test_provider_backed_assistant_hides_raw_connection_error_in_english(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / ".env").write_text(
        "LLM_BASE_URL=http://127.0.0.1:11434/v1\nLLM_MODEL=qwen3:14b\n",
        encoding="utf-8",
    )

    def fake_urlopen(request, timeout):
        raise OSError("[WinError 10061] No connection could be made because the target machine actively refused it")

    monkeypatch.setattr(assistant_module.urllib.request, "urlopen", fake_urlopen)

    answer = ProviderBackedAssistant("config.toml", ".env").answer("Explain risk", _snapshot())

    assert "WinError" not in answer
    assert "could not be reached" in answer


def test_provider_backed_assistant_hides_raw_connection_error_in_czech(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / ".env").write_text(
        "LLM_BASE_URL=http://127.0.0.1:11434/v1\nLLM_MODEL=qwen3:14b\n",
        encoding="utf-8",
    )

    def fake_urlopen(request, timeout):
        raise OSError("[WinError 10061] Nemohlo být vytvořeno žádné připojení, protože cílový počítač jej aktivně odmítl")

    monkeypatch.setattr(assistant_module.urllib.request, "urlopen", fake_urlopen)

    answer = ProviderBackedAssistant("config.toml", ".env").answer(
        "Co znamenají jednotlivá pole v Nastavení, abych věděl co mám zvolit?",
        _snapshot(),
    )

    assert "WinError" not in answer
    assert "nepodařilo kontaktovat" in answer


def test_assistant_prepares_safe_navigation_without_calling_provider() -> None:
    response = ProviderBackedAssistant().respond("Open portfolio", _snapshot())

    assert response.proposed_action == {
        "type": "NAVIGATE",
        "title": "Open Portfolio",
        "description": "Navigate to the Portfolio page. This does not change portfolio or exchange state.",
        "confirmLabel": "Open page",
        "page": 2,
    }


@pytest.mark.parametrize("alias,page,label", [(alias, page, label) for alias, (page, label) in AssistantIntentService._PAGES.items()])
def test_assistant_navigates_to_every_page_alias_in_english_and_czech(alias, page, label) -> None:
    # Broad paraphrase coverage: every page alias (English and Czech) the assistant
    # is supposed to recognize must actually resolve to the right page index.
    response = ProviderBackedAssistant().respond(f"Open {alias}", _snapshot())

    assert response.proposed_action is not None, f"'open {alias}' did not resolve to a NAVIGATE action"
    assert response.proposed_action["type"] == "NAVIGATE"
    assert response.proposed_action["page"] == page, f"alias {alias!r} resolved to page {response.proposed_action['page']}, expected {page} ({label})"


def test_assistant_navigation_covers_every_sidebar_page() -> None:
    # Guards against silently losing coverage for a whole page if _PAGES is edited.
    covered_pages = {page for page, _label in AssistantIntentService._PAGES.values()}

    assert covered_pages == {0, 1, 2, 3, 4, 5, 6, 7, 8}


def test_assistant_prepares_read_only_analysis_but_blocks_live_trade() -> None:
    service = AssistantIntentService()

    analysis = service.propose("Spust novou analyzu", _snapshot())
    live = service.propose("Buy BTC now", _snapshot())

    assert analysis is not None
    assert analysis.proposed_action["type"] == "RUN_READ_ONLY_ANALYSIS"
    assert live is not None
    assert live.proposed_action is None
    assert "cannot prepare or execute" in live.text


def test_assistant_prepares_validated_asset_role_change() -> None:
    response = AssistantIntentService().propose("Change BTC role to grid candidate", _snapshot())

    assert response is not None
    assert response.proposed_action["type"] == "SET_ASSET_ROLE"
    assert response.proposed_action["asset"] == "BTC"
    assert response.proposed_action["role"] == "GRID_CANDIDATE"


def test_controller_confirms_only_known_asset_role_change(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    controller = AppController()
    controller._portfolio_assets = [{"asset": "BTC", "policy": "System default"}]
    controller._on_assistant_completed(
        AssistantResponse(
            "Prepared.",
            {
                "type": "SET_ASSET_ROLE",
                "asset": "BTC",
                "role": "GRID_CANDIDATE",
                "title": "Change BTC role",
                "description": "Test",
                "confirmLabel": "Change role",
            },
        )
    )

    controller.confirmAssistantAction()

    assert controller.assistantPendingAction == {}
    assert controller._asset_policy_store.load() == {"BTC": "GRID_CANDIDATE"}


def test_controller_rejects_unknown_asset_role_change(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    controller = AppController()
    controller._portfolio_assets = [{"asset": "BTC", "policy": "System default"}]
    controller._assistant_pending_action = {
        "type": "SET_ASSET_ROLE",
        "asset": "ETH",
        "role": "GRID_CANDIDATE",
    }

    controller.confirmAssistantAction()

    assert controller._asset_policy_store.load() == {}


def test_ui_knowledge_answers_refresh_checks_exactly_in_czech() -> None:
    answer = UiKnowledgeService().answer("Co udělá tlačítko Refresh checks v Live actions?")

    assert answer is not None
    assert "znovu načte lokální stav" in answer
    assert "Neprovádí síťovou kontrolu" in answer
    assert "likely" not in answer.lower()


def test_ui_knowledge_explains_safe_defaults_without_guessing() -> None:
    answer = UiKnowledgeService().answer("What does Use safe defaults do?")

    assert answer is not None
    assert "20% reserve" in answer
    assert "spot trading disabled" in answer


def test_ui_knowledge_summarizes_action_plan_in_czech() -> None:
    answer = UiKnowledgeService().answer("Shrň mi sekci Action Plan")

    assert answer is not None
    assert "konsolidovaný výsledek" in answer
    assert "deterministické podmínky" in answer


def test_contextual_help_explains_current_trade_blocker_in_czech() -> None:
    answer = ContextualHelpService().answer(
        "Co tady teď brání obchodu?",
        {
            "context_page": "Action Plan",
            "action_plan": [
                {
                    "title": "Trade",
                    "status": "HOLD",
                    "detail": "Risk-off trend and price below EMA200.",
                    "submitBlockedReason": "Live submit appears only for BUY previews.",
                }
            ],
        },
    )

    assert answer is not None
    assert "Aktuální stav Trade je HOLD" in answer
    assert "Risk-off trend" in answer


def test_contextual_help_summarizes_origin_page() -> None:
    answer = ContextualHelpService().answer(
        "Shrň tuto stránku",
        {"context_page": "Active Strategies"},
    )

    assert answer is not None
    assert "monitoruje" in answer


def test_contextual_help_explains_itself_in_czech_without_provider() -> None:
    response = ProviderBackedAssistant().respond("Tak co mi o sobě řekneš?", _snapshot(), {})

    assert "AI Assistant vysvětluje" in response.text
    assert "Chat nemůže přímo" in response.text
    assert "fallback" not in response.text.lower()


def test_contextual_help_explains_binance_not_checked_without_provider() -> None:
    context = {
        "context_page": "Overview",
        "binance_read_only": {
            "status": "Not checked",
            "detail": "Run the read-only check from Settings before live analysis.",
        },
    }

    response = ProviderBackedAssistant().respond(
        "What does the Binance Not checked box in the lower-left corner mean?",
        _snapshot(),
        context,
    )

    assert "read-only Binance API connection" in response.text
    assert "does not prove" in response.text
    assert response.proposed_action is None


def test_contextual_help_explains_exact_binance_status_question_in_czech() -> None:
    answer = UiKnowledgeService().answer("Co znamená box Binance Not checked v levém spodním rohu?")

    assert "read-only Binance API" in answer
    assert "neznamená, že klíč chybí" in answer


def test_ui_knowledge_semantically_resolves_safety_follow_up() -> None:
    answer = UiKnowledgeService().answer("A co znamená box nad tím SAFETY - Live enabled?")

    assert answer is not None
    assert "lokální brána exekuce" in answer
    assert "Samotná změna stage nikdy neprovede příkaz" in answer


def test_ui_knowledge_combines_multiple_documented_components() -> None:
    answer = UiKnowledgeService().answer(
        "Jak spolu v aplikaci souvisí Safety stage a stav Binance read-only připojení?"
    )

    assert answer is not None
    assert "Safety stage:" in answer
    assert "BINANCE connection status box:" in answer
    assert "podezřel" not in answer.lower()


def test_ui_knowledge_explains_its_own_vision_warning() -> None:
    answer = UiKnowledgeService().answer(
        "Co znamená, že mám nakonfigurovat vision model or set LLM_VISION_ENABLED=true only when the endpoint supports images?"
    )

    assert answer is not None
    assert "qwen3:14b vision schopnosti nepřidá" in answer
    assert "pouze přepíše detekci" in answer
    assert "Safe defaults" not in answer


def test_ui_knowledge_explains_how_to_enable_image_input_for_rephrased_question() -> None:
    answer = UiKnowledgeService().answer(
        "Proč nyní nemohu vložit obrázek? Co mám udělat pro to, abych obrázky mohl vkládat?"
    )

    assert answer is not None
    assert "https://ollama.com/library/qwen3-vl" in answer
    assert "qwen3-vl:8b" in answer
    assert "Settings > Configure AI models" in answer
    assert "Save local AI" in answer
    assert "Check AI provider" in answer
    assert "qwen3:14b vision schopnosti nepřidá" in answer


def test_ui_knowledge_explains_image_setup_for_english_support_question() -> None:
    answer = UiKnowledgeService().answer("Why can't I attach an image and how do I enable it?")

    assert answer is not None
    assert "https://ollama.com/library/qwen3-vl" in answer
    assert "Settings > Configure AI models" in answer


def test_ui_knowledge_does_not_use_description_words_as_confident_match() -> None:
    answer = UiKnowledgeService().answer("Co znamená enabled only?")

    assert answer is None


def test_ui_knowledge_explains_how_to_create_binance_api_keys() -> None:
    answer = UiKnowledgeService().answer("How do I create a Binance API key?")

    assert answer is not None
    assert "API Management" in answer
    assert "Never enable withdrawals" in answer


def test_ui_knowledge_explains_automation_level_in_czech() -> None:
    answer = UiKnowledgeService().answer("Co znamená automation level?")

    assert answer is not None
    assert "Recommend-only" in answer
    assert "risk engine" in answer.lower()


def test_ui_knowledge_explains_first_vs_existing_portfolio_path() -> None:
    answer = UiKnowledgeService().answer(
        "What is the difference between existing portfolio and first portfolio?"
    )

    assert answer is not None
    assert "Build my first portfolio" in answer
    assert "First portfolio deployment" in answer


def test_ui_knowledge_explains_local_ai_download_steps_in_czech() -> None:
    answer = UiKnowledgeService().answer("Co si mám stáhnout pro lokální AI?")

    assert answer is not None
    assert "ollama.com" in answer
    assert "Detect installed models" in answer


def test_ui_knowledge_explains_testnet_purpose() -> None:
    answer = UiKnowledgeService().answer("What is Testnet for?")

    assert answer is not None
    assert "virtual funds" in answer
    assert "optional" in answer.lower()


def test_ui_knowledge_explains_decision_profile_fields_in_czech() -> None:
    answer = UiKnowledgeService().answer(
        "Co znamenají jednotlivá pole v Decision profile, abych věděl co správně mám zvolit?"
    )

    assert answer is not None
    assert "Balanced" in answer
    assert "Recommendations only" in answer
    assert "Drawdown comfort" in answer or "propad" in answer.lower()


def test_ui_knowledge_explains_decision_profile_fields_in_english() -> None:
    answer = UiKnowledgeService().answer("Explain the decision profile fields and which profile options should I choose.")

    assert answer is not None
    assert "Guarded automation" in answer
    assert "None of these choices place an order" in answer


def test_contextual_next_step_offers_navigation_not_execution() -> None:
    context = {
        "context_page": "AI Assistant",
        "readiness": {
            "next_step": "Read-only keys exist but have not been checked.",
            "action_code": "CHECK_BINANCE",
            "action_label": "Run read-only check",
        },
    }
    service = ContextualHelpService()

    answer = service.answer("Co mám udělat dál?", context)
    proposal = service.proposed_action("Co mám udělat dál?", context)

    assert answer is not None
    assert proposal["type"] == "NAVIGATE"
    assert proposal["page"] == 8
    assert "Nic se neprovede automaticky" in proposal["description"]


def test_controller_tracks_assistant_origin_and_starts_new_chat(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    controller = AppController()
    controller.setCurrentPage(3)
    controller.setCurrentPage(6)
    controller._assistant_messages.append({"role": "user", "text": "Old question"})

    assert controller.assistantContextPage == "Action Plan"

    controller.newAssistantChat()

    assert len(controller.assistantMessages) == 1
    assert controller.assistantMessages[0]["role"] == "assistant"


def test_controller_restores_saved_assistant_chat(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    controller = AppController()
    controller._assistant_messages = [
        {"role": "user", "text": "Saved question"},
        {"role": "assistant", "text": "Saved answer"},
    ]
    controller._assistant_history_store.save("saved-chat", controller._assistant_messages, "Portfolio")
    controller._assistant_history = controller._assistant_history_store.summaries()

    controller.restoreAssistantChat("saved-chat")

    assert controller.assistantMessages[-1]["text"] == "Saved answer"
    assert controller.assistantContextPage == "Portfolio"


def test_controller_restores_image_metadata_from_saved_chat(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    controller = AppController()
    messages = [
        {
            "role": "user",
            "text": "Explain this screenshot",
            "imageUrl": "file:///D:/Screenshots/example.png",
            "imageName": "example.png",
        },
        {"role": "assistant", "text": "It shows the Overview page."},
    ]
    controller._assistant_history_store.save("image-chat", messages, "Overview")

    controller.restoreAssistantChat("image-chat")

    assert controller.assistantMessages[0]["imageName"] == "example.png"


def test_completed_answer_is_immediately_visible_in_chat_history(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    controller = AppController()
    controller._assistant_messages = [
        {"role": "user", "text": "What does Refresh checks do?"},
        {"role": "typing", "text": ""},
    ]

    controller._on_assistant_completed(AssistantResponse("It reloads local setup state."))

    assert len(controller.assistantHistory) == 1
    assert controller.assistantHistory[0]["title"] == "What does Refresh checks do?"


def test_looks_slovak_flags_slovak_but_not_czech() -> None:
    from coinductor.assistant import looks_slovak

    slovak = (
        "Vaša aktuálna stratégia je v režime HOLD, čo znamená, že žiadne aktívne "
        "obchodovanie nie je odporúčané. V súčasnosti nie sú žiadne stratégie vhodné."
    )
    assert looks_slovak(slovak) is True

    for czech in (
        "Vaše aktuální strategie je v režimu HOLD, což znamená, že žádné aktivní obchodování není doporučeno.",
        "Action Plan zobrazuje konkrétní další kroky z posledního běhu.",
        "Ano, můžeme se bavit česky. Ptejte se česky a odpovím česky.",
    ):
        assert looks_slovak(czech) is False


def test_language_meta_question_matches_noun_and_imperative_forms() -> None:
    service = ContextualHelpService()

    # "v češtině" and imperatives previously fell through to the model, which
    # answered about trading strategy instead.
    for question in (
        "Můžu si s tebou povídat v češtině?",
        "Mluv česky",
        "Odpovídej mi v češtině",
        "Umíš česky?",
    ):
        assert service.answer(question, {}) is not None, question

    for unrelated in ("Jaká je cena BTC?", "Co je Action Plan?", "Kde najdu reporty?"):
        assert service.answer(unrelated, {}) is None, unrelated


def test_language_meta_question_is_answered_deterministically() -> None:
    service = ContextualHelpService()

    czech = service.answer("Můžu si s tebou povídat česky?", {})
    english = service.answer("Can I talk to you in Czech?", {})

    assert czech is not None and czech.startswith("Ano, můžeme se bavit česky")
    assert english is not None and english.startswith("Yes, I can answer in Czech")
    # It must not be mistaken for a portfolio/strategy question.
    assert "HOLD" not in czech and "strategi" not in czech.lower()
    # Unrelated questions still fall through to the rest of the pipeline.
    assert service.answer("Jaká je cena BTC?", {}) is None


def test_czech_questions_instruct_the_model_to_avoid_slovak(tmp_path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout=0):
        captured["body"] = json.loads(request.data.decode("utf-8"))

        class _Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({"choices": [{"message": {"content": '{"answer": "ok"}'}}]}).encode("utf-8")

        return _Response()

    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / ".env").write_text("LLM_BASE_URL=http://127.0.0.1:11434/v1\nLLM_MODEL=qwen3:14b\n", encoding="utf-8")
    monkeypatch.setattr(assistant_module.urllib.request, "urlopen", fake_urlopen)

    ProviderBackedAssistant("config.toml", str(tmp_path / ".env")).answer(
        "Co znamená Action Plan?", _snapshot()
    )

    # The payload is embedded as an ASCII-escaped JSON string, so parse it back
    # rather than string-matching the outer request body.
    user_message = next(item for item in captured["body"]["messages"] if item["role"] == "user")
    payload = json.loads(user_message["content"])

    assert payload["response_language"] == "Czech (čeština)"
    assert any("Slovak is a different language" in rule for rule in payload["strict_boundaries"])


def test_matched_guide_id_uses_explicit_override() -> None:
    service = UiKnowledgeService()

    assert service.matched_guide_id("how do i create an api key") == "binance-api"
    assert service.matched_guide_id("what is testnet for") == "binance-testnet"


def test_matched_guide_id_maps_page_to_page_guide() -> None:
    service = UiKnowledgeService()

    assert service.matched_guide_id("what does prepare trade preview do") == "page-live-actions"


def test_respond_offers_open_guide_action_for_documented_topic(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    assistant = ProviderBackedAssistant(config_path="config.toml", env_path=str(tmp_path / ".env"))

    response = assistant.respond("how do i create an api key", _snapshot())

    assert response.proposed_action is not None
    assert response.proposed_action["type"] == "OPEN_GUIDE"
    assert response.proposed_action["guide_id"] == "binance-api"


def _snapshot() -> DesktopSnapshot:
    run = DesktopRunResult(
        run_id=42,
        status="OK",
        report_path="report.md",
        decision="HOLD",
        decision_summary="Wait for a safer entry.",
        risk_approved=True,
        risk_reason="Within limits.",
        portfolio_value=Decimal("500"),
        liquid_value=Decimal("100"),
        locked_value=Decimal("400"),
        ai_summary="",
        actions=(ActionSummary("LOW", "Run again tomorrow.", "No urgency."),),
    )
    snapshot = DesktopSnapshot(
        latest_run=run,
        portfolio_assets=(
            {
                "asset": "BTC",
                "allocation": "60.00%",
            },
        ),
        strategies=(
            {
                "type": "Spot Grid",
                "detail": "Grid is blocked while trend risk remains high.",
            },
        ),
        run_history=(),
    )
    return snapshot


def test_slovak_answer_triggers_retry_then_clean_czech_fallback(tmp_path, monkeypatch) -> None:
    """A model that keeps answering Slovak must never reach the user."""
    calls: list[int] = []
    slovak = "Vaša stratégia nie je vhodná, sú tu iba riziká podľa filtrov."

    def always_slovak(request, timeout=0):
        calls.append(1)

        class _Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({"choices": [{"message": {"content": json.dumps({"answer": slovak})}}]}).encode("utf-8")

        return _Response()

    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / ".env").write_text("LLM_BASE_URL=http://127.0.0.1:11434/v1\nLLM_MODEL=qwen3:14b\n", encoding="utf-8")
    monkeypatch.setattr(assistant_module.urllib.request, "urlopen", always_slovak)

    result = ProviderBackedAssistant("config.toml", str(tmp_path / ".env")).answer(
        "Co znamená Action Plan?", _snapshot()
    )

    # It retried once with a Czech-only instruction...
    assert len(calls) >= 2
    # ...and, still getting Slovak, returned clean Czech instead of the Slovak text.
    from coinductor.assistant import looks_slovak

    assert looks_slovak(result) is False
    assert "nie je vhodná" not in result


def test_image_questions_send_a_lean_payload(tmp_path, monkeypatch) -> None:
    """The text path ships a ~15k-char component catalogue and tells the model
    to answer *from the catalogue*. Sent alongside a picture that buries a small
    vision model and steers it away from the image."""
    captured: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self) -> bytes:
            return json.dumps({"choices": [{"message": {"content": json.dumps({"answer": "ok"})}}]}).encode("utf-8")

    def fake_urlopen(request, timeout):
        body = json.loads(request.data.decode("utf-8"))
        content = body["messages"][1]["content"]
        captured["system"] = body["messages"][0]["content"]
        captured["payload"] = json.loads(content[0]["text"] if isinstance(content, list) else content)
        return FakeResponse()

    monkeypatch.chdir(tmp_path)
    for key in ("LLM_BASE_URL", "LLM_MODEL", "LLM_VISION_MODEL"):
        monkeypatch.delenv(key, raising=False)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / ".env").write_text(
        "LLM_BASE_URL=http://127.0.0.1:11434/v1\nLLM_MODEL=qwen3:14b\nLLM_VISION_MODEL=qwen3-vl:8b\n",
        encoding="utf-8",
    )
    image = tmp_path / "shot.png"
    image.write_bytes(b"fake-png")
    monkeypatch.setattr(assistant_module.urllib.request, "urlopen", fake_urlopen)

    ProviderBackedAssistant("config.toml", ".env").answer(
        "What do you see on this picture?", _snapshot(), image_path=str(image)
    )

    payload = captured["payload"]
    assert payload["image_attached"] is True
    # The bulky catalogue is dropped; the small relevant subset is kept so the
    # model can still name Coinductor controls.
    assert "ui_component_catalog" not in payload
    assert "most_relevant_ui_components" in payload
    assert "snapshot" not in payload
    # The instructions must point at the image, not at the manifest.
    assert "image" in captured["system"].lower()
    guidance = " ".join(payload["guidance"]).lower()
    assert "visible in the image" in guidance


def test_image_questions_bypass_the_text_only_matchers(tmp_path, monkeypatch) -> None:
    """A keyword in an image question must not hijack it.

    "Co znamena kdyz mam takto nastaveny profil?" asked about a screenshot came
    back as canned role-change instructions, because the deterministic text
    matchers ran first and cannot see the attached image.
    """
    reached_provider = {"yes": False}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self) -> bytes:
            reached_provider["yes"] = True
            return json.dumps(
                {"choices": [{"message": {"content": json.dumps({"answer": "The screenshot shows the decision profile."})}}]}
            ).encode("utf-8")

    monkeypatch.chdir(tmp_path)
    for key in ("LLM_BASE_URL", "LLM_MODEL", "LLM_VISION_MODEL"):
        monkeypatch.delenv(key, raising=False)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / ".env").write_text(
        "LLM_BASE_URL=http://127.0.0.1:11434/v1\nLLM_MODEL=qwen3:14b\nLLM_VISION_MODEL=qwen3-vl:8b\n",
        encoding="utf-8",
    )
    image = tmp_path / "profile.png"
    image.write_bytes(b"fake-png")
    monkeypatch.setattr(assistant_module.urllib.request, "urlopen", lambda request, timeout: FakeResponse())

    response = ProviderBackedAssistant("config.toml", ".env").respond(
        "What does it mean when I have the profile and role set like this?",
        _snapshot(),
        image_path=str(image),
    )

    assert reached_provider["yes"], "an image question was answered without the vision model"
    assert "screenshot" in response.text.lower()


def test_text_questions_still_use_the_deterministic_matchers(tmp_path, monkeypatch) -> None:
    """The bypass must apply only when an image is attached."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")

    response = ProviderBackedAssistant("config.toml", str(tmp_path / ".env")).respond(
        "Can I talk to you in Czech?", _snapshot()
    )

    assert response.text.startswith("Yes, I can answer in Czech")


def test_thinking_models_answering_in_the_reasoning_field_are_read(tmp_path, monkeypatch) -> None:
    """qwen3-vl:*-thinking returns content="" and puts the answer in `reasoning`.

    Reading `content` alone reported "AI provider returned an empty answer"
    for a model that had actually replied.
    """
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self) -> bytes:
            return json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "",
                                "reasoning": json.dumps({"answer": "The screenshot shows the Action Plan page."}),
                            }
                        }
                    ]
                }
            ).encode("utf-8")

    monkeypatch.chdir(tmp_path)
    for key in ("LLM_BASE_URL", "LLM_MODEL"):
        monkeypatch.delenv(key, raising=False)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / ".env").write_text(
        "LLM_BASE_URL=http://127.0.0.1:11434/v1\nLLM_MODEL=qwen3:14b\n", encoding="utf-8"
    )
    monkeypatch.setattr(assistant_module.urllib.request, "urlopen", lambda request, timeout: FakeResponse())

    answer = ProviderBackedAssistant("config.toml", ".env").answer("Explain risk", _snapshot())

    assert answer == "The screenshot shows the Action Plan page."


def test_role_intent_does_not_hijack_generic_settings_questions() -> None:
    """"nastav" matches any Czech phrasing about settings.

    As a standalone trigger it made unrelated questions return canned
    role-change instructions instead of a real answer.
    """
    service = AssistantIntentService()
    snapshot = _snapshot()

    for question in (
        "ok, mam to spravne nastavene nebo bys doporucil jine nastaveni?",
        "je to dobre nastavene?",
        "zmen mi nastaveni aplikace",
    ):
        assert service.propose(question, snapshot) is None, question


def test_role_intent_still_handles_real_role_requests() -> None:
    service = AssistantIntentService()
    snapshot = _snapshot()

    action = service.propose("Change BTC role to Grid candidate", snapshot)
    assert action is not None and action.proposed_action is not None
    assert action.proposed_action["type"] == "SET_ASSET_ROLE"
    assert action.proposed_action["asset"] == "BTC"

    # Naming the feature without both parts still gets the guidance.
    partial = service.propose("what does the role mean?", snapshot)
    assert partial is not None and "name one asset" in partial.text
