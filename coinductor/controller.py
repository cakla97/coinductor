from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QObject, Property, QThread, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication, QImageReader

from trading_agent.config import default_config_path, load_config
from trading_agent.storage import Storage

from .ai_provider import AiProviderService, provider_kind
from .app_tour_service import AppTourService
from .assistant import AssistantResponse
from .assistant_history import AssistantHistoryStore
from .asset_policy_store import AssetPolicyStore
from .desktop_store import DesktopStore
from .first_portfolio_planner import FirstPortfolioPlanner
from .diagnostics_service import DiagnosticsService
from .guide_service import GuideService
from .local_data_reset import LocalDataResetService
from .local_ai_recommender import LocalAiRecommender
from .models import AiProviderHealthResult, ConnectionCheckResult, DesktopRunResult, RunOptions, SafetySnapshot
from .readiness_service import ReadinessService
from .profile_choices import profile_choices, toggle_help
from .risk_profile import (
    apply_bots_to_config,
    apply_drawdown_to_config,
    apply_style_to_config,
)
from .safety_service import SafetyService
from .secret_store import SecretStore
from .service_strings import service_text
from .setup_service import SetupService
from .strategy_registration import StrategyRegistrationService
from .ui_strings import DEFAULT_LANGUAGE, UiStringsService
from .user_profile_service import UserProfileService
from .workers import (
    AiModelDiscoveryWorker,
    AiProviderHealthWorker,
    AnalysisWorker,
    AssistantWorker,
    ConnectionCheckWorker,
    FirstPortfolioTrancheWorker,
    LiveTradingCheckWorker,
    TestnetCheckWorker,
)


class AppController(QObject):
    busyChanged = Signal()
    stateChanged = Signal()
    actionsChanged = Signal()
    dataChanged = Signal()
    pageChanged = Signal()
    assistantChanged = Signal()
    setupChanged = Signal()
    connectionChanged = Signal()
    liveTradingCheckChanged = Signal()
    testnetCheckChanged = Signal()
    aiProviderChanged = Signal()
    userProfileChanged = Signal()
    safetyChanged = Signal()
    readinessChanged = Signal()
    notificationRequested = Signal(str)
    openGuideRequested = Signal(str)
    firstPortfolioPlanChanged = Signal()
    onboardingWizardChanged = Signal()
    appTourChanged = Signal()
    localAiRecommendationChanged = Signal()
    localAiDiscoveryChanged = Signal()
    wizardAssistantChanged = Signal()
    wizardLanguageChanged = Signal()
    localDataResetChanged = Signal()
    firstPortfolioDeploymentChanged = Signal()

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
        self._action_plan_items: list[dict[str, object]] = []
        self._portfolio_assets: list[dict[str, str]] = []
        self._strategies: list[dict[str, object]] = []
        self._active_strategies: list[dict[str, object]] = []
        self._active_strategies_summary = "No active strategies are registered."
        self._registered_strategy_count = 0
        self._next_review: dict[str, object] = {}
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
        self._challenged_symbol = ""
        self._challenge_outcome = ""
        self._pending_result_page = 3
        self._pending_completion_message = "Analysis complete. Review the Action Plan."
        self._onboarding_path = ""
        self._checking_connection = False
        self._checking_live_trading = False
        self._checking_testnet = False
        self._checking_ai_provider = False
        self._assistant_busy = False
        # Identifies the in-flight assistant request so a cancelled or
        # superseded reply can be discarded when it eventually arrives.
        self._assistant_token = 0
        self._assistant_accept_token = 0
        self._local_ai_model_recommendations: list[dict[str, str]] = []
        self._discovering_ai_models = False
        self._wizard_language = DEFAULT_LANGUAGE
        self._apply_idle_status_defaults()
        self._local_ai_discovered_models: list[str] = []
        self._snapshot = DesktopStore().load()
        self._setup_snapshot = SetupService(language=self._wizard_language).inspect()
        self._ai_provider_snapshot = AiProviderService(language=self._wizard_language).inspect()
        self._user_profile_service = UserProfileService(language=self._wizard_language)
        self._user_profile_snapshot = self._user_profile_service.inspect()
        self._onboarding_wizard_visible = not self._user_profile_snapshot.configured
        self._app_tour_service = AppTourService()
        self._app_tour_steps: list[dict[str, object]] = [
            {
                "page": 0,
                "navLabel": "Overview",
                "title": "Your portfolio at a glance",
                "detail": "Overview shows the latest portfolio totals, readiness state, safety stage, and the clearest next action.",
                "tip": "Start a normal read-only analysis here. It never submits an order by itself.",
            },
            {
                "page": 2,
                "navLabel": "Portfolio",
                "title": "Review how every asset may be used",
                "detail": "Portfolio lists all detected holdings and their roles, including protected assets, funding sources, trading assets, and dust.",
                "tip": "You can override a role, but Coinductor keeps deterministic risk and funding limits in force.",
            },
            {
                "page": 1,
                "navLabel": "Live Actions",
                "title": "Safety before execution",
                "detail": "Live Actions contains analysis controls, the staged safety lock, and the separate live API management workflow.",
                "tip": "Preview, Armed, and Live Enabled are local gates. Every real order still needs its own confirmation.",
            },
            {
                "page": 3,
                "navLabel": "Action Plan",
                "title": "One place for every run result",
                "detail": "After an analysis, Action Plan consolidates the trade decision, Spot Grid plan, Rebalancing plan, blockers, and next-review timing.",
                "tip": "A READY action can expose a guarded confirmation. HOLD, Watched, and Blocked remain review-only.",
            },
            {
                "page": 4,
                "navLabel": "Active Strategies",
                "title": "Monitor Binance bots you created",
                "detail": "Register the real parameters of an active Grid or Rebalancing Bot so future runs can evaluate its lifecycle and health.",
                "tip": "Coinductor currently guides bot creation in Binance; registration here does not create or modify the bot.",
            },
            {
                "page": 5,
                "navLabel": "Run History",
                "title": "Every past run stays on record",
                "detail": "Run History lists the latest analytical runs with their data mode, status, and decision, so you can trace what happened and when.",
                "tip": "REAL runs read your live Binance account. MOCK runs use example data and never touch it.",
            },
            {
                "page": 6,
                "navLabel": "AI Assistant",
                "title": "Ask for explanations, not permission bypasses",
                "detail": "The assistant can explain reports, portfolio roles, settings, and market context using your configured local or cloud provider.",
                "tip": "AI commentary supports decisions but cannot override deterministic safety gates or submit an action on its own.",
            },
            {
                "page": 7,
                "navLabel": "Help & Guides",
                "title": "Detailed help stays available",
                "detail": "Open the built-in guides whenever you need step-by-step help with Ollama, Binance APIs, safety, or portfolio roles.",
                "tip": "You can replay this tour later from Settings.",
            },
            {
                "page": 8,
                "navLabel": "Settings",
                "title": "Configuration and system status live here",
                "detail": "Settings holds your Binance and AI connections, onboarding profile, privacy controls, and the detailed Safety stage state.",
                "tip": "Nothing here places an order. \"Delete local data\" is currently a preview only and is not executed.",
            },
        ]
        self._assistant_pending_action: dict[str, object] = {}
        self._assistant_origin_page = 0
        self._assistant_history_store = AssistantHistoryStore()
        self._assistant_history = self._assistant_history_store.summaries()
        self._assistant_conversation_id = uuid4().hex
        self._assistant_attachment: dict[str, str] = {}
        self._assistant_vision_available, self._assistant_vision_detail = AiProviderService().vision_support()
        self._wizard_assistant_busy = False
        self._wizard_assistant_question = ""
        self._wizard_assistant_answer = ""
        self._app_tour_step = 0
        self._app_tour_visible = self._user_profile_snapshot.configured and not self._app_tour_service.is_completed()
        self._safety_service = SafetyService(language=self._wizard_language)
        self._safety_snapshot = self._inspect_safety()
        self._readiness_service = ReadinessService(language=self._wizard_language)
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
        self._first_portfolio_deployment_progress: list[dict[str, object]] = self._load_first_portfolio_progress()
        self._guides = GuideService().list_guides(self._wizard_language)
        try:
            self._manual_override_symbols = load_config(default_config_path()).allowed_symbols
        except Exception:
            self._manual_override_symbols = []
        self._local_data_reset_snapshot = LocalDataResetService(language=self._wizard_language).preview()
        self._asset_policy_store = AssetPolicyStore()
        self._asset_role_overrides = self._asset_policy_store.load()
        self._strategy_registration_service = StrategyRegistrationService()
        self._portfolio_sort_mode = "VALUE_DESC"
        self._thread: QThread | None = None
        self._worker: AnalysisWorker | None = None
        self._connection_thread: QThread | None = None
        self._connection_worker: ConnectionCheckWorker | None = None
        self._live_trading_check_thread: QThread | None = None
        self._live_trading_check_worker: LiveTradingCheckWorker | None = None
        self._testnet_check_thread: QThread | None = None
        self._testnet_check_worker: TestnetCheckWorker | None = None
        self._first_portfolio_tranche_thread: QThread | None = None
        self._first_portfolio_tranche_worker: FirstPortfolioTrancheWorker | None = None
        self._ai_provider_thread: QThread | None = None
        self._ai_provider_worker: AiProviderHealthWorker | None = None
        self._ai_model_discovery_thread: QThread | None = None
        self._ai_model_discovery_worker: AiModelDiscoveryWorker | None = None
        self._assistant_thread: QThread | None = None
        self._assistant_worker: AssistantWorker | None = None
        self._wizard_assistant_thread: QThread | None = None
        self._wizard_assistant_worker: AssistantWorker | None = None
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

    @Property("QVariantList", notify=actionsChanged)
    def actionPlanItems(self) -> list[dict[str, object]]:
        return self._action_plan_items

    @Property("QVariantList", notify=dataChanged)
    def portfolioAssets(self) -> list[dict[str, str]]:
        return self._portfolio_assets

    @Property(str, notify=dataChanged)
    def portfolioSortMode(self) -> str:
        return getattr(self, "_portfolio_sort_mode", "VALUE_DESC")

    @Property("QVariantList", notify=dataChanged)
    def strategies(self) -> list[dict[str, object]]:
        return self._strategies

    @Property("QVariantList", notify=dataChanged)
    def activeStrategies(self) -> list[dict[str, object]]:
        return self._active_strategies

    @Property(str, notify=dataChanged)
    def activeStrategiesSummary(self) -> str:
        return self._active_strategies_summary

    @Property(int, notify=dataChanged)
    def registeredStrategyCount(self) -> int:
        return self._registered_strategy_count

    @Property("QVariantList", constant=True)
    def gridRegistrationSymbols(self) -> list[str]:
        return list(self._strategy_registration_service.grid_symbols())

    @Property("QVariantList", constant=True)
    def rebalancingRegistrationAssets(self) -> list[str]:
        return list(self._strategy_registration_service.rebalancing_assets())

    @Property("QVariantList", constant=True)
    def manualOverrideSymbols(self) -> list[str]:
        return list(self._manual_override_symbols)

    @Property("QVariantMap", notify=dataChanged)
    def latestGridRegistrationSuggestion(self) -> dict[str, object]:
        return self._registration_suggestion("Spot Grid")

    @Property("QVariantMap", notify=dataChanged)
    def latestRebalancingRegistrationSuggestion(self) -> dict[str, object]:
        return self._registration_suggestion("Rebalancing")

    @Property("QVariantMap", notify=dataChanged)
    def nextReview(self) -> dict[str, object]:
        return self._next_review

    @Property("QVariantList", notify=dataChanged)
    def runHistory(self) -> list[dict[str, str]]:
        return self._run_history

    @Property("QVariantList", notify=assistantChanged)
    def assistantMessages(self) -> list[dict[str, str]]:
        return self._assistant_messages

    @Property(bool, notify=assistantChanged)
    def assistantBusy(self) -> bool:
        return self._assistant_busy

    @Property(bool, notify=wizardAssistantChanged)
    def wizardAssistantBusy(self) -> bool:
        return self._wizard_assistant_busy

    @Property(str, notify=wizardAssistantChanged)
    def wizardAssistantQuestion(self) -> str:
        return self._wizard_assistant_question

    @Property(str, notify=wizardAssistantChanged)
    def wizardAssistantAnswer(self) -> str:
        return self._wizard_assistant_answer

    @Property(str, notify=wizardLanguageChanged)
    def wizardLanguage(self) -> str:
        return self._wizard_language

    @Property("QVariantMap", notify=wizardLanguageChanged)
    def wizardText(self) -> dict[str, str]:
        return UiStringsService().wizard_text(self._wizard_language)

    def _automation_allows_submit(self) -> bool:
        """Whether the profile's automation level permits submitting anything.

        RECOMMEND_ONLY promises the user that Coinductor "will explain and
        recommend actions, but you decide what to do", so it vetoes every
        submit. Nothing here can grant a permission the safety stage withholds.
        """
        profile = self._user_profile_service.store.load()
        if profile is None:
            return False
        return str(profile.automation_level).strip().upper() == "GUARDED_AUTOMATION"

    def _submit_locked_reason(self, action: str) -> str:
        """Name the lock that is actually holding, not just the stage.

        The automation level vetoes submit through the same flag as the stage,
        so blaming the stage would send a RECOMMEND_ONLY user to the wrong place.
        """
        if not self._automation_allows_submit():
            return service_text("submit_locked_by_profile", self._wizard_language).format(action=action)
        return service_text("submit_locked_by_stage", self._wizard_language).format(action=action)

    def _spot_trades_allowed(self) -> bool:
        """Whether the profile lets Coinductor submit a spot buy at all."""
        profile = self._user_profile_service.store.load()
        return bool(profile is not None and profile.allow_spot_trades)

    @Property(bool, notify=userProfileChanged)
    def spotTradesAllowed(self) -> bool:
        return self._spot_trades_allowed()

    def _inspect_safety(self) -> SafetySnapshot:
        self._safety_service.automation_allows_submit = self._automation_allows_submit()
        return self._safety_service.inspect()

    @Property(bool, notify=safetyChanged)
    def automationAllowsSubmit(self) -> bool:
        return self._safety_service.automation_allows_submit

    @Property("QVariantMap", notify=userProfileChanged)
    def savedProfileChoices(self) -> dict[str, object]:
        """The stored profile in wizard terms, so reopening it shows the truth.

        Empty when nothing is saved yet; the wizard then keeps its own defaults.
        """
        profile = self._user_profile_service.store.load()
        if profile is None:
            return {}
        return {
            "style": profile.management_style,
            "automation": profile.automation_level,
            "cadence": profile.run_cadence,
            "locale": profile.locale,
            "drawdown": int(profile.max_drawdown_comfort_pct),
            "budget": int(profile.planned_deposit_amount),
            "useBots": profile.use_bots,
            "allowSpotTrades": profile.allow_spot_trades,
        }

    @Property("QVariantMap", notify=wizardLanguageChanged)
    def profileChoices(self) -> dict[str, list[dict[str, object]]]:
        """Decision-profile dropdowns: localized labels plus per-option help."""
        return profile_choices(self._wizard_language)

    @Property("QVariantMap", notify=wizardLanguageChanged)
    def profileToggleHelp(self) -> dict[str, str]:
        return toggle_help(self._wizard_language)

    @Property("QVariantMap", notify=wizardLanguageChanged)
    def appText(self) -> dict[str, str]:
        return UiStringsService().app_text(self._wizard_language)

    def _status_display(self, status: str) -> str:
        """Localize a check status for display only.

        The stored status stays English because guarded-action gates compare it
        verbatim (e.g. `_live_trading_check_status == "Verified"`); translating
        the stored value would silently disable those gates.
        """
        key = {
            "Not checked": "status_not_checked",
            "Checking": "status_checking",
            "Connected": "status_connected",
            "Verified": "status_verified",
            "Blocked": "status_blocked",
        }.get(status)
        return service_text(key, self._wizard_language) if key else status

    # (status attribute, detail attribute, idle detail key)
    _IDLE_STATUS_FIELDS = (
        ("_connection_status", "_connection_detail", "connection_idle_detail"),
        ("_live_trading_check_status", "_live_trading_check_detail", "live_trading_idle_detail"),
        ("_testnet_check_status", "_testnet_check_detail", "testnet_idle_detail"),
        ("_ai_provider_health_status", "_ai_provider_health_detail", "ai_provider_idle_detail"),
        ("_local_ai_discovery_status", "_local_ai_discovery_detail", "ai_discovery_idle_detail"),
    )

    def _apply_idle_status_defaults(self, only_unchecked: bool = False) -> None:
        """Reset checks to their idle status and localized explanatory detail.

        With ``only_unchecked`` (used when the language changes) checks that
        already ran keep their result: re-running them is a network call, and
        clearing a "Verified" live key would silently revoke guarded-action
        access just because the user switched language.
        """
        language = self._wizard_language
        for status_attr, detail_attr, detail_key in self._IDLE_STATUS_FIELDS:
            if only_unchecked and getattr(self, status_attr, "Not checked") != "Not checked":
                continue
            setattr(self, status_attr, "Not checked")
            setattr(self, detail_attr, service_text(detail_key, language))
        if not only_unchecked or not self._local_ai_model_recommendations:
            self._local_ai_hardware_summary = service_text("hardware_not_scanned", language)

    @Slot(str)
    def setWizardLanguage(self, language: str) -> None:
        normalized = language.strip().lower()
        if normalized == self._wizard_language:
            return
        self._wizard_language = normalized
        self._guides = GuideService().list_guides(normalized)
        # Re-resolve locally computed text. Checks that already ran keep their
        # result; only never-run checks get their idle text re-localized.
        self._apply_idle_status_defaults(only_unchecked=True)
        self._setup_snapshot = SetupService(language=normalized).inspect()
        self._ai_provider_snapshot = AiProviderService(language=normalized).inspect()
        self._user_profile_service.language = normalized
        self._user_profile_snapshot = self._user_profile_service.inspect()
        self._safety_service.language = normalized
        self._safety_snapshot = self._inspect_safety()
        self._local_data_reset_snapshot = LocalDataResetService(language=normalized).preview()
        self._readiness_service.language = normalized
        self._refresh_readiness()
        self.readinessChanged.emit()
        self.wizardLanguageChanged.emit()
        self.setupChanged.emit()
        self.connectionChanged.emit()
        self.aiProviderChanged.emit()
        self.userProfileChanged.emit()
        self.safetyChanged.emit()
        self.localDataResetChanged.emit()
        # These carry their own notify signal, so QML keeps the previous
        # language until they are emitted too.
        self.liveTradingCheckChanged.emit()
        self.testnetCheckChanged.emit()
        self.localAiDiscoveryChanged.emit()

    @Property("QVariantMap", notify=assistantChanged)
    def assistantPendingAction(self) -> dict[str, object]:
        return self._assistant_pending_action

    @Property(str, notify=assistantChanged)
    def assistantContextPage(self) -> str:
        return self._page_label(self._assistant_origin_page)

    @Property("QVariantList", notify=assistantChanged)
    def assistantHistory(self) -> list[dict[str, object]]:
        return self._assistant_history

    @Property("QVariantMap", notify=assistantChanged)
    def assistantAttachment(self) -> dict[str, str]:
        return self._assistant_attachment

    @Property(bool, notify=assistantChanged)
    def assistantVisionAvailable(self) -> bool:
        return self._assistant_vision_available

    @Property(str, notify=assistantChanged)
    def assistantVisionDetail(self) -> str:
        return self._assistant_vision_detail

    @Property(int, notify=pageChanged)
    def currentPage(self) -> int:
        return self._current_page

    @Property(bool, notify=onboardingWizardChanged)
    def onboardingWizardVisible(self) -> bool:
        return self._onboarding_wizard_visible

    @Property(bool, notify=appTourChanged)
    def appTourVisible(self) -> bool:
        return self._app_tour_visible

    @Property(int, notify=appTourChanged)
    def appTourStep(self) -> int:
        return self._app_tour_step

    @Property(int, constant=True)
    def appTourStepCount(self) -> int:
        return len(self._app_tour_steps)

    @Property("QVariantMap", notify=appTourChanged)
    def currentAppTourStep(self) -> dict[str, object]:
        return dict(self._app_tour_steps[self._app_tour_step])

    @Property("QVariantList", notify=setupChanged)
    def setupChecks(self) -> list[dict[str, str]]:
        return list(self._setup_snapshot.checks)

    @Property(bool, notify=setupChanged)
    def binanceReadOnlyConfigured(self) -> bool:
        """Whether read-only credentials exist, regardless of this session's check.

        A check result is deliberately not persisted - it is a live proof, not a
        stored claim - so after a restart nothing has been verified yet. That is
        not a setup gap, so the Finish setup banner must not call it one.
        """
        return any(
            check.get("code") == "BINANCE_READONLY" and check.get("status") == "PASS"
            for check in self._setup_snapshot.checks
        )

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

    @Property("QVariantList", notify=wizardLanguageChanged)
    def guides(self) -> list[dict[str, str]]:
        return list(self._guides)

    @Property(str, notify=localDataResetChanged)
    def localDataResetSummary(self) -> str:
        return self._local_data_reset_snapshot.summary

    @Property("QVariantList", notify=localDataResetChanged)
    def localDataResetItems(self) -> list[dict[str, str]]:
        return list(self._local_data_reset_snapshot.items)

    @Property(str, notify=setupChanged)
    def setupSummary(self) -> str:
        if self._setup_snapshot.blocked:
            return f"{self._setup_snapshot.blocked} blocker(s) require attention"
        return f"{self._setup_snapshot.passed} ready, {self._setup_snapshot.warnings} optional item(s)"

    @Property(str, notify=setupChanged)
    def liveTradingKeyStatus(self) -> str:
        return self._setup_check("BINANCE_LIVE").get("status", "WARN")

    @Property(str, notify=setupChanged)
    def liveTradingKeyDetail(self) -> str:
        return self._setup_check("BINANCE_LIVE").get("detail", "Optional; guarded execution only")

    @Property(bool, notify=liveTradingCheckChanged)
    def checkingLiveTrading(self) -> bool:
        return self._checking_live_trading

    @Property(str, notify=liveTradingCheckChanged)
    def liveTradingCheckStatus(self) -> str:
        return self._status_display(self._live_trading_check_status)

    @Property(str, notify=liveTradingCheckChanged)
    def liveTradingCheckState(self) -> str:
        """Untranslated status for QML comparisons; use *Status for display."""
        return self._live_trading_check_status

    @Property(str, notify=liveTradingCheckChanged)
    def liveTradingCheckDetail(self) -> str:
        return self._live_trading_check_detail

    @Property(bool, notify=testnetCheckChanged)
    def checkingTestnet(self) -> bool:
        return self._checking_testnet

    @Property(str, notify=testnetCheckChanged)
    def testnetCheckStatus(self) -> str:
        return self._status_display(self._testnet_check_status)

    @Property(str, notify=testnetCheckChanged)
    def testnetCheckState(self) -> str:
        return self._testnet_check_status

    @Property(str, notify=testnetCheckChanged)
    def testnetCheckDetail(self) -> str:
        return self._testnet_check_detail

    @Property(bool, notify=dataChanged)
    def hasCompletedRealAnalysis(self) -> bool:
        return self._snapshot.latest_run is not None

    @Property(bool, notify=dataChanged)
    def hasReadyLivePreview(self) -> bool:
        return self._snapshot.has_ready_live_preview

    @Property("QVariantList", notify=aiProviderChanged)
    def aiProviderChecks(self) -> list[dict[str, str]]:
        return list(self._ai_provider_snapshot.checks)

    @Property("QVariantList", notify=aiProviderChanged)
    def aiContextSections(self) -> list[dict[str, str]]:
        return list(self._ai_provider_snapshot.context_sections)

    @Property(str, notify=aiProviderChanged)
    def aiProviderSummary(self) -> str:
        return self._ai_provider_snapshot.summary

    @Property(str, notify=aiProviderChanged)
    def aiProviderBaseUrl(self) -> str:
        return self._ai_provider_snapshot.base_url

    @Property(str, notify=aiProviderChanged)
    def activeAiProviderKind(self) -> str:
        """LOCAL, CLOUD or NONE. Untranslated: QML compares it."""
        return provider_kind(self._ai_provider_snapshot.base_url)

    @Property(str, notify=aiProviderChanged)
    def aiTextModel(self) -> str:
        return self._ai_provider_snapshot.text_model

    @Property(str, notify=aiProviderChanged)
    def aiVisionModel(self) -> str:
        return self._ai_provider_snapshot.vision_model

    @Property(bool, notify=aiProviderChanged)
    def checkingAiProvider(self) -> bool:
        return self._checking_ai_provider

    @Property(str, notify=aiProviderChanged)
    def aiProviderHealthStatus(self) -> str:
        return self._status_display(self._ai_provider_health_status)

    @Property(str, notify=aiProviderChanged)
    def aiProviderHealthState(self) -> str:
        return self._ai_provider_health_status

    @Property(str, notify=aiProviderChanged)
    def aiProviderHealthDetail(self) -> str:
        return self._ai_provider_health_detail

    @Property(str, notify=localAiRecommendationChanged)
    def localAiHardwareSummary(self) -> str:
        return self._local_ai_hardware_summary

    @Property("QVariantList", notify=localAiRecommendationChanged)
    def localAiModelRecommendations(self) -> list[dict[str, str]]:
        return list(self._local_ai_model_recommendations)

    @Property(bool, notify=localAiDiscoveryChanged)
    def discoveringAiModels(self) -> bool:
        return self._discovering_ai_models

    @Property(str, notify=localAiDiscoveryChanged)
    def localAiDiscoveryStatus(self) -> str:
        return self._status_display(self._local_ai_discovery_status)

    @Property(str, notify=localAiDiscoveryChanged)
    def localAiDiscoveryState(self) -> str:
        return self._local_ai_discovery_status

    @Property(str, notify=localAiDiscoveryChanged)
    def localAiDiscoveryDetail(self) -> str:
        return self._local_ai_discovery_detail

    @Property("QVariantList", notify=localAiDiscoveryChanged)
    def localAiDiscoveredModels(self) -> list[str]:
        return list(self._local_ai_discovered_models)

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

    @Property("QVariantList", notify=firstPortfolioDeploymentChanged)
    def firstPortfolioDeploymentProgress(self) -> list[dict[str, object]]:
        return list(self._first_portfolio_deployment_progress)

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
        return self._status_display(self._connection_status)

    @Property(str, notify=connectionChanged)
    def binanceConnectionState(self) -> str:
        return self._connection_status

    @Property(str, notify=connectionChanged)
    def binanceConnectionDetail(self) -> str:
        return self._connection_detail

    @Property(bool, notify=stateChanged)
    def hasReport(self) -> bool:
        return bool(self._report_path)

    @Slot(int)
    def setCurrentPage(self, index: int) -> None:
        if self._app_tour_visible:
            tour_page = int(self._app_tour_steps[self._app_tour_step]["page"])
            if index != tour_page:
                return
        if index == self._current_page:
            return
        if index == 6 and self._current_page != 6:
            self._assistant_origin_page = self._current_page
        self._current_page = index
        self.pageChanged.emit()
        if index == 6:
            self.assistantChanged.emit()

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
        self.setCurrentPage(0)
        if not self._app_tour_service.is_completed():
            self.startAppTour()

    @Slot()
    def startAppTour(self) -> None:
        if self._onboarding_wizard_visible:
            return
        self._app_tour_step = 0
        self._app_tour_visible = True
        self._show_app_tour_step()

    @Slot()
    def previousAppTourStep(self) -> None:
        if not self._app_tour_visible or self._app_tour_step == 0:
            return
        self._app_tour_step -= 1
        self._show_app_tour_step()

    @Slot()
    def nextAppTourStep(self) -> None:
        if not self._app_tour_visible:
            return
        if self._app_tour_step >= len(self._app_tour_steps) - 1:
            self.finishAppTour()
            return
        self._app_tour_step += 1
        self._show_app_tour_step()

    @Slot()
    def skipAppTour(self) -> None:
        self.finishAppTour()

    @Slot()
    def finishAppTour(self) -> None:
        self._app_tour_service.mark_completed()
        self._app_tour_visible = False
        self.appTourChanged.emit()

    def _show_app_tour_step(self) -> None:
        self.setCurrentPage(int(self._app_tour_steps[self._app_tour_step]["page"]))
        self.appTourChanged.emit()

    @Slot()
    def refreshSetup(self) -> None:
        self._setup_snapshot = SetupService(language=self._wizard_language).inspect()
        self._ai_provider_snapshot = AiProviderService(language=self._wizard_language).inspect()
        self._assistant_vision_available, self._assistant_vision_detail = AiProviderService().vision_support()
        self._user_profile_snapshot = self._user_profile_service.inspect()
        if not self._user_profile_snapshot.configured:
            self._onboarding_wizard_visible = True
            self._app_tour_visible = False
        self._safety_snapshot = self._inspect_safety()
        self._refresh_readiness()
        self._refresh_first_portfolio_plan()
        self.setupChanged.emit()
        self.aiProviderChanged.emit()
        self.userProfileChanged.emit()
        self.safetyChanged.emit()
        self.localDataResetChanged.emit()
        self.readinessChanged.emit()
        self.firstPortfolioPlanChanged.emit()
        self.onboardingWizardChanged.emit()
        self.appTourChanged.emit()

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
        self._safety_snapshot = self._inspect_safety()
        self._refresh_readiness()
        self._refresh_first_portfolio_plan()
        self.userProfileChanged.emit()
        self.readinessChanged.emit()
        self.firstPortfolioPlanChanged.emit()
        self.onboardingWizardChanged.emit()
        self.safetyChanged.emit()

    @Slot()
    def deleteUserProfile(self) -> None:
        self._user_profile_snapshot = self._user_profile_service.delete_profile()
        self._safety_snapshot = self._inspect_safety()
        self._app_tour_service.reset()
        self._app_tour_visible = False
        self._onboarding_wizard_visible = True
        self._refresh_readiness()
        self._refresh_first_portfolio_plan()
        self.userProfileChanged.emit()
        self.readinessChanged.emit()
        self.firstPortfolioPlanChanged.emit()
        self.onboardingWizardChanged.emit()
        self.appTourChanged.emit()
        self.safetyChanged.emit()

    @Slot("QVariantList", str, result=bool)
    def executeLocalDataReset(self, codes, confirmation: str) -> bool:
        if self._busy:
            self.notificationRequested.emit("Wait for the current analysis to finish before deleting local data.")
            return False
        if confirmation.strip() != "DELETE":
            self.notificationRequested.emit("Type DELETE exactly to confirm.")
            return False
        selected = [str(code) for code in codes]
        if not selected:
            self.notificationRequested.emit("Select at least one local data group first.")
            return False
        self._local_data_reset_snapshot = LocalDataResetService(language=self._wizard_language).execute(selected)
        self.notificationRequested.emit(self._local_data_reset_snapshot.summary)
        self.localDataResetChanged.emit()
        self.refreshSetup()
        self._snapshot = DesktopStore().load()
        self._apply_snapshot()
        self.dataChanged.emit()
        return True

    @Slot()
    def exportDiagnosticsBundle(self) -> None:
        try:
            path = DiagnosticsService().write_bundle()
        except Exception as exc:
            self.notificationRequested.emit(f"Could not write diagnostics bundle: {type(exc).__name__}")
            return
        self.notificationRequested.emit(f"Diagnostics bundle saved to {path}")

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
        previous = self._user_profile_service.current_profile(path)
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
        self._apply_profile_to_config(
            previous,
            management_style=management_style,
            drawdown_pct=max_drawdown_comfort_pct,
            use_bots=use_bots,
        )
        # The automation level vetoes live submit, so the safety snapshot has to
        # be recomputed here rather than waiting for the next refreshSetup().
        self._safety_snapshot = self._inspect_safety()
        self._refresh_readiness()
        self._refresh_first_portfolio_plan()
        self.userProfileChanged.emit()
        self.readinessChanged.emit()
        self.firstPortfolioPlanChanged.emit()
        self.onboardingWizardChanged.emit()
        self.safetyChanged.emit()

    def _apply_profile_to_config(
        self,
        previous,
        *,
        management_style: str,
        drawdown_pct: float,
        use_bots: bool,
    ) -> None:
        """Materialise the profile choices that own a config value.

        Each choice is written only when it actually changed, so re-saving the
        profile never reverts numbers the user hand-tuned in config.toml.
        """
        config_path = default_config_path()
        language = self._wizard_language

        if management_style.strip().upper() != str(getattr(previous, "management_style", "")).strip().upper():
            changed = apply_style_to_config(config_path, management_style)
            if changed:
                self._notify_config_change(
                    "style_gates_updated", changed, style=management_style.title()
                )

        if float(drawdown_pct or 0) != float(getattr(previous, "max_drawdown_comfort_pct", -1)):
            changed = apply_drawdown_to_config(config_path, drawdown_pct)
            if changed:
                self._notify_config_change("drawdown_limits_updated", changed)

        if bool(use_bots) != bool(getattr(previous, "use_bots", not use_bots)):
            changed = apply_bots_to_config(config_path, use_bots)
            if changed:
                self._notify_config_change(
                    "bots_config_updated",
                    changed,
                    state=service_text(
                        "bots_state_enabled" if use_bots else "bots_state_disabled", language
                    ),
                )

    def _notify_config_change(self, key: str, changed: dict[str, str], **extra: str) -> None:
        detail = ", ".join(f"{name} {value}" for name, value in changed.items())
        self.notificationRequested.emit(
            service_text(key, self._wizard_language).format(changes=detail, **extra)
        )

    def _start_worker(self, worker: QObject, cleanup) -> QThread:
        """Run a worker on its own thread and tear both down when it finishes.

        Every background job in this controller has the same lifecycle, so it
        lives here once. Connect the worker's own result signals before calling
        this; the thread is only started at the end.
        """
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(cleanup)
        thread.start()
        return thread

    @Slot()
    def checkBinanceReadOnly(self) -> None:
        if self._checking_connection:
            return
        self._checking_connection = True
        self._connection_status = "Checking"
        self._connection_detail = "Testing Binance read-only permissions..."
        self.connectionChanged.emit()

        self._connection_worker = ConnectionCheckWorker(self._wizard_language)
        self._connection_worker.completed.connect(self._on_connection_completed)
        self._connection_worker.failed.connect(self._on_connection_failed)
        self._connection_thread = self._start_worker(self._connection_worker, self._clear_connection_worker)

    @Slot()
    def checkAiProvider(self) -> None:
        if self._checking_ai_provider:
            return
        self._checking_ai_provider = True
        self._ai_provider_health_status = "Checking"
        self._ai_provider_health_detail = "Testing the configured AI /models endpoint..."
        self.aiProviderChanged.emit()

        self._ai_provider_worker = AiProviderHealthWorker()
        self._ai_provider_worker.completed.connect(self._on_ai_provider_completed)
        self._ai_provider_worker.failed.connect(self._on_ai_provider_failed)
        self._ai_provider_thread = self._start_worker(self._ai_provider_worker, self._clear_ai_provider_worker)

    @Slot()
    def scanLocalAiHardware(self) -> None:
        snapshot = LocalAiRecommender().inspect()
        self._local_ai_hardware_summary = snapshot.summary
        self._local_ai_model_recommendations = [
            {"model": item.model, "fit": item.fit, "reason": item.reason, "purpose": item.purpose}
            for item in snapshot.recommendations
        ]
        self.localAiRecommendationChanged.emit()

    @Slot(str)
    def discoverLocalAiModels(self, base_url: str) -> None:
        if self._discovering_ai_models:
            return
        if not base_url.strip():
            self.notificationRequested.emit("Enter the endpoint URL before detecting models.")
            return
        self._discovering_ai_models = True
        self._local_ai_discovery_status = "Checking"
        self._local_ai_discovery_detail = "Asking the endpoint which models are installed..."
        self.localAiDiscoveryChanged.emit()

        self._ai_model_discovery_worker = AiModelDiscoveryWorker(base_url)
        self._ai_model_discovery_worker.completed.connect(self._on_ai_model_discovery_completed)
        self._ai_model_discovery_worker.failed.connect(self._on_ai_model_discovery_failed)
        self._ai_model_discovery_thread = self._start_worker(
            self._ai_model_discovery_worker, self._clear_ai_model_discovery_worker
        )

    @Slot(object)
    def _on_ai_model_discovery_completed(self, result) -> None:
        self._local_ai_discovery_status = result.status
        self._local_ai_discovery_detail = result.detail
        self._local_ai_discovered_models = list(result.models)
        self.localAiDiscoveryChanged.emit()

    @Slot(str)
    def _on_ai_model_discovery_failed(self, message: str) -> None:
        self._local_ai_discovery_status = "BLOCK"
        self._local_ai_discovery_detail = message
        self.localAiDiscoveryChanged.emit()

    @Slot()
    def _clear_ai_model_discovery_worker(self) -> None:
        self._ai_model_discovery_worker = None
        self._ai_model_discovery_thread = None
        self._discovering_ai_models = False
        # Without this the button stays on "Detecting..." forever: the flag
        # clears here, after the completion handler's emit, so QML never
        # re-evaluates it. Matches the other check workers.
        self.localAiDiscoveryChanged.emit()

    def _saved_detail(self, backend: str, context_key: str) -> str:
        """Where the credential landed, plus the next step."""
        where = service_text(
            "creds_stored_keychain" if backend == "keychain" else "creds_stored_env",
            self._wizard_language,
        )
        return f"{where} {service_text(context_key, self._wizard_language)}"

    @Slot(str, str)
    def saveBinanceReadOnlyCredentials(self, api_key: str, api_secret: str) -> None:
        backend = SecretStore().set_many(
            {
                "BINANCE_API_KEY": api_key,
                "BINANCE_API_SECRET": api_secret,
            }
        )
        self._connection_status = "Not checked"
        self._connection_detail = self._saved_detail(backend, "creds_readonly_saved")
        self.refreshSetup()
        self.connectionChanged.emit()

    @Slot(str, str)
    def saveBinanceLiveTradingCredentials(self, api_key: str, api_secret: str) -> None:
        backend = SecretStore().set_many(
            {
                "BINANCE_LIVE_TRADE_API_KEY": api_key,
                "BINANCE_LIVE_TRADE_API_SECRET": api_secret,
            }
        )
        self._live_trading_check_status = "Not checked"
        self._live_trading_check_detail = self._saved_detail(backend, "creds_live_saved")
        self.refreshSetup()
        self.liveTradingCheckChanged.emit()

    @Slot()
    def checkBinanceLiveTrading(self) -> None:
        if self._checking_live_trading:
            return
        self._checking_live_trading = True
        self._live_trading_check_status = "Checking"
        self._live_trading_check_detail = "Checking live-key permissions without placing an order..."
        self.liveTradingCheckChanged.emit()

        self._live_trading_check_worker = LiveTradingCheckWorker(self._wizard_language)
        self._live_trading_check_worker.completed.connect(self._on_live_trading_check_completed)
        self._live_trading_check_worker.failed.connect(self._on_live_trading_check_failed)
        self._live_trading_check_thread = self._start_worker(
            self._live_trading_check_worker, self._clear_live_trading_check_worker
        )

    @Slot(str, str)
    def saveBinanceTestnetCredentials(self, api_key: str, api_secret: str) -> None:
        backend = SecretStore().set_many(
            {
                "BINANCE_TESTNET_API_KEY": api_key,
                "BINANCE_TESTNET_API_SECRET": api_secret,
            }
        )
        self._testnet_check_status = "Not checked"
        self._testnet_check_detail = self._saved_detail(backend, "creds_testnet_saved")
        self.refreshSetup()
        self.testnetCheckChanged.emit()

    @Slot()
    def checkBinanceTestnet(self) -> None:
        if self._checking_testnet:
            return
        self._checking_testnet = True
        self._testnet_check_status = "Checking"
        self._testnet_check_detail = "Checking Spot Testnet access with virtual funds..."
        self.testnetCheckChanged.emit()

        self._testnet_check_worker = TestnetCheckWorker(self._wizard_language)
        self._testnet_check_worker.completed.connect(self._on_testnet_check_completed)
        self._testnet_check_worker.failed.connect(self._on_testnet_check_failed)
        self._testnet_check_thread = self._start_worker(self._testnet_check_worker, self._clear_testnet_check_worker)

    @Slot(str, str)
    def promoteSafetyStage(self, target: str, confirmation: str) -> None:
        normalized_target = target.strip().upper()
        if normalized_target == "PREVIEW_ONLY" and self._snapshot.latest_run is None:
            self.notificationRequested.emit("Complete a real read-only analysis before enabling mainnet preview.")
            return
        if normalized_target == "ARMED" and not self._snapshot.has_ready_live_preview:
            self.notificationRequested.emit("Review at least one PREVIEW_READY live trade result before arming guarded actions.")
            return
        self._safety_service.automation_allows_submit = self._automation_allows_submit()
        try:
            self._safety_snapshot = self._safety_service.transition(
                normalized_target,
                confirmation,
                live_key_verified=self._live_trading_check_status == "Verified",
            )
        except ValueError as exc:
            self.notificationRequested.emit(str(exc))
            return
        self._refresh_readiness()
        self._action_plan_items = self._build_action_plan_items()
        self.safetyChanged.emit()
        self.readinessChanged.emit()
        self.actionsChanged.emit()
        next_step = {
            "PREVIEW_ONLY": "Next: prepare a trade preview. HOLD and blocked results remain review-only.",
            "ARMED": "Next: enable guarded live submit when you are ready.",
            "LIVE_ENABLED": "Guarded submit is available only for READY actions in Action Plan.",
        }.get(normalized_target, "")
        self.notificationRequested.emit(f"Safety stage changed to {self._safety_snapshot.label}. {next_step}".strip())

    @Slot(str)
    def copyText(self, text: str) -> None:
        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            self.notificationRequested.emit("Clipboard is not available.")
            return
        clipboard.setText(text)
        self.notificationRequested.emit("Confirmation phrase copied.")

    @Slot()
    def lockLiveSubmit(self) -> None:
        self._safety_service.automation_allows_submit = self._automation_allows_submit()
        self._safety_snapshot = self._safety_service.lock_live_submit()
        self._refresh_readiness()
        self._action_plan_items = self._build_action_plan_items()
        self.safetyChanged.emit()
        self.readinessChanged.emit()
        self.actionsChanged.emit()
        self.notificationRequested.emit("Live submissions locked. Mainnet preview remains available.")

    @Slot(str, str, str)
    def saveLocalAiProvider(self, base_url: str, model: str, vision_model: str) -> None:
        store = SecretStore()
        backend = store.set_many(
            {
                "LLM_BASE_URL": base_url,
                "LLM_MODEL": model,
                "LLM_VISION_MODEL": vision_model,
            }
        )
        # Both panels write the same LLM_* variables, so switching to local
        # would otherwise leave a cloud API key behind - and every request
        # builder attaches it whenever it is set, sending a paid key to
        # whatever is listening on localhost.
        store.clear(("LLM_API_KEY",))
        self._ai_provider_health_status = "Not checked"
        self._ai_provider_health_detail = self._saved_detail(backend, "creds_ai_local_saved")
        self.refreshSetup()
        self.aiProviderChanged.emit()

    @Slot(str, str, str, str)
    def saveCloudAiProvider(self, base_url: str, model: str, vision_model: str, api_key: str) -> None:
        backend = SecretStore().set_many(
            {
                "LLM_BASE_URL": base_url,
                "LLM_MODEL": model,
                "LLM_VISION_MODEL": vision_model,
                "LLM_API_KEY": api_key,
            }
        )
        self._ai_provider_health_status = "Not checked"
        self._ai_provider_health_detail = self._saved_detail(backend, "creds_ai_cloud_saved")
        self.refreshSetup()
        self.aiProviderChanged.emit()

    @Slot(str, str)
    def askWizardAssistant(self, question: str, step_name: str) -> None:
        text = question.strip()
        if not text or self._wizard_assistant_busy:
            return
        self._wizard_assistant_busy = True
        self._wizard_assistant_question = text
        self._wizard_assistant_answer = ""
        self.wizardAssistantChanged.emit()

        self._wizard_assistant_worker = AssistantWorker(
            text,
            self._snapshot,
            {"context_page": f"Setup wizard: {step_name}" if step_name else "Setup wizard"},
            (),
            "",
        )
        self._wizard_assistant_worker.completed.connect(self._on_wizard_assistant_completed)
        self._wizard_assistant_thread = self._start_worker(
            self._wizard_assistant_worker, self._clear_wizard_assistant_worker
        )

    @Slot(object)
    def _on_wizard_assistant_completed(self, response) -> None:
        self._wizard_assistant_answer = response.text
        self.wizardAssistantChanged.emit()

    @Slot()
    def _clear_wizard_assistant_worker(self) -> None:
        self._wizard_assistant_worker = None
        self._wizard_assistant_thread = None
        self._wizard_assistant_busy = False
        self.wizardAssistantChanged.emit()

    @Slot(str)
    def askAssistant(self, question: str) -> None:
        text = question.strip()
        if (not text and not self._assistant_attachment) or self._assistant_busy:
            return
        if self._assistant_attachment and not self._assistant_vision_available:
            self.notificationRequested.emit(self._assistant_vision_detail)
            return
        if not text:
            text = "Describe this image and explain how it relates to Coinductor."
        conversation = tuple(
            {"role": str(item.get("role", "")), "text": str(item.get("text", ""))}
            for item in self._assistant_messages[-8:]
            if item.get("role") in {"user", "assistant"}
        )
        self._assistant_pending_action = {}
        attachment = dict(self._assistant_attachment)
        user_message = {"role": "user", "text": text}
        if attachment:
            user_message.update({"imageUrl": attachment["url"], "imageName": attachment["name"]})
        self._assistant_messages.append(user_message)
        self._assistant_messages.append({"role": "typing", "text": ""})
        self._assistant_busy = True
        self.assistantChanged.emit()

        self._assistant_token += 1
        token = self._assistant_token
        self._assistant_accept_token = token

        self._assistant_worker = AssistantWorker(
            text,
            self._snapshot,
            self._assistant_context(),
            conversation,
            attachment.get("path", ""),
        )
        self._assistant_worker.completed.connect(
            lambda response, request=token: self._on_assistant_completed(response, request)
        )
        # The token keeps a superseded request from clearing a newer one's state.
        self._assistant_thread = self._start_worker(
            self._assistant_worker,
            lambda request=token: self._clear_assistant_worker(request),
        )
        self._assistant_attachment = {}
        self.assistantChanged.emit()

    @Slot()
    def cancelAssistant(self) -> None:
        """Give the chat back to the user without waiting for the answer.

        A blocking HTTP read cannot be interrupted safely, so the request is
        left to finish in the background and its result is discarded instead.
        """
        if not self._assistant_busy:
            return
        self._assistant_accept_token = 0
        if self._assistant_messages and self._assistant_messages[-1].get("role") == "typing":
            self._assistant_messages.pop()
        self._assistant_busy = False
        self._assistant_pending_action = {}
        self.assistantChanged.emit()
        self.notificationRequested.emit(service_text("assistant_cancelled", self._wizard_language))

    @Slot(str)
    def attachAssistantImage(self, image_url: str) -> None:
        local_path = QUrl(image_url).toLocalFile() or image_url
        path = Path(local_path)
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            self.notificationRequested.emit("Choose a PNG, JPEG, or WebP image.")
            return
        if not path.is_file() or path.stat().st_size > 10 * 1024 * 1024:
            self.notificationRequested.emit("The image is missing or exceeds the 10 MB limit.")
            return
        if not QImageReader(str(path)).canRead():
            self.notificationRequested.emit("The selected file is not a readable image.")
            return
        self._set_assistant_attachment(path)

    @Slot(result=bool)
    def pasteAssistantImageFromClipboard(self) -> bool:
        clipboard = QGuiApplication.clipboard()
        if clipboard is None or clipboard.mimeData() is None or not clipboard.mimeData().hasImage():
            return False
        image = clipboard.image()
        if image.isNull():
            return False
        directory = Path("state/assistant_attachments")
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"clipboard-{uuid4().hex}.png"
        if not image.save(str(path), "PNG"):
            self.notificationRequested.emit("The screenshot could not be saved locally.")
            return True
        self._rotate_assistant_attachments(directory)
        self._set_assistant_attachment(path)
        return True

    def _set_assistant_attachment(self, path: Path) -> None:
        self._assistant_attachment = {
            "path": str(path.resolve()),
            "url": QUrl.fromLocalFile(str(path.resolve())).toString(),
            "name": path.name,
            "size": f"{path.stat().st_size / (1024 * 1024):.1f} MB",
        }
        self.assistantChanged.emit()

    def _rotate_assistant_attachments(self, directory: Path, keep: int = 40) -> None:
        files = sorted(
            directory.glob("clipboard-*.png"),
            key=lambda candidate: candidate.stat().st_mtime,
            reverse=True,
        )
        for expired in files[keep:]:
            expired.unlink(missing_ok=True)

    @Slot()
    def clearAssistantAttachment(self) -> None:
        if not self._assistant_attachment:
            return
        self._assistant_attachment = {}
        self.assistantChanged.emit()

    @Slot()
    def newAssistantChat(self) -> None:
        if self._assistant_busy:
            return
        self._assistant_pending_action = {}
        self._assistant_attachment = {}
        self._assistant_conversation_id = uuid4().hex
        self._assistant_messages = [
            {
                "role": "assistant",
                "text": "New chat started. Ask about the current page, latest run, portfolio, or risk controls.",
            }
        ]
        self.assistantChanged.emit()

    @Slot(str)
    def restoreAssistantChat(self, conversation_id: str) -> None:
        if self._assistant_busy:
            return
        record = self._assistant_history_store.get(conversation_id)
        if record is None:
            return
        messages = record.get("messages", [])
        if not isinstance(messages, list):
            return
        self._assistant_conversation_id = conversation_id
        self._assistant_messages = []
        for item in messages:
            if not isinstance(item, dict) or item.get("role") not in {"user", "assistant"}:
                continue
            message = {"role": str(item.get("role", "assistant")), "text": str(item.get("text", ""))}
            if item.get("imageUrl"):
                message.update(
                    {
                        "imageUrl": str(item["imageUrl"]),
                        "imageName": str(item.get("imageName", "Attached image")),
                    }
                )
            self._assistant_messages.append(message)
        self._assistant_pending_action = {}
        self._assistant_attachment = {}
        self._assistant_origin_page = self._page_index(str(record.get("contextPage", "Overview")))
        self.assistantChanged.emit()

    @Slot()
    def dismissAssistantAction(self) -> None:
        if not self._assistant_pending_action:
            return
        self._assistant_pending_action = {}
        self.assistantChanged.emit()

    @Slot()
    def confirmAssistantAction(self) -> None:
        action = dict(self._assistant_pending_action)
        self._assistant_pending_action = {}
        action_type = str(action.get("type", ""))
        if action_type == "NAVIGATE":
            page = int(action.get("page", -1))
            if 0 <= page <= 8:
                self.setCurrentPage(page)
                self.notificationRequested.emit("Page opened from the AI Assistant.")
        elif action_type == "OPEN_REPORT":
            self.openReport()
        elif action_type == "OPEN_GUIDE":
            guide_id = str(action.get("guide_id", ""))
            if guide_id:
                self.openGuideRequested.emit(guide_id)
        elif action_type == "RUN_READ_ONLY_ANALYSIS":
            self._start_analysis(
                "REAL",
                True,
                True,
                False,
                result_page=3,
                completion_message="Read-only analysis complete. Review the Action Plan.",
            )
        elif action_type == "SET_ASSET_ROLE":
            asset = str(action.get("asset", "")).upper()
            role = str(action.get("role", "")).upper()
            known_assets = {str(item.get("asset", "")).upper() for item in self._portfolio_assets}
            if asset in known_assets and role in self._asset_policy_store.role_options:
                self.saveAssetRoleOverride(asset, role)
                self.notificationRequested.emit(f"{asset} role changed to {_humanize_policy_label(role)}.")
        self.assistantChanged.emit()

    @Slot(str, bool, bool, bool)
    def runAnalysis(
        self,
        data_mode: str,
        ai_summary: bool,
        ai_proposals: bool,
        live_preview: bool,
    ) -> None:
        self._start_analysis(
            data_mode,
            ai_summary,
            ai_proposals,
            live_preview,
            result_page=3,
            completion_message="Analysis complete. Review the Action Plan.",
        )

    @Slot()
    def prepareTradePreview(self) -> None:
        self._start_analysis(
            "REAL",
            True,
            True,
            True,
            result_page=3,
            completion_message="Trade preview ready. Review the Action Plan.",
        )

    @Slot()
    def prepareBotPlan(self) -> None:
        self._start_analysis(
            "REAL",
            True,
            True,
            False,
            result_page=3,
            completion_message="Bot plan ready. Review the Action Plan.",
        )

    @Slot(str)
    def challengeHold(self, symbol: str) -> None:
        if self._busy:
            return
        if self._decision != "HOLD":
            self.notificationRequested.emit("Manual override is only available when the current decision is HOLD.")
            return
        normalized = symbol.strip().upper()
        if normalized not in self._manual_override_symbols:
            self.notificationRequested.emit(f"{normalized} is not in the allowed trading symbols.")
            return
        # Keep the user on the screen they launched this from; the detail dialog
        # refreshes in place, so yanking them to the Action Plan only hid what
        # had changed. The completion message is rewritten in _on_completed once
        # the outcome is actually known.
        self._challenged_symbol = normalized
        self._start_analysis(
            "REAL",
            True,
            True,
            True,
            result_page=self._current_page,
            completion_message=f"Manual override evaluated for {normalized}.",
            manual_override_symbol=normalized,
        )

    @Slot(str, float, float, int, str, bool, str)
    def runFirstPortfolioTranche(
        self,
        asset: str,
        target_pct: float,
        total_budget_usdc: float,
        tranches_total: int,
        mode: str,
        submit: bool,
        confirm: str,
    ) -> None:
        if self._busy:
            self.notificationRequested.emit("Wait for the current analysis to finish first.")
            return
        mode_normalized = mode.strip().upper()
        if mode_normalized not in {"TESTNET", "MAINNET"}:
            self.notificationRequested.emit("Mode must be Testnet or Mainnet.")
            return
        if total_budget_usdc <= 0:
            self.notificationRequested.emit("Enter the actual USDC budget for this basket before continuing.")
            return
        if tranches_total <= 0:
            self.notificationRequested.emit("Tranches total must be at least 1.")
            return
        if mode_normalized == "MAINNET" and submit and not self._safety_snapshot.allows_live_submit:
            self.notificationRequested.emit("Mainnet submit is locked until the Safety stage is promoted to LIVE_ENABLED.")
            return

        asset_normalized = asset.strip().upper()
        completed = sum(
            1
            for item in self._first_portfolio_deployment_progress
            if item.get("asset") == asset_normalized
            and item.get("mode") == mode_normalized
            and item.get("submitted")
        )
        tranche_index = completed + 1
        if tranche_index > tranches_total:
            self.notificationRequested.emit(
                f"All {tranches_total} tranche(s) for {asset_normalized} on {mode_normalized} are already complete."
            )
            return

        self._set_busy(True)
        self._status_text = f"Running first portfolio tranche {tranche_index}/{tranches_total} for {asset_normalized}..."
        self.stateChanged.emit()

        self._first_portfolio_tranche_worker = FirstPortfolioTrancheWorker(
            asset=asset_normalized,
            target_pct=Decimal(str(target_pct)),
            total_budget=Decimal(str(total_budget_usdc)),
            tranche_index=tranche_index,
            tranches_total=tranches_total,
            mode=mode_normalized,
            submit=submit,
            confirm=confirm,
        )
        self._first_portfolio_tranche_worker.completed.connect(self._on_first_portfolio_tranche_completed)
        self._first_portfolio_tranche_worker.failed.connect(self._on_first_portfolio_tranche_failed)
        self._first_portfolio_tranche_thread = self._start_worker(
            self._first_portfolio_tranche_worker, self._clear_first_portfolio_tranche_worker
        )

    @Slot(object)
    def _on_first_portfolio_tranche_completed(self, result) -> None:
        self._first_portfolio_deployment_progress = self._load_first_portfolio_progress()
        self.firstPortfolioDeploymentChanged.emit()
        self.notificationRequested.emit(result.message or result.validation_summary or result.status)

    @Slot(str)
    def _on_first_portfolio_tranche_failed(self, message: str) -> None:
        self.notificationRequested.emit(f"First portfolio tranche failed: {message}")

    @Slot()
    def _clear_first_portfolio_tranche_worker(self) -> None:
        self._first_portfolio_tranche_worker = None
        self._first_portfolio_tranche_thread = None
        self._set_busy(False)
        self._status_text = "Ready for analysis"
        self.stateChanged.emit()

    def _start_analysis(
        self,
        data_mode: str,
        ai_summary: bool,
        ai_proposals: bool,
        live_preview: bool,
        *,
        result_page: int,
        completion_message: str,
        live_submit: bool = False,
        live_confirm: str = "",
        oco_submit: bool = False,
        oco_confirm: str = "",
        earn_redeem_submit: bool = False,
        earn_redeem_confirm: str = "",
        manual_override_symbol: str = "",
    ) -> None:
        if self._busy:
            return
        self._pending_result_page = result_page
        self._pending_completion_message = completion_message
        self._set_busy(True)
        self._progress = 0
        self._status_text = "Starting analysis"
        self.stateChanged.emit()

        options = RunOptions(
            data_mode=data_mode,
            ai_summary=ai_summary,
            ai_proposals=ai_proposals,
            live_preview=(live_preview or live_submit) and self._safety_snapshot.allows_live_preview,
            live_submit=live_submit and self._safety_snapshot.allows_live_submit,
            live_confirm=live_confirm.strip(),
            oco_submit=oco_submit and self._safety_snapshot.allows_live_submit,
            oco_confirm=oco_confirm.strip(),
            earn_redeem_submit=earn_redeem_submit and self._safety_snapshot.allows_live_submit,
            earn_redeem_confirm=earn_redeem_confirm.strip(),
            manual_override_symbol=manual_override_symbol.strip(),
        )
        self._worker = AnalysisWorker(options)
        self._worker.progress.connect(self._on_progress)
        self._worker.completed.connect(self._on_completed)
        self._worker.failed.connect(self._on_failed)
        self._thread = self._start_worker(self._worker, self._clear_worker)

    @Slot(str)
    def submitGuardedTrade(self, confirmation: str) -> None:
        if self._busy:
            return
        if not self._safety_snapshot.allows_live_submit:
            self.notificationRequested.emit(self._submit_locked_reason("Live submit"))
            return
        # The profile's spot-trade switch is a separate lock from the stage: a
        # user can arm guarded automation for bots and rebalancing while still
        # keeping Coinductor out of opening spot positions. OCO is deliberately
        # not gated here - it protects a position that is already open.
        if not self._spot_trades_allowed():
            self.notificationRequested.emit(
                service_text("spot_trades_locked_by_profile", self._wizard_language)
            )
            return
        latest_trade = self._snapshot.latest_run.trade_proposal if self._snapshot.latest_run is not None else None
        action = str(latest_trade.get("action", self._decision) if latest_trade else self._decision).upper()
        if action != "BUY":
            self.notificationRequested.emit("Guarded desktop submit currently supports BUY previews only.")
            return
        if confirmation.strip() != "CONFIRM_MAINNET_ORDER":
            self.notificationRequested.emit("Confirmation text did not match CONFIRM_MAINNET_ORDER.")
            return
        self._start_analysis(
            "REAL",
            True,
            True,
            True,
            result_page=3,
            completion_message="Guarded trade submit run complete. Review the Action Plan.",
            live_submit=True,
            live_confirm=confirmation,
        )

    @Slot()
    def refreshActiveStrategies(self) -> None:
        self._start_analysis(
            "REAL",
            False,
            False,
            False,
            result_page=4,
            completion_message="Active strategy monitoring refreshed.",
        )

    @Slot(str, str, str, str, str, str, str, str, str, str, str, str, str, bool, result=bool)
    def registerGridStrategy(
        self,
        name: str,
        binance_bot_id: str,
        symbol: str,
        range_low: str,
        range_high: str,
        grid_count: str,
        grid_type: str,
        investment: str,
        entry_price: str,
        stop_loss: str,
        take_profit: str,
        created_at: str,
        notes: str,
        verified: bool,
    ) -> bool:
        result = self._strategy_registration_service.register_grid(
            name=name,
            binance_bot_id=binance_bot_id,
            symbol=symbol,
            range_low=range_low,
            range_high=range_high,
            grid_count=grid_count,
            grid_type=grid_type,
            investment=investment,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            created_at=created_at,
            notes=notes,
            verified=verified,
        )
        self.notificationRequested.emit(result.message)
        if result.success:
            self._registered_strategy_count = self._strategy_registration_service.registered_count()
            self.dataChanged.emit()
            self.refreshActiveStrategies()
        return result.success

    @Slot(str, str, str, str, str, str, str, str, str, bool, result=bool)
    def registerRebalancingStrategy(
        self,
        name: str,
        binance_bot_id: str,
        assets: str,
        target_weights: str,
        entry_prices: str,
        investment: str,
        threshold: str,
        created_at: str,
        notes: str,
        verified: bool,
    ) -> bool:
        result = self._strategy_registration_service.register_rebalancing(
            name=name,
            binance_bot_id=binance_bot_id,
            assets=assets,
            target_weights=target_weights,
            entry_prices=entry_prices,
            investment=investment,
            threshold=threshold,
            created_at=created_at,
            notes=notes,
            verified=verified,
        )
        self.notificationRequested.emit(result.message)
        if result.success:
            self._registered_strategy_count = self._strategy_registration_service.registered_count()
            self.dataChanged.emit()
            self.refreshActiveStrategies()
        return result.success

    @Slot(str, str, str, bool, result=bool)
    def updateActiveStrategyStatus(
        self,
        strategy_type: str,
        name: str,
        status: str,
        verified: bool,
    ) -> bool:
        result = self._strategy_registration_service.update_status(
            strategy_type=strategy_type,
            name=name,
            status=status,
            verified=verified,
        )
        self.notificationRequested.emit(result.message)
        if result.success:
            self._registered_strategy_count = self._strategy_registration_service.registered_count()
            self.dataChanged.emit()
            self.refreshActiveStrategies()
        return result.success

    @Slot(str)
    def submitGuardedOco(self, confirmation: str) -> None:
        if self._busy:
            return
        if not self._safety_snapshot.allows_live_submit:
            self.notificationRequested.emit(
                self._submit_locked_reason("OCO submit")
            )
            return
        protection = self._snapshot.position_protection or {}
        if not protection.get("canSubmitOco"):
            self.notificationRequested.emit("No READY OCO protection preview is available for submission.")
            return
        if confirmation.strip() != "CONFIRM_MAINNET_OCO":
            self.notificationRequested.emit("Confirmation text did not match CONFIRM_MAINNET_OCO.")
            return
        self._start_analysis(
            "REAL",
            True,
            True,
            True,
            result_page=3,
            completion_message="Guarded OCO protection run complete. Review the Action Plan.",
            oco_submit=True,
            oco_confirm=confirmation,
        )

    @Slot(str)
    def submitGuardedEarnRedeem(self, confirmation: str) -> None:
        if self._busy:
            return
        if not self._safety_snapshot.allows_live_submit:
            self.notificationRequested.emit(
                self._submit_locked_reason("Earn redeem submit")
            )
            return
        earn_redeem = self._snapshot.earn_redeem or {}
        if not earn_redeem.get("canSubmitEarnRedeem"):
            self.notificationRequested.emit("No READY Earn redeem preview is available for submission.")
            return
        if confirmation.strip() != "CONFIRM_EARN_REDEEM":
            self.notificationRequested.emit("Confirmation text did not match CONFIRM_EARN_REDEEM.")
            return
        self._start_analysis(
            "REAL",
            True,
            True,
            True,
            result_page=3,
            completion_message="Guarded Earn redeem run complete. Review the Action Plan.",
            earn_redeem_submit=True,
            earn_redeem_confirm=confirmation,
        )

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
            self.setCurrentPage(2)
        elif code == "OPEN_SETTINGS":
            self.setCurrentPage(8)

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

    @Property(str, notify=actionsChanged)
    def challengeOutcome(self) -> str:
        """Last challenge result, kept so it outlives the toast."""
        return self._challenge_outcome

    def _challenge_outcome_message(self) -> str:
        """Say whether the challenge changed the decision, not just that it ran."""
        symbol = getattr(self, "_challenged_symbol", "")
        if not symbol:
            return ""
        self._challenged_symbol = ""
        if self._decision == "HOLD":
            self._challenge_outcome = service_text(
                "challenge_rejected", self._wizard_language
            ).format(symbol=symbol)
        else:
            self._challenge_outcome = service_text(
                "challenge_accepted", self._wizard_language
            ).format(symbol=symbol, decision=self._decision)
        return self._challenge_outcome

    @Slot(object)
    def _on_completed(self, result: DesktopRunResult) -> None:
        self._hydrate_run_result(result)
        self._progress = 100
        self._snapshot = DesktopStore().load()
        self._asset_role_overrides = self._asset_policy_store.load()
        self._apply_snapshot()
        self._refresh_readiness()
        # Resolve the outcome before emitting: challengeOutcome is notified by
        # actionsChanged, so setting it afterwards left the QML text binding on
        # the stale empty value while `visible` (which also reads busy) had
        # already flipped true - an empty banner.
        message = self._challenge_outcome_message() or self._pending_completion_message
        self._status_text = f"Run {result.run_id} completed - {message}"
        self.actionsChanged.emit()
        self.dataChanged.emit()
        self.stateChanged.emit()
        self.readinessChanged.emit()
        self.setCurrentPage(self._pending_result_page)
        self.notificationRequested.emit(message)

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
    def _on_live_trading_check_completed(self, result: ConnectionCheckResult) -> None:
        self._live_trading_check_status = "Verified" if result.status == "PASS" else "Blocked"
        self._live_trading_check_detail = result.detail
        self._action_plan_items = self._build_action_plan_items()
        self.liveTradingCheckChanged.emit()
        self.actionsChanged.emit()

    @Slot(str)
    def _on_live_trading_check_failed(self, message: str) -> None:
        self._live_trading_check_status = "Blocked"
        self._live_trading_check_detail = message
        self.liveTradingCheckChanged.emit()

    @Slot(object)
    def _on_testnet_check_completed(self, result: ConnectionCheckResult) -> None:
        self._testnet_check_status = "Verified" if result.status == "PASS" else "Blocked"
        self._testnet_check_detail = result.detail
        self.testnetCheckChanged.emit()

    @Slot(str)
    def _on_testnet_check_failed(self, message: str) -> None:
        self._testnet_check_status = "Blocked"
        self._testnet_check_detail = message
        self.testnetCheckChanged.emit()

    @Slot(object)
    def _on_ai_provider_completed(self, result: AiProviderHealthResult) -> None:
        self._ai_provider_health_status = "Connected" if result.status == "PASS" else "Blocked"
        self._ai_provider_health_detail = result.detail
        self._ai_provider_snapshot = AiProviderService(language=self._wizard_language).inspect()
        self.aiProviderChanged.emit()

    @Slot(str)
    def _on_ai_provider_failed(self, message: str) -> None:
        self._ai_provider_health_status = "Blocked"
        self._ai_provider_health_detail = message
        self.aiProviderChanged.emit()

    @Slot(object)
    def _on_assistant_completed(self, response: AssistantResponse, token: int | None = None) -> None:
        # A cancelled or superseded request still finishes in the background;
        # its answer must not land in the conversation.
        if token is not None and token != self._assistant_accept_token:
            return
        answer = response.text
        self._assistant_pending_action = dict(response.proposed_action or {})
        if self._assistant_messages and self._assistant_messages[-1].get("role") == "typing":
            self._assistant_messages[-1] = {"role": "assistant", "text": answer}
        else:
            self._assistant_messages.append({"role": "assistant", "text": answer})
        self._assistant_history_store.save(
            self._assistant_conversation_id,
            self._assistant_messages,
            self.assistantContextPage,
        )
        self._assistant_history = self._assistant_history_store.summaries()
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
    def _clear_live_trading_check_worker(self) -> None:
        self._live_trading_check_worker = None
        self._live_trading_check_thread = None
        self._checking_live_trading = False
        self.liveTradingCheckChanged.emit()

    @Slot()
    def _clear_testnet_check_worker(self) -> None:
        self._testnet_check_worker = None
        self._testnet_check_thread = None
        self._checking_testnet = False
        self.testnetCheckChanged.emit()

    @Slot()
    def _clear_ai_provider_worker(self) -> None:
        self._ai_provider_worker = None
        self._ai_provider_thread = None
        self._checking_ai_provider = False
        self.aiProviderChanged.emit()

    @Slot()
    def _clear_assistant_worker(self, token: int | None = None) -> None:
        if token is not None and token != self._assistant_token:
            return  # a newer request owns the state now
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

    def _assistant_context(self) -> dict[str, object]:
        return {
            "context_page": self._page_label(self._assistant_origin_page),
            "navigation_pages": [
                "Overview", "Live Actions", "Portfolio", "Action Plan", "Active Strategies",
                "Run History", "AI Assistant", "Help & Guides", "Settings",
            ],
            "visible_sidebar_statuses": [
                {
                    "label": "SAFETY",
                    "status": self._safety_snapshot.label,
                    "meaning": "Current local execution gate; it never submits an order by changing stage alone.",
                    "details_page": "Live Actions",
                },
                {
                    "label": "BINANCE",
                    "status": self._connection_status,
                    "meaning": "Read-only Binance API connection check state for the current app session.",
                    "details_page": "Settings",
                },
            ],
            "safety": {
                "stage": self._safety_snapshot.stage,
                "label": self._safety_snapshot.label,
                "detail": self._safety_snapshot.detail,
                "allows_live_preview": self._safety_snapshot.allows_live_preview,
                "allows_live_submit": self._safety_snapshot.allows_live_submit,
            },
            "readiness": {
                "summary": self._readiness_snapshot.summary,
                "next_step": self._readiness_snapshot.next_step,
                "action_code": self._readiness_snapshot.action_code,
                "action_label": self._readiness_snapshot.action_label,
            },
            "binance_read_only": {
                "status": self._connection_status,
                "detail": self._connection_detail,
            },
            "binance_live_key": {
                "status": self._live_trading_check_status,
                "detail": self._live_trading_check_detail,
            },
            "action_plan": [dict(item) for item in self._action_plan_items],
            "active_strategies_summary": self._active_strategies_summary,
            "next_review": dict(self._next_review),
        }

    def _page_label(self, index: int) -> str:
        pages = (
            "Overview",
            "Live Actions",
            "Portfolio",
            "Action Plan",
            "Active Strategies",
            "Run History",
            "AI Assistant",
            "Help & Guides",
            "Settings",
        )
        return pages[index] if 0 <= index < len(pages) else "Unknown"

    def _page_index(self, label: str) -> int:
        pages = (
            "Overview", "Live Actions", "Portfolio", "Action Plan", "Active Strategies",
            "Run History", "AI Assistant", "Help & Guides", "Settings",
        )
        return pages.index(label) if label in pages else 0

    def _apply_snapshot(self) -> None:
        self._portfolio_assets = self._apply_asset_role_overrides(self._snapshot.portfolio_assets)
        self._strategies = list(self._snapshot.strategies)
        self._active_strategies = list(self._snapshot.active_strategies)
        self._active_strategies_summary = self._snapshot.active_strategies_summary
        self._registered_strategy_count = self._strategy_registration_service.registered_count()
        self._next_review = self._enrich_next_review(self._snapshot.next_review)
        pending = max(0, self._registered_strategy_count - len(self._active_strategies))
        if pending:
            suffix = "strategy is" if pending == 1 else "strategies are"
            self._active_strategies_summary += f" {pending} registered {suffix} awaiting a fresh evaluation."
        self._run_history = list(self._snapshot.run_history)
        if self._snapshot.latest_run is not None:
            self._hydrate_run_result(self._snapshot.latest_run)
        self._action_plan_items = self._build_action_plan_items()
        self._refresh_onboarding_review()

    def _hydrate_run_result(self, result: DesktopRunResult) -> None:
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

    def _registration_suggestion(self, strategy_type: str) -> dict[str, object]:
        for strategy in self._strategies:
            if str(strategy.get("type", "")) == strategy_type:
                suggestion = strategy.get("registrationSuggestion", {})
                return dict(suggestion) if isinstance(suggestion, dict) else {}
        return {}

    def _enrich_next_review(self, review: dict[str, object] | None) -> dict[str, object]:
        if review is None:
            return {}
        result = dict(review)
        profile = self._user_profile_service.current_profile("EXISTING_PORTFOLIO")
        cadence_labels = {
            "DAILY": "Daily",
            "TWICE_WEEKLY": "Twice weekly",
            "WEEKLY": "Weekly",
            "MANUAL": "Manual / irregular",
        }
        result["profileCadence"] = cadence_labels.get(profile.run_cadence, profile.run_cadence.replace("_", " ").title())
        return result

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

    def _build_action_plan_items(self) -> list[dict[str, object]]:
        trade_status = self._decision or "NOT RUN"
        trade_tone = "ready" if trade_status in {"BUY", "SELL"} else "watch" if trade_status == "HOLD" else "blocked"
        top_action = self._actions[0]["action"] if self._actions else "No follow-up action recorded yet."
        trade_detail = self._decision_summary or "Run a trade preview to load the latest decision."
        if top_action and top_action not in trade_detail:
            trade_detail = f"{trade_detail} Next: {top_action}"

        latest_trade = self._snapshot.latest_run.trade_proposal if self._snapshot.latest_run is not None else None
        trade_parameters = [
            {"label": "Action", "value": str(latest_trade.get("action", trade_status) if latest_trade else trade_status)},
            {"label": "Symbol", "value": str(latest_trade.get("symbol", "") if latest_trade else "")},
            {"label": "Confidence", "value": str(latest_trade.get("confidence", "") if latest_trade else "")},
            {"label": "Quote amount", "value": str(latest_trade.get("quoteAmount", "") if latest_trade else "")},
        ]
        if latest_trade and latest_trade.get("reason"):
            trade_detail = str(latest_trade["reason"])
        trade_action = str(latest_trade.get("action", trade_status) if latest_trade else trade_status).upper()
        trade_can_submit = trade_tone == "ready" and trade_action == "BUY"
        if not trade_can_submit:
            trade_submit_blocked = "Live submit appears only for BUY previews that pass deterministic checks."
        elif not self._safety_snapshot.allows_live_submit:
            trade_submit_blocked = "Live submit is locked until the Safety stage is promoted to LIVE_ENABLED."
        elif self.liveTradingKeyStatus != "PASS":
            trade_submit_blocked = "Live trading key is not configured or has not passed setup checks."
        elif self._live_trading_check_status != "Verified":
            trade_submit_blocked = "Verify live-key permissions in Live Actions for this app session."
        else:
            trade_submit_blocked = ""

        trade_card = {
            "title": "Trade",
            "status": trade_status,
            "tone": trade_tone,
            "detail": trade_detail,
            "parameters": trade_parameters,
            # A HOLD decision is not "watched", so name it for what it is.
            "primaryLabel": service_text("card_review_trade", self._wizard_language)
            if trade_tone == "ready"
            else service_text("card_why_hold" if trade_status == "HOLD" else "card_why_watched", self._wizard_language)
            if trade_tone == "watch"
            else service_text("card_show_blockers", self._wizard_language),
            "actionCode": "REVIEW_TRADE",
            "canSubmitLive": trade_can_submit,
            "submitEnabled": trade_can_submit
            and self._safety_snapshot.allows_live_submit
            and self.liveTradingKeyStatus == "PASS"
            and self._live_trading_check_status == "Verified",
            "submitLabel": f"Confirm live {trade_action}" if trade_can_submit else "Live submit locked",
            "submitBlockedReason": trade_submit_blocked,
        }
        if self._snapshot.live_action_lifecycle is not None:
            trade_card["liveLifecycle"] = dict(self._snapshot.live_action_lifecycle)
        cards = [trade_card]

        if self._strategies:
            for item in self._strategies:
                status = str(item.get("allowed") or item.get("status") or "UNKNOWN")
                status_upper = status.upper()
                tone = "ready" if status_upper == "READY" else "blocked" if "BLOCK" in status_upper else "watch"
                display_status = "Ready" if tone == "ready" else "Blocked" if tone == "blocked" else "Watched"
                detail = str(item.get("detail", "")).strip()
                cards.append(
                    {
                        "title": str(item.get("type", "Strategy")),
                        "status": display_status,
                        "tone": tone,
                        "detail": detail or "No strategy detail was recorded for the latest run.",
                        "parameters": list(item.get("parameters", ())),
                        "primaryLabel": service_text("card_show_manual_setup", self._wizard_language)
                        if tone == "ready"
                        else service_text("card_why_watched", self._wizard_language)
                        if tone == "watch"
                        else service_text("card_show_blockers", self._wizard_language),
                        "actionCode": "REVIEW_ACTION",
                    }
                )
        else:
            cards.append(
                {
                    "title": "Grid / Rebalancing",
                    "status": "NOT RUN",
                    "tone": "blocked",
                    "detail": "Run a bot plan to prepare Grid and Rebalancing recommendations.",
                    "parameters": [],
                    "primaryLabel": "Run bot plan",
                    "actionCode": "NONE",
                }
            )

        urgent_strategies = [
            item for item in self._active_strategies if str(item.get("health", "")) == "Action required"
        ]
        if urgent_strategies:
            names = ", ".join(str(item.get("name", "Unnamed bot")) for item in urgent_strategies)
            cards.append(
                {
                    "title": "Active bot attention",
                    "status": "Review required",
                    "tone": "blocked",
                    "detail": (
                        f"{len(urgent_strategies)} active bot(s) need lifecycle review: {names}. "
                        "Verify the actual bot in Binance before changing its local monitoring status."
                    ),
                    "parameters": [
                        {
                            "label": str(item.get("type", "Strategy")),
                            "value": f"{item.get('name', 'Unnamed bot')} · {item.get('state', 'Unknown state')}",
                        }
                        for item in urgent_strategies
                    ],
                    "primaryLabel": "Review active bots",
                    "actionCode": "OPEN_ACTIVE_STRATEGIES",
                }
            )

        protection = self._snapshot.position_protection
        if protection is not None:
            card = dict(protection)
            can_submit = bool(card.get("canSubmitOco"))
            if not can_submit:
                blocked_reason = "Protection is already active or the latest OCO preview did not pass validation."
            elif not self._safety_snapshot.allows_live_submit:
                blocked_reason = "OCO submit is locked until the Safety stage is promoted to LIVE_ENABLED."
            elif self.liveTradingKeyStatus != "PASS":
                blocked_reason = "Live trading key is not configured or has not passed setup checks."
            elif self._live_trading_check_status != "Verified":
                blocked_reason = "Verify live-key permissions in Live Actions for this app session."
            else:
                blocked_reason = ""
            card.update(
                {
                    "primaryLabel": "Review protection" if can_submit else "Show protection status",
                    "actionCode": "REVIEW_OCO",
                    "submitEnabled": can_submit
                    and self._safety_snapshot.allows_live_submit
                    and self.liveTradingKeyStatus == "PASS"
                    and self._live_trading_check_status == "Verified",
                    "submitLabel": "Confirm OCO protection",
                    "submitBlockedReason": blocked_reason,
                }
            )
            cards.append(card)

        earn_redeem = self._snapshot.earn_redeem
        if earn_redeem is not None:
            card = dict(earn_redeem)
            can_submit = bool(card.get("canSubmitEarnRedeem"))
            if not can_submit:
                blocked_reason = "The latest Earn redeem plan is not a submittable preview (it is blocked, skipped, or already submitted)."
            elif not self._safety_snapshot.allows_live_submit:
                blocked_reason = "Earn redeem submit is locked until the Safety stage is promoted to LIVE_ENABLED."
            elif self.liveTradingKeyStatus != "PASS":
                blocked_reason = "Live trading key is not configured or has not passed setup checks."
            elif self._live_trading_check_status != "Verified":
                blocked_reason = "Verify live-key permissions in Live Actions for this app session."
            else:
                blocked_reason = ""
            card.update(
                {
                    "primaryLabel": "Review Earn redeem" if can_submit else "Show Earn redeem status",
                    "actionCode": "REVIEW_EARN_REDEEM",
                    "submitEnabled": can_submit
                    and self._safety_snapshot.allows_live_submit
                    and self.liveTradingKeyStatus == "PASS"
                    and self._live_trading_check_status == "Verified",
                    "submitLabel": "Confirm Earn redeem",
                    "submitBlockedReason": blocked_reason,
                }
            )
            cards.append(card)

        return cards

    def _setup_check(self, code: str) -> dict[str, str]:
        # Matched on the stable code: `name` is translated.
        for item in self._setup_snapshot.checks:
            if item.get("code") == code:
                return dict(item)
        return {"code": code, "name": code, "status": "WARN", "detail": "", "group": ""}

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

    def _load_first_portfolio_progress(self) -> list[dict[str, object]]:
        try:
            config = load_config(default_config_path())
            return Storage(config.database_path).get_first_portfolio_progress()
        except Exception:
            return []

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
