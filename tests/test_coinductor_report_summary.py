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
    assert len(result.actions) == 2
    assert result.actions[0].priority == "HIGH"
