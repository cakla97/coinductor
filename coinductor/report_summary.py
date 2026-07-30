from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import re

from .models import ActionSummary, DesktopRunResult


class ReportSummaryReader:
    def read(self, run_id: int, status: str, report_path: str) -> DesktopRunResult:
        path = Path(report_path)
        text = path.read_text(encoding="utf-8")
        return DesktopRunResult(
            run_id=run_id,
            status=status,
            report_path=str(path.resolve()),
            decision=self._field(text, "Strategy Decision", "Decision", "UNKNOWN"),
            decision_summary=self._field(text, "Strategy Decision", "Summary", ""),
            risk_approved=self._field(text, "Risk Decision", "Approved", "False").lower() == "true",
            risk_reason=self._field(text, "Risk Decision", "Reason", ""),
            portfolio_value=self._amount(text, "Executive Summary", "Total portfolio value"),
            liquid_value=self._amount(text, "Executive Summary", "Liquid value"),
            locked_value=self._amount(text, "Executive Summary", "Locked value"),
            ai_summary=self._field(text, "AI Commentary", "Summary", ""),
            ai_enabled=self._field(text, "AI Commentary", "Enabled", "True").lower() == "true",
            ai_language=self._field(text, "AI Commentary", "Language", "").lower(),
            actions=self._actions(text),
        )

    def _section(self, text: str, heading: str) -> str:
        match = re.search(
            rf"^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
        return match.group("body") if match else ""

    def _field(self, text: str, heading: str, label: str, default: str) -> str:
        section = self._section(text, heading)
        match = re.search(rf"^- {re.escape(label)}:\s*(.+?)\s*$", section, re.MULTILINE)
        if not match:
            return default
        return match.group(1).strip().strip("`")

    def _amount(self, text: str, heading: str, label: str) -> Decimal:
        value = self._field(text, heading, label, "0")
        match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
        return Decimal(match.group(0)) if match else Decimal("0")

    def _actions(self, text: str) -> tuple[ActionSummary, ...]:
        section = self._section(text, "Recommended Actions")
        matches = re.findall(
            r"^\d+\.\s+\*\*(?P<priority>[^*]+)\*\*\s+-\s+(?P<action>.+?)\s*$"
            r"\n\s+Reason:\s+(?P<reason>.+?)\s*$",
            section,
            re.MULTILINE,
        )
        return tuple(ActionSummary(priority, action, reason) for priority, action, reason in matches)
