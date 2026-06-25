from decimal import Decimal

from coinductor.assistant import LocalHelpAssistant
from coinductor.models import ActionSummary, DesktopRunResult, DesktopSnapshot


def test_local_assistant_answers_from_latest_snapshot() -> None:
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
    assistant = LocalHelpAssistant()

    assert "Run 42 ended with HOLD" in assistant.answer("What happened in the latest run?", snapshot)
    assert "Run 42 ended with HOLD" in assistant.answer("Co provedl posledni beh?", snapshot)
    assert "BTC 60.00%" in assistant.answer("Describe my portfolio", snapshot)
    assert "Grid is blocked" in assistant.answer("What about grid?", snapshot)
