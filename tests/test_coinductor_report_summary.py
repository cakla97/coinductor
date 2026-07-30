from decimal import Decimal

from coinductor.report_summary import ReportSummaryReader


def test_reads_dashboard_summary_from_report(tmp_path) -> None:
    path = tmp_path / "report.md"
    path.write_text(
        """# Report

## Recommended Actions

1. **HIGH** - Review funding.
   Reason: A funding gap remains.
2. **LOW** - Run again tomorrow.
   Reason: No trade was approved.

## AI Commentary

- Enabled: `True`
- Summary: Portfolio remains guarded.

## Executive Summary

- Total portfolio value: `782.87 USDT`
- Liquid value: `510.14 USDT`
- Locked value: `272.72 USDT` (`34.84%`)

## Risk Decision

- Approved: `False`
- Reason: AI proposal is HOLD.

## Strategy Decision

- Decision: `HOLD`
- Priority: `LOW`
- Summary: No action is recommended.
""",
        encoding="utf-8",
    )

    result = ReportSummaryReader().read(128, "OK", str(path))

    assert result.decision == "HOLD"
    assert result.risk_approved is False
    assert result.portfolio_value == Decimal("782.87")
    assert result.liquid_value == Decimal("510.14")
    assert result.locked_value == Decimal("272.72")
    assert result.ai_summary == "Portfolio remains guarded."
    assert result.ai_enabled is True
    assert len(result.actions) == 2
    assert result.actions[0].priority == "HIGH"


def test_a_run_without_ai_is_read_back_as_such(tmp_path) -> None:
    """The report has always recorded this; the desktop never read it.

    So a run started with the AI summary unticked showed the engine's English
    note under a card headed "Shrnuti od AI", which reads as a malfunction
    rather than as the setting the user chose.
    """
    path = tmp_path / "report.md"
    path.write_text(
        """# Report

## AI Commentary

- Enabled: `False`
- Summary: AI commentary is disabled.
""",
        encoding="utf-8",
    )

    result = ReportSummaryReader().read(129, "OK", str(path))

    assert result.ai_enabled is False
