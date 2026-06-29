from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Property, QThread, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from .ai_provider import AiProviderService
from .application import CoinductorApplication
from .assistant import ProviderBackedAssistant
from .asset_policy_store import AssetPolicyStore
from .connection_check import ConnectionCheckService
from .desktop_store import DesktopStore
from .first_portfolio_planner import FirstPortfolioPlanner
from .local_data_reset import LocalDataResetService
from .models import AiProviderHealthResult, ConnectionCheckResult, DesktopRunResult, RunOptions
from .readiness_service import ReadinessService
from .safety_service import SafetyService
from .setup_service import SetupService
from .user_profile_service import UserProfileService


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


class ConnectionCheckWorker(QObject):
    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    @Slot()
    def run(self) -> None:
        try:
            self.completed.emit(ConnectionCheckService().check_binance_read_only())
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()


class AiProviderHealthWorker(QObject):
    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    @Slot()
    def run(self) -> None:
        try:
            self.completed.emit(AiProviderService().health_check())
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()


class AssistantWorker(QObject):
    completed = Signal(str)
    finished = Signal()

    def __init__(self, question: str, snapshot):
        super().__init__()
        self.question = question
        self.snapshot = snapshot

    @Slot()
    def run(self) -> None:
        try:
            self.completed.emit(ProviderBackedAssistant().answer(self.question, self.snapshot))
        finally:
            self.finished.emit()


class AppController(QObject):
    busyChanged = Signal()
    stateChanged = Signal()
    actionsChanged = Signal()
    dataChanged = Signal()
    pageChanged = Signal()
    assistantChanged = Signal()
    setupChanged = Signal()
    connectionChanged = Signal()
    aiProviderChanged = Signal()
    userProfileChanged = Signal()
    safetyChanged = Signal()
    readinessChanged = Signal()
    firstPortfolioPlanChanged = Signal()
    onboardingWizardChanged = Signal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
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
        self._portfolio_assets: list[dict[str, str]] = []
        self._strategies: list[dict[str, str]] = []
        self._run_history: list[dict[str, str]] = []
        self._onboarding_review: list[dict[str, str]] = []
        self._onboarding_review_summary = "Run a real analysis to prepare portfolio classification."
        self._assistant_messages: list[dict[str, str]] = [
            {
                "role": "assistant",
                "text": "Ask me about the latest run, portfolio roles, risk controls, Grid, or Rebalancing.",
            }
        ]
        self._current_page = 0
        self._onboarding_path = ""
        self._checking_connection = False
        self._connection_status = "Not checked"
        self._connection_detail = "Run the read-only check from Settings before live analysis."
        self._checking_ai_provider = False
        self._assistant_busy = False
        self._ai_provider_health_status = "Not checked"
        self._ai_provider_health_detail = "Run an AI provider check after configuring LLM_BASE_URL and LLM_MODEL."
        self._snapshot = DesktopStore().load()
        self._setup_snapshot = SetupService().inspect()
        self._ai_provider_snapshot = AiProviderService().inspect()
        self._user_profile_service = UserProfileService()
        self._user_profile_snapshot = self._user_profile_service.inspect()
        self._onboarding_wizard_visible = not self._user_profile_snapshot.configured
        self._safety_service = SafetyService()
        self._safety_snapshot = self._safety_service.inspect()
        self._readiness_service = ReadinessService()
        self._readiness_snapshot = self._readiness_service.inspect(
            self._setup_snapshot,
            self._user_profile_snapshot,
            self._safety_snapshot,
            self._snapshot,
            self._connection_status,
        )
        self._first_portfolio_planner = FirstPortfolioPlanner()
        self._first_portfolio_plan = self._first_portfolio_planner.plan(
            self._user_profile_service.current_profile("EXISTING_PORTFOLIO")
        )
        self._local_data_reset_snapshot = LocalDataResetService().preview()
        self._asset_policy_store = AssetPolicyStore()
        self._asset_role_overrides = self._asset_policy_store.load()
        self._portfolio_sort_mode = "VALUE_DESC"
        self._thread: QThread | None = None
        self._worker: AnalysisWorker | None = None
        self._connection_thread: QThread | None = None
        self._connection_worker: ConnectionCheckWorker | None = None
        self._ai_provider_thread: QThread | None = None
        self._ai_provider_worker: AiProviderHealthWorker | None = None
        self._assistant_thread: QThread | None = None
        self._assistant_worker: AssistantWorker | None = None
        self._apply_snapshot()

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

    @Property("QVariantList", notify=dataChanged)
    def portfolioAssets(self) -> list[dict[str, str]]:
        return self._portfolio_assets

    @Property(str, notify=dataChanged)
    def portfolioSortMode(self) -> str:
        return getattr(self, "_portfolio_sort_mode", "VALUE_DESC")

    @Property("QVariantList", notify=dataChanged)
    def strategies(self) -> list[dict[str, str]]:
        return self._strategies

    @Property("QVariantList", notify=dataChanged)
    def runHistory(self) -> list[dict[str, str]]:
        return self._run_history

    @Property("QVariantList", notify=assistantChanged)
    def assistantMessages(self) -> list[dict[str, str]]:
        return self._assistant_messages

    @Property(bool, notify=assistantChanged)
    def assistantBusy(self) -> bool:
        return self._assistant_busy

    @Property(int, notify=pageChanged)
    def currentPage(self) -> int:
        return self._current_page

    @Property(bool, notify=onboardingWizardChanged)
    def onboardingWizardVisible(self) -> bool:
        return self._onboarding_wizard_visible

    @Property("QVariantList", notify=setupChanged)
    def setupChecks(self) -> list[dict[str, str]]:
        return list(self._setup_snapshot.checks)

    @Property("QVariantList", constant=True)
    def privacyDataItems(self) -> list[dict[str, str]]:
        return [
            {
                "name": "Binance account data",
                "value": "Read when you run checks",
                "detail": "Balances, Earn/Spot positions, order history, and strategy status are used to build local reports.",
            },
            {
                "name": "Local files",
                "value": "Stored on this PC",
                "detail": ".env secrets, SQLite state, reports, research notes, safety state, and your onboarding profile stay in the project folder.",
            },
            {
                "name": "Cloud AI",
                "value": "Optional",
                "detail": "Data stays local unless you configure a cloud AI provider; then only the selected prompt/report context is sent to that provider.",
            },
            {
                "name": "Execution",
                "value": "Guarded",
                "detail": "Coinductor does not withdraw funds and does not submit live orders from the desktop UI without explicit guarded workflows.",
            },
        ]

    @Property(str, constant=True)
    def localDataResetSummary(self) -> str:
        return self._local_data_reset_snapshot.summary

    @Property("QVariantList", constant=True)
    def localDataResetItems(self) -> list[dict[str, str]]:
        return list(self._local_data_reset_snapshot.items)

    @Property(str, notify=setupChanged)
    def setupSummary(self) -> str:
        if self._setup_snapshot.blocked:
            return f"{self._setup_snapshot.blocked} blocker(s) require attention"
        return f"{self._setup_snapshot.passed} ready, {self._setup_snapshot.warnings} optional item(s)"

    @Property("QVariantList", notify=aiProviderChanged)
    def aiProviderChecks(self) -> list[dict[str, str]]:
        return list(self._ai_provider_snapshot.checks)

    @Property("QVariantList", notify=aiProviderChanged)
    def aiContextSections(self) -> list[dict[str, str]]:
        return list(self._ai_provider_snapshot.context_sections)

    @Property(str, notify=aiProviderChanged)
    def aiProviderSummary(self) -> str:
        return self._ai_provider_snapshot.summary

    @Property(bool, notify=aiProviderChanged)
    def checkingAiProvider(self) -> bool:
        return self._checking_ai_provider

    @Property(str, notify=aiProviderChanged)
    def aiProviderHealthStatus(self) -> str:
        return self._ai_provider_health_status

    @Property(str, notify=aiProviderChanged)
    def aiProviderHealthDetail(self) -> str:
        return self._ai_provider_health_detail

    @Property(str, notify=userProfileChanged)
    def userProfileSummary(self) -> str:
        return self._user_profile_snapshot.summary

    @Property(bool, notify=userProfileChanged)
    def userProfileConfigured(self) -> bool:
        return self._user_profile_snapshot.configured

    @Property("QVariantList", notify=userProfileChanged)
    def userProfileFields(self) -> list[dict[str, str]]:
        return list(self._user_profile_snapshot.fields)

    @Property("QVariantList", notify=userProfileChanged)
    def exchangeOnboardingSteps(self) -> list[dict[str, str]]:
        return list(self._user_profile_snapshot.exchange_steps)

    @Property(str, notify=safetyChanged)
    def safetyStage(self) -> str:
        return self._safety_snapshot.label

    @Property(str, notify=safetyChanged)
    def safetyStageCode(self) -> str:
        return self._safety_snapshot.stage

    @Property(str, notify=safetyChanged)
    def safetyDetail(self) -> str:
        return self._safety_snapshot.detail

    @Property(bool, notify=safetyChanged)
    def safetyAllowsLivePreview(self) -> bool:
        return self._safety_snapshot.allows_live_preview

    @Property(bool, notify=safetyChanged)
    def safetyAllowsLiveSubmit(self) -> bool:
        return self._safety_snapshot.allows_live_submit

    @Property("QVariantList", notify=safetyChanged)
    def safetyChecks(self) -> list[dict[str, str]]:
        return list(self._safety_snapshot.checks)

    @Property(str, notify=readinessChanged)
    def readinessSummary(self) -> str:
        return self._readiness_snapshot.summary

    @Property(str, notify=readinessChanged)
    def readinessNextStep(self) -> str:
        return self._readiness_snapshot.next_step

    @Property(str, notify=readinessChanged)
    def readinessActionCode(self) -> str:
        return self._readiness_snapshot.action_code

    @Property(str, notify=readinessChanged)
    def readinessActionLabel(self) -> str:
        return self._readiness_snapshot.action_label

    @Property(bool, notify=readinessChanged)
    def readinessActionEnabled(self) -> bool:
        return self._readiness_snapshot.action_enabled and not self._busy

    @Property("QVariantList", notify=readinessChanged)
    def readinessSteps(self) -> list[dict[str, str]]:
        return list(self._readiness_snapshot.steps)

    @Property(bool, notify=firstPortfolioPlanChanged)
    def firstPortfolioPlanAvailable(self) -> bool:
        return self._first_portfolio_plan.available

    @Property(str, notify=firstPortfolioPlanChanged)
    def firstPortfolioPlanSummary(self) -> str:
        return self._first_portfolio_plan.summary

    @Property("QVariantList", notify=firstPortfolioPlanChanged)
    def firstPortfolioFunding(self) -> list[dict[str, str]]:
        return list(self._first_portfolio_plan.funding)

    @Property("QVariantList", notify=firstPortfolioPlanChanged)
    def firstPortfolioAllocation(self) -> list[dict[str, str]]:
        return list(self._first_portfolio_plan.allocation)

    @Property("QVariantList", notify=firstPortfolioPlanChanged)
    def firstPortfolioSteps(self) -> list[dict[str, str]]:
        return list(self._first_portfolio_plan.steps)

    @Property("QVariantList", notify=firstPortfolioPlanChanged)
    def firstPortfolioNotes(self) -> list[dict[str, str]]:
        return list(self._first_portfolio_plan.notes)

    @Property(str, notify=setupChanged)
    def onboardingPath(self) -> str:
        return self._onboarding_path

    @Property("QVariantList", notify=dataChanged)
    def onboardingReview(self) -> list[dict[str, str]]:
        return self._onboarding_review

    @Property(str, notify=dataChanged)
    def onboardingReviewSummary(self) -> str:
        return self._onboarding_review_summary

    @Property("QVariantList", notify=dataChanged)
    def assetRoleOptions(self) -> list[str]:
        return self._asset_policy_store.role_options

    @Property("QVariantList", notify=dataChanged)
    def assetRoleOptionItems(self) -> list[dict[str, str]]:
        return [
            {
                "value": role,
                "label": _humanize_policy_label(role),
                "detail": _role_help(role),
            }
            for role in self._asset_policy_store.role_options
        ]

    @Property(bool, notify=connectionChanged)
    def checkingConnection(self) -> bool:
        return self._checking_connection

    @Property(str, notify=connectionChanged)
    def binanceConnectionStatus(self) -> str:
        return self._connection_status

    @Property(str, notify=connectionChanged)
    def binanceConnectionDetail(self) -> str:
        return self._connection_detail

    @Property(bool, notify=stateChanged)
    def hasReport(self) -> bool:
        return bool(self._report_path)

    @Slot(int)
    def setCurrentPage(self, index: int) -> None:
        if index == self._current_page:
            return
        self._current_page = index
        self.pageChanged.emit()

    @Slot()
    def openOnboardingWizard(self) -> None:
        if self._onboarding_wizard_visible:
            return
        self._onboarding_wizard_visible = True
        self.onboardingWizardChanged.emit()

    @Slot()
    def closeOnboardingWizard(self) -> None:
        if not self._user_profile_snapshot.configured:
            return
        if not self._onboarding_wizard_visible:
            return
        self._onboarding_wizard_visible = False
        self.onboardingWizardChanged.emit()

    @Slot()
    def finishOnboardingWizard(self) -> None:
        self.closeOnboardingWizard()

    @Slot()
    def refreshSetup(self) -> None:
        self._setup_snapshot = SetupService().inspect()
        self._ai_provider_snapshot = AiProviderService().inspect()
        self._user_profile_snapshot = self._user_profile_service.inspect()
        if not self._user_profile_snapshot.configured:
            self._onboarding_wizard_visible = True
        self._safety_snapshot = self._safety_service.inspect()
        self._refresh_readiness()
        self._refresh_first_portfolio_plan()
        self.setupChanged.emit()
        self.aiProviderChanged.emit()
        self.userProfileChanged.emit()
        self.safetyChanged.emit()
        self.readinessChanged.emit()
        self.firstPortfolioPlanChanged.emit()
        self.onboardingWizardChanged.emit()

    @Slot(str)
    def selectOnboardingPath(self, path: str) -> None:
        normalized = path.strip().upper()
        if normalized not in {"EXISTING", "FIRST_PORTFOLIO"}:
            return
        self._onboarding_path = normalized
        self._refresh_first_portfolio_plan()
        self.setupChanged.emit()
        self.firstPortfolioPlanChanged.emit()

    @Slot()
    def useSafeDefaultProfile(self) -> None:
        path = "FIRST_PORTFOLIO" if self._onboarding_path == "FIRST_PORTFOLIO" else "EXISTING_PORTFOLIO"
        self._user_profile_snapshot = self._user_profile_service.save_safe_default(path)
        self._refresh_readiness()
        self._refresh_first_portfolio_plan()
        self.userProfileChanged.emit()
        self.readinessChanged.emit()
        self.firstPortfolioPlanChanged.emit()
        self.onboardingWizardChanged.emit()

    @Slot()
    def deleteUserProfile(self) -> None:
        self._user_profile_snapshot = self._user_profile_service.delete_profile()
        self._onboarding_wizard_visible = True
        self._refresh_readiness()
        self._refresh_first_portfolio_plan()
        self.userProfileChanged.emit()
        self.readinessChanged.emit()
        self.firstPortfolioPlanChanged.emit()
        self.onboardingWizardChanged.emit()

    @Slot(str, str, str, str, str, bool, bool, float, float)
    def saveGuidedProfile(
        self,
        management_style: str,
        automation_level: str,
        run_cadence: str,
        locale: str,
        base_currency: str,
        use_bots: bool,
        allow_spot_trades: bool,
        max_drawdown_comfort_pct: float,
        planned_deposit_amount: float,
    ) -> None:
        path = "FIRST_PORTFOLIO" if self._onboarding_path == "FIRST_PORTFOLIO" else "EXISTING_PORTFOLIO"
        self._user_profile_snapshot = self._user_profile_service.save_guided(
            onboarding_path=path,
            management_style=management_style,
            automation_level=automation_level,
            run_cadence=run_cadence,
            locale=locale,
            base_currency=base_currency,
            use_bots=use_bots,
            allow_spot_trades=allow_spot_trades,
            max_drawdown_comfort_pct=max_drawdown_comfort_pct,
            planned_deposit_amount=planned_deposit_amount,
        )
        self._refresh_readiness()
        self._refresh_first_portfolio_plan()
        self.userProfileChanged.emit()
        self.readinessChanged.emit()
        self.firstPortfolioPlanChanged.emit()
        self.onboardingWizardChanged.emit()

    @Slot()
    def checkBinanceReadOnly(self) -> None:
        if self._checking_connection:
            return
        self._checking_connection = True
        self._connection_status = "Checking"
        self._connection_detail = "Testing Binance read-only permissions..."
        self.connectionChanged.emit()

        self._connection_thread = QThread(self)
        self._connection_worker = ConnectionCheckWorker()
        self._connection_worker.moveToThread(self._connection_thread)
        self._connection_thread.started.connect(self._connection_worker.run)
        self._connection_worker.completed.connect(self._on_connection_completed)
        self._connection_worker.failed.connect(self._on_connection_failed)
        self._connection_worker.finished.connect(self._connection_thread.quit)
        self._connection_worker.finished.connect(self._connection_worker.deleteLater)
        self._connection_thread.finished.connect(self._connection_thread.deleteLater)
        self._connection_thread.finished.connect(self._clear_connection_worker)
        self._connection_thread.start()

    @Slot()
    def checkAiProvider(self) -> None:
        if self._checking_ai_provider:
            return
        self._checking_ai_provider = True
        self._ai_provider_health_status = "Checking"
        self._ai_provider_health_detail = "Testing the configured AI /models endpoint..."
        self.aiProviderChanged.emit()

        self._ai_provider_thread = QThread(self)
        self._ai_provider_worker = AiProviderHealthWorker()
        self._ai_provider_worker.moveToThread(self._ai_provider_thread)
        self._ai_provider_thread.started.connect(self._ai_provider_worker.run)
        self._ai_provider_worker.completed.connect(self._on_ai_provider_completed)
        self._ai_provider_worker.failed.connect(self._on_ai_provider_failed)
        self._ai_provider_worker.finished.connect(self._ai_provider_thread.quit)
        self._ai_provider_worker.finished.connect(self._ai_provider_worker.deleteLater)
        self._ai_provider_thread.finished.connect(self._ai_provider_thread.deleteLater)
        self._ai_provider_thread.finished.connect(self._clear_ai_provider_worker)
        self._ai_provider_thread.start()

    @Slot(str)
    def askAssistant(self, question: str) -> None:
        text = question.strip()
        if not text or self._assistant_busy:
            return
        self._assistant_messages.append({"role": "user", "text": text})
        self._assistant_messages.append({"role": "assistant", "text": "Thinking..."})
        self._assistant_busy = True
        self.assistantChanged.emit()

        self._assistant_thread = QThread(self)
        self._assistant_worker = AssistantWorker(text, self._snapshot)
        self._assistant_worker.moveToThread(self._assistant_thread)
        self._assistant_thread.started.connect(self._assistant_worker.run)
        self._assistant_worker.completed.connect(self._on_assistant_completed)
        self._assistant_worker.finished.connect(self._assistant_thread.quit)
        self._assistant_worker.finished.connect(self._assistant_worker.deleteLater)
        self._assistant_thread.finished.connect(self._assistant_thread.deleteLater)
        self._assistant_thread.finished.connect(self._clear_assistant_worker)
        self._assistant_thread.start()

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
            live_preview=live_preview and self._safety_snapshot.allows_live_preview,
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
    def runInitialClassification(self) -> None:
        self.runAnalysis("REAL", True, False, True)

    @Slot()
    def executeReadinessAction(self) -> None:
        code = self._readiness_snapshot.action_code
        if code == "CHECK_BINANCE":
            self.checkBinanceReadOnly()
        elif code == "RUN_CLASSIFICATION":
            self.runInitialClassification()
        elif code == "OPEN_PORTFOLIO":
            self.setCurrentPage(1)

    @Slot(str, str)
    def saveAssetRoleOverride(self, asset: str, role: str) -> None:
        self._asset_policy_store.save_role(asset, role)
        self._asset_role_overrides = self._asset_policy_store.load()
        self._portfolio_assets = self._apply_asset_role_overrides(self._snapshot.portfolio_assets)
        self._refresh_onboarding_review()
        self.dataChanged.emit()

    @Slot(str)
    def setPortfolioSortMode(self, mode: str) -> None:
        normalized = mode.strip().upper()
        if normalized not in {"ASSET_ASC", "VALUE_DESC", "VALUE_ASC", "ROLE_ASC"}:
            return
        if normalized == self.portfolioSortMode:
            return
        self._portfolio_sort_mode = normalized
        self._portfolio_assets = self._apply_asset_role_overrides(self._snapshot.portfolio_assets)
        self.dataChanged.emit()

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
        self._snapshot = DesktopStore().load()
        self._asset_role_overrides = self._asset_policy_store.load()
        self._portfolio_assets = self._apply_asset_role_overrides(self._snapshot.portfolio_assets)
        self._strategies = list(self._snapshot.strategies)
        self._run_history = list(self._snapshot.run_history)
        self._refresh_onboarding_review()
        self._refresh_readiness()
        self.actionsChanged.emit()
        self.dataChanged.emit()
        self.stateChanged.emit()
        self.readinessChanged.emit()

    @Slot(str)
    def _on_failed(self, message: str) -> None:
        self._status_text = f"Analysis failed: {message}"
        self._progress = 0
        self.stateChanged.emit()

    @Slot(object)
    def _on_connection_completed(self, result: ConnectionCheckResult) -> None:
        self._connection_status = "Connected" if result.status == "PASS" else "Blocked"
        self._connection_detail = result.detail
        self._refresh_readiness()
        self.connectionChanged.emit()
        self.readinessChanged.emit()

    @Slot(str)
    def _on_connection_failed(self, message: str) -> None:
        self._connection_status = "Blocked"
        self._connection_detail = message
        self._refresh_readiness()
        self.connectionChanged.emit()
        self.readinessChanged.emit()

    @Slot(object)
    def _on_ai_provider_completed(self, result: AiProviderHealthResult) -> None:
        self._ai_provider_health_status = "Connected" if result.status == "PASS" else "Blocked"
        self._ai_provider_health_detail = result.detail
        self._ai_provider_snapshot = AiProviderService().inspect()
        self.aiProviderChanged.emit()

    @Slot(str)
    def _on_ai_provider_failed(self, message: str) -> None:
        self._ai_provider_health_status = "Blocked"
        self._ai_provider_health_detail = message
        self.aiProviderChanged.emit()

    @Slot(str)
    def _on_assistant_completed(self, answer: str) -> None:
        if self._assistant_messages and self._assistant_messages[-1]["text"] == "Thinking...":
            self._assistant_messages[-1] = {"role": "assistant", "text": answer}
        else:
            self._assistant_messages.append({"role": "assistant", "text": answer})
        self.assistantChanged.emit()

    @Slot()
    def _clear_worker(self) -> None:
        self._worker = None
        self._thread = None
        self._set_busy(False)

    @Slot()
    def _clear_connection_worker(self) -> None:
        self._connection_worker = None
        self._connection_thread = None
        self._checking_connection = False
        self.connectionChanged.emit()

    @Slot()
    def _clear_ai_provider_worker(self) -> None:
        self._ai_provider_worker = None
        self._ai_provider_thread = None
        self._checking_ai_provider = False
        self.aiProviderChanged.emit()

    @Slot()
    def _clear_assistant_worker(self) -> None:
        self._assistant_worker = None
        self._assistant_thread = None
        self._assistant_busy = False
        self.assistantChanged.emit()

    def _set_busy(self, value: bool) -> None:
        if self._busy == value:
            return
        self._busy = value
        self.busyChanged.emit()
        self.readinessChanged.emit()

    def _apply_snapshot(self) -> None:
        self._portfolio_assets = self._apply_asset_role_overrides(self._snapshot.portfolio_assets)
        self._strategies = list(self._snapshot.strategies)
        self._run_history = list(self._snapshot.run_history)
        self._refresh_onboarding_review()
        if self._snapshot.latest_run is not None:
            self._on_completed(self._snapshot.latest_run)

    def _refresh_onboarding_review(self) -> None:
        assets = self._portfolio_assets
        if not assets:
            self._onboarding_review_summary = "No real portfolio classification has been loaded yet."
            self._onboarding_review = (
                [
                    {
                        "label": "Portfolio classification",
                        "value": "Not loaded",
                        "detail": "Run initial classification after the read-only connection check passes.",
                    },
                    {
                        "label": "Execution readiness",
                        "value": "Waiting",
                        "detail": "The desktop app can review data before any guarded live action is exposed here.",
                    },
                ]
            )
            return

        role_counts: dict[str, int] = {}
        for asset in assets:
            role = str(asset.get("role", "UNCLASSIFIED") or "UNCLASSIFIED")
            role_counts[role] = role_counts.get(role, 0) + 1
        top_asset = assets[0]
        protected = sum(count for role, count in role_counts.items() if "PROTECTED" in role or "CORE" in role)
        source = sum(count for role, count in role_counts.items() if "SOURCE" in role or "FUNDING" in role)
        tradable = sum(count for role, count in role_counts.items() if "TRADING" in role or "QUOTE" in role)
        dust = sum(count for role, count in role_counts.items() if "DUST" in role or "AIRDROP" in role)
        latest_run = self._snapshot.latest_run.run_id if self._snapshot.latest_run is not None else "unknown"
        self._onboarding_review_summary = (
            f"Latest real classification: run {latest_run}, {len(assets)} tracked asset(s). "
            "Review roles before enabling any guarded execution."
        )
        self._onboarding_review = [
            {
                "label": "Tracked assets",
                "value": str(len(assets)),
                "detail": "Assets from the latest real portfolio valuation.",
            },
            {
                "label": "Largest holding",
                "value": f"{top_asset.get('asset', 'UNKNOWN')} {top_asset.get('value', '')}".strip(),
                "detail": str(top_asset.get("role", "UNCLASSIFIED")),
            },
            {
                "label": "Protected/Core",
                "value": str(protected),
                "detail": "Assets treated as long-term holdings or utility reserves.",
            },
            {
                "label": "Trading/Funding",
                "value": str(tradable + source),
                "detail": "Assets available to strategy logic within configured limits.",
            },
            {
                "label": "Dust/Airdrop",
                "value": str(dust),
                "detail": "Small assets that can be considered for USDC funding when allowed.",
            },
        ]

    def _refresh_readiness(self) -> None:
        self._readiness_snapshot = self._readiness_service.inspect(
            self._setup_snapshot,
            self._user_profile_snapshot,
            self._safety_snapshot,
            self._snapshot,
            self._connection_status,
        )

    def _refresh_first_portfolio_plan(self) -> None:
        fallback = "FIRST_PORTFOLIO" if self._onboarding_path == "FIRST_PORTFOLIO" else "EXISTING_PORTFOLIO"
        self._first_portfolio_plan = self._first_portfolio_planner.plan(
            self._user_profile_service.current_profile(fallback)
        )

    def _apply_asset_role_overrides(self, assets: tuple[dict[str, str], ...]) -> list[dict[str, str]]:
        enriched: list[dict[str, str]] = []
        for item in assets:
            row = dict(item)
            asset = str(row.get("asset", "")).upper()
            base_role = str(row.get("role", "UNCLASSIFIED") or "UNCLASSIFIED").upper()
            override = self._asset_role_overrides.get(asset)
            effective = override or base_role
            row["baseRole"] = base_role
            row["role"] = effective
            row["roleOverride"] = override or "SYSTEM_DEFAULT"
            row["policySource"] = "MANUAL" if override else "SYSTEM"
            row["roleLabel"] = _humanize_policy_label(effective)
            row["baseRoleLabel"] = _humanize_policy_label(base_role)
            row["roleOverrideLabel"] = _humanize_policy_label(row["roleOverride"])
            row["policySourceLabel"] = "Manual override" if override else "System default"
            row["roleHelp"] = _role_help(effective)
            enriched.append(row)
        return self._sort_portfolio_assets(enriched)

    def _sort_portfolio_assets(self, assets: list[dict[str, str]]) -> list[dict[str, str]]:
        mode = self.portfolioSortMode
        if mode == "ASSET_ASC":
            return sorted(assets, key=lambda item: str(item.get("asset", "")))
        if mode == "VALUE_ASC":
            return sorted(assets, key=lambda item: _parse_money_value(str(item.get("value", ""))))
        if mode == "ROLE_ASC":
            return sorted(
                assets,
                key=lambda item: (
                    str(item.get("roleLabel", "")),
                    str(item.get("asset", "")),
                ),
            )
        return sorted(assets, key=lambda item: _parse_money_value(str(item.get("value", ""))), reverse=True)


def _humanize_policy_label(value: str) -> str:
    normalized = (value or "").strip().upper()
    if normalized == "SYSTEM_DEFAULT":
        return "System default"
    return normalized.replace("_", " ").title()


def _role_help(value: str) -> str:
    normalized = (value or "").strip().upper()
    if normalized == "SYSTEM_DEFAULT":
        return "Use the role from the latest portfolio classification."
    if "PROTECTED" in normalized or "CORE" in normalized:
        return "Long-term or utility holding. Coinductor should avoid using it as trading funding."
    if "SOURCE" in normalized or "FUNDING" in normalized:
        return "Funding source that may be used within configured limits."
    if "TRADING" in normalized or "GRID" in normalized or "REBALANC" in normalized:
        return "Asset can be considered by trading or bot recommendation logic."
    if "DUST" in normalized or "AIRDROP" in normalized:
        return "Small or opportunistic balance that can usually be converted to USDC when allowed."
    if "QUOTE" in normalized or "STABLE" in normalized or normalized == "USDC":
        return "Quote/funding currency used to deploy bot capital."
    return "Custom portfolio policy role used by Coinductor risk rules."


def _parse_money_value(value: str) -> float:
    cleaned = value.replace(",", "").replace("USDC", "").replace("USDT", "").replace("$", "").strip()
    try:
        return float(cleaned.split()[0])
    except (ValueError, IndexError):
        return 0.0
