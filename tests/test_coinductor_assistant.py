from decimal import Decimal
import json

from coinductor import assistant as assistant_module
from coinductor.assistant import (
    AssistantIntentService,
    AssistantResponse,
    ContextualHelpService,
    LocalHelpAssistant,
    ProviderBackedAssistant,
)
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


def test_provider_backed_assistant_uses_chat_completions(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / ".env").write_text(
        "LLM_BASE_URL=http://127.0.0.1:11434/v1\nLLM_MODEL=qwen3:14b\n",
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


def test_provider_backed_assistant_sends_image_to_vision_model(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_VISION_ENABLED", raising=False)
    (tmp_path / "config.toml").write_text(VALID_CONFIG, encoding="utf-8")
    (tmp_path / ".env").write_text(
        "LLM_BASE_URL=http://127.0.0.1:11434/v1\nLLM_MODEL=qwen3-vl:8b\n",
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


def test_assistant_prepares_safe_navigation_without_calling_provider() -> None:
    response = ProviderBackedAssistant().respond("Open portfolio", _snapshot())

    assert response.proposed_action == {
        "type": "NAVIGATE",
        "title": "Open Portfolio",
        "description": "Navigate to the Portfolio page. This does not change portfolio or exchange state.",
        "confirmLabel": "Open page",
        "page": 2,
    }


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

    assert "read-only API connection state" in response.text
    assert "does not by itself mean" in response.text
    assert response.proposed_action["type"] == "NAVIGATE"
    assert response.proposed_action["page"] == 8


def test_contextual_help_explains_exact_binance_status_question_in_czech() -> None:
    answer = ContextualHelpService().answer(
        "Co znamená box Binance Not checked v levém spodním rohu?",
        {
            "binance_read_only": {
                "status": "Not checked",
                "detail": "Run the read-only check from Settings before live analysis.",
            }
        },
    )

    assert "zatím nespustila nebo nedokončila" in answer
    assert "neříká, že klíč chybí" in answer


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
