from decimal import Decimal
import json

from coinductor import assistant as assistant_module
from coinductor.assistant import AssistantIntentService, AssistantResponse, LocalHelpAssistant, ProviderBackedAssistant
from coinductor.controller import AppController
from coinductor.models import ActionSummary, DesktopRunResult, DesktopSnapshot
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
        return FakeResponse()

    monkeypatch.setattr(assistant_module.urllib.request, "urlopen", fake_urlopen)

    answer = ProviderBackedAssistant("config.toml", ".env").answer("Explain risk", _snapshot())

    assert answer == "Provider answer."
    assert called_urls == ["http://127.0.0.1:11434/v1/chat/completions"]


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
