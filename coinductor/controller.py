from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Property, QThread, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from .application import CoinductorApplication
from .models import DesktopRunResult, RunOptions


class AnalysisWorker(QObject):
    progress = Signal(str, int)
    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, options: RunOptions):
        super().__init__()
        self.options = options

    @Slot()
    def run(self) -> None:
        try:
            result = CoinductorApplication().run_analysis(
                self.options,
                lambda message, percent: self.progress.emit(message, percent),
            )
            self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()


class AppController(QObject):
    busyChanged = Signal()
    stateChanged = Signal()
    actionsChanged = Signal()

    def __init__(self):
        super().__init__()
        self._busy = False
        self._progress = 0
        self._status_text = "Ready for analysis"
        self._decision = "NOT RUN"
        self._decision_summary = "Run an analysis to load the current portfolio state."
        self._portfolio_value = "0.00 USDC"
        self._liquid_value = "0.00 USDC"
        self._locked_value = "0.00 USDC"
        self._risk_state = "Not evaluated"
        self._ai_summary = "No summary available."
        self._report_path = ""
        self._actions: list[dict[str, str]] = []
        self._thread: QThread | None = None
        self._worker: AnalysisWorker | None = None

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(int, notify=stateChanged)
    def progress(self) -> int:
        return self._progress

    @Property(str, notify=stateChanged)
    def statusText(self) -> str:
        return self._status_text

    @Property(str, notify=stateChanged)
    def decision(self) -> str:
        return self._decision

    @Property(str, notify=stateChanged)
    def decisionSummary(self) -> str:
        return self._decision_summary

    @Property(str, notify=stateChanged)
    def portfolioValue(self) -> str:
        return self._portfolio_value

    @Property(str, notify=stateChanged)
    def liquidValue(self) -> str:
        return self._liquid_value

    @Property(str, notify=stateChanged)
    def lockedValue(self) -> str:
        return self._locked_value

    @Property(str, notify=stateChanged)
    def riskState(self) -> str:
        return self._risk_state

    @Property(str, notify=stateChanged)
    def aiSummary(self) -> str:
        return self._ai_summary

    @Property("QVariantList", notify=actionsChanged)
    def actions(self) -> list[dict[str, str]]:
        return self._actions

    @Property(bool, notify=stateChanged)
    def hasReport(self) -> bool:
        return bool(self._report_path)

    @Slot(str, bool, bool, bool)
    def runAnalysis(
        self,
        data_mode: str,
        ai_summary: bool,
        ai_proposals: bool,
        live_preview: bool,
    ) -> None:
        if self._busy:
            return
        self._set_busy(True)
        self._progress = 0
        self._status_text = "Starting analysis"
        self.stateChanged.emit()

        options = RunOptions(
            data_mode=data_mode,
            ai_summary=ai_summary,
            ai_proposals=ai_proposals,
            live_preview=live_preview,
        )
        self._thread = QThread(self)
        self._worker = AnalysisWorker(options)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.completed.connect(self._on_completed)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._clear_worker)
        self._thread.start()

    @Slot()
    def openReport(self) -> None:
        if self._report_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._report_path))

    @Slot(str, int)
    def _on_progress(self, message: str, percent: int) -> None:
        self._status_text = message
        self._progress = percent
        self.stateChanged.emit()

    @Slot(object)
    def _on_completed(self, result: DesktopRunResult) -> None:
        self._decision = result.decision
        self._decision_summary = result.decision_summary
        self._portfolio_value = f"{result.portfolio_value:.2f} USDC"
        self._liquid_value = f"{result.liquid_value:.2f} USDC"
        self._locked_value = f"{result.locked_value:.2f} USDC"
        self._risk_state = "Approved" if result.risk_approved else result.risk_reason
        self._ai_summary = result.ai_summary or "AI summary was not requested."
        self._report_path = str(Path(result.report_path))
        self._actions = [
            {"priority": item.priority, "action": item.action, "reason": item.reason}
            for item in result.actions
        ]
        self._status_text = f"Run {result.run_id} completed"
        self._progress = 100
        self.actionsChanged.emit()
        self.stateChanged.emit()

    @Slot(str)
    def _on_failed(self, message: str) -> None:
        self._status_text = f"Analysis failed: {message}"
        self._progress = 0
        self.stateChanged.emit()

    @Slot()
    def _clear_worker(self) -> None:
        self._worker = None
        self._thread = None
        self._set_busy(False)

    def _set_busy(self, value: bool) -> None:
        if self._busy == value:
            return
        self._busy = value
        self.busyChanged.emit()
