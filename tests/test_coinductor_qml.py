from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import qInstallMessageHandler, QUrl
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine

from coinductor.controller import AppController


def test_main_qml_loads(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    messages: list[str] = []

    def capture_message(_mode, _context, message: str) -> None:
        messages.append(message)

    previous_handler = qInstallMessageHandler(capture_message)
    app = QGuiApplication.instance() or QGuiApplication([])
    engine = QQmlApplicationEngine()
    try:
        controller = AppController(engine)
        engine.rootContext().setContextProperty("appController", controller)
        qml_path = Path(__file__).parents[1] / "coinductor" / "qml" / "Main.qml"

        engine.load(QUrl.fromLocalFile(str(qml_path.resolve())))

        assert engine.rootObjects()
        engine.rootObjects()[0].deleteLater()
        app.processEvents()
    finally:
        qInstallMessageHandler(previous_handler)

    assert not any("appController" in message and "null" in message for message in messages)
    assert not any("undefined" in message.lower() for message in messages)


def test_controller_pastes_clipboard_image_as_local_attachment(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    app = QGuiApplication.instance() or QGuiApplication([])
    image = QImage(8, 8, QImage.Format_ARGB32)
    image.fill("#36c98f")
    app.clipboard().setImage(image)
    controller = AppController()

    handled = controller.pasteAssistantImageFromClipboard()

    assert handled is True
    assert controller.assistantAttachment["name"].startswith("clipboard-")
    assert Path(controller.assistantAttachment["path"]).is_file()
    app.clipboard().clear()


def test_controller_switches_wizard_text_language() -> None:
    QGuiApplication.instance() or QGuiApplication([])
    controller = AppController()

    assert controller.wizardLanguage == "en"
    assert controller.wizardText["welcome_title"] == "Welcome to Coinductor"

    controller.setWizardLanguage("cs")

    assert controller.wizardLanguage == "cs"
    assert controller.wizardText["welcome_title"] == "Vítejte v Coinductoru"


def test_controller_switches_app_text_language() -> None:
    QGuiApplication.instance() or QGuiApplication([])
    controller = AppController()

    assert controller.appText["overview_title"] == "Portfolio Overview"

    controller.setWizardLanguage("cs")

    assert controller.appText["overview_title"] == "Přehled portfolia"


def test_main_qml_contains_separate_guarded_trade_and_oco_confirmations() -> None:
    qml_path = Path(__file__).parents[1] / "coinductor" / "qml" / "Main.qml"
    qml = qml_path.read_text(encoding="utf-8")

    assert "CONFIRM_MAINNET_ORDER" in qml
    assert "appController.submitGuardedTrade" in qml
    assert "CONFIRM_MAINNET_OCO" in qml
    assert "appController.submitGuardedOco" in qml
    assert "appController.submitGuardedEarnRedeem" in qml
    assert "CONFIRM_EARN_REDEEM" in qml
    assert "REVIEW_EARN_REDEEM" in qml
    assert "appController.challengeHold" in qml
    assert "appController.manualOverrideSymbols" in qml
    assert "Challenge this HOLD" in qml
    assert "appController.executeLocalDataReset(codes, deleteConfirm.text)" in qml
    assert "This permanently deletes the selected local files" in qml
    assert "appController.checkBinanceLiveTrading" in qml
    assert "Enable mainnet preview" in qml
    assert "Arm guarded actions" in qml
    assert "Enable guarded live submit" in qml
    assert "appController.copyText" in qml
    assert "appController.lockLiveSubmit" in qml
    assert "appController.appText.overview_safety_title" in qml
    assert "appController.hasCompletedRealAnalysis" in qml
    assert "appController.hasReadyLivePreview" in qml
    assert "Layout.row: 2" in qml
    assert "Layout.row: 3" in qml
    assert "Manage live trading API" in qml
    assert "liveApiManagerDialog.open()" in qml
    assert "rightPadding: 18" in qml
    assert "Credentials & Safety" not in qml
    assert "appController.appText.live_api_permissions_verified" in qml
    assert "Last live trade" in qml
    assert "activeActionPlanItem.liveLifecycle.lifecycleSteps" in qml
    assert "contentHeight: actionPlanPageContent.implicitHeight + 72" in qml
    assert "contentHeight: portfolioPageContent.implicitHeight + 72" in qml
    assert "contentHeight: runHistoryPageContent.implicitHeight + 72" in qml
    assert "REVIEW_LIFECYCLE" not in qml
    assert '"Active Strategies"' in qml
    assert "appController.activeStrategiesSummary" in qml
    assert "appController.refreshActiveStrategies()" in qml
    assert "strategyRegistrationDialog.open()" in qml
    assert qml.count("text: appController.appText.import_latest_recommendation_button") == 2
    assert "appController.latestGridRegistrationSuggestion" in qml
    assert "appController.latestRebalancingRegistrationSuggestion" in qml
    assert "appController.appText.grid_import_notice_template.replace" in qml
    assert "appController.registerGridStrategy(" in qml
    assert "appController.registerRebalancingStrategy(" in qml
    assert "appController.updateActiveStrategyStatus(" in qml
    assert "I already applied this status change to the bot in Binance." in qml
    assert "OPEN_ACTIVE_STRATEGIES" in qml
    assert 'text: "Open Active Strategies"' in qml
    assert "appController.appText.verified_matches_bot_checkbox" in qml
    assert "activeStrategyDetailDialog.open()" in qml
    assert "visible: appController.currentPage === 8" in qml
    assert "appController.appText.next_review_title" in qml
    assert "appController.nextReview" in qml
    assert "appController.appText.next_review_run_earlier_if_title" in qml
    assert "appController.appText.next_review_run_earlier_if_description" in qml
    assert "appController.appText.next_review_resolve_before_rerun_title" in qml
    assert "appController.appText.next_review_resolve_before_rerun_description" in qml
    assert "appController.appText.next_review_ai_disclaimer_suffix" in qml
    assert "sourceComponent: nextReviewPanelComponent" in qml
    assert "id: appTourOverlay" in qml
    assert "navigationRepeater.itemAt" in qml
    assert "appController.currentAppTourStep" in qml
    assert "appController.nextAppTourStep()" in qml
    assert "appController.previousAppTourStep()" in qml
    assert "appController.skipAppTour()" in qml
    assert "text: appController.appText.replay_app_tour_button" in qml
    assert "safetyPhraseRow.implicitHeight + 24" in qml
    assert 'safetyAllowsLiveSubmit ? "#ee6b6e"' not in qml
    assert "text: appController.appText.assistant_attach_image_button" in qml
    assert "appController.attachAssistantImage" in qml
    assert "appController.assistantVisionAvailable" in qml
    assert "PlatformDialogs.FileDialog" in qml
    assert "appController.pasteAssistantImageFromClipboard" in qml
    assert "Qt.Key_V" in qml
    assert "TextEdit {\n                                    id: messageText" in qml
    assert "selectByMouse: true" in qml
    assert "persistentSelection: true" in qml
    assert "id: localAiVisionModel" in qml
    assert "appController.aiVisionModel" in qml
    assert "appController.saveLocalAiProvider(localAiBaseUrl.text, localAiModel.text, localAiVisionModel.text)" in qml
    assert "text: appController.appText.configure_ai_models_button" in qml
    assert "id: cloudAiVisionModel" in qml
    assert "appController.saveCloudAiProvider(cloudAiBaseUrl.text, cloudAiModel.text, cloudAiVisionModel.text, cloudAiKey.text)" in qml
    assert "appController.appText.first_portfolio_deployment_title" in qml
    assert "appController.firstPortfolioAllocation" in qml
    assert "appController.firstPortfolioDeploymentProgress" in qml
    assert "appController.runFirstPortfolioTranche(" in qml
    assert "CONFIRM_TESTNET_ORDER" in qml
    assert "id: firstPortfolioBudgetInput" in qml
    assert "id: firstPortfolioDeployDialog" in qml
    assert "appController.appText.first_portfolio_budget_warning" in qml
    assert "appController.discoverLocalAiModels(localAiBaseUrl.text)" in qml
    assert "appController.localAiDiscoveredModels" in qml
    assert '"Detect installed models"' in qml
    assert "localAiModel.text = modelData" in qml
    assert "localAiVisionModel.text = modelData" in qml
    assert "appController.wizardText.ask_ai_title" in qml
    assert "appController.askWizardAssistant(wizardAskAiInput.text, window.wizardSteps[window.wizardStep])" in qml
    assert "appController.wizardAssistantBusy" in qml
    assert "appController.wizardAssistantAnswer" in qml
    assert "appController.wizardText.ask_ai_description" in qml
    assert "appController.wizardText.ask_ai_provider_status_configured" in qml
    assert "appController.wizardText.ask_ai_provider_status_missing" in qml
    assert "appController.appText.overview_title" in qml
    assert "appController.appText.metric_portfolio_help" in qml
    assert "appController.appText.overview_ai_summary_title" in qml
    assert "appController.appText.language_toggle_label" in qml
    assert qml.count('appController.setWizardLanguage("cs")') == 2
    assert "appController.appText.portfolio_title" in qml
    assert "appController.appText.portfolio_col_liquidity" in qml
    assert "appController.appText.portfolio_policy_changed_toast.replace" in qml
    assert "appController.appText.live_actions_title" in qml
    assert "appController.appText.safety_stage_disclaimer" in qml
    assert "appController.appText.safety_next_action_enable_preview" in qml
    assert 'openSafetyStageConfirmation("PREVIEW_ONLY", "Enable mainnet preview")' in qml
    assert 'openSafetyStageConfirmation("ARMED", "Arm guarded actions")' in qml
    assert 'openSafetyStageConfirmation("LIVE_ENABLED", "Enable guarded live submit")' in qml
    assert "text: appController.appText.safety_arm_button" in qml
    assert "appController.appText.action_plan_title" in qml
    assert "appController.appText.legend_ready" in qml
    assert "appController.appText.last_live_trade_label" in qml
    assert 'modelData.primaryLabel || appController.appText.review_button' in qml
    assert "appController.appText.active_strategies_title" in qml
    assert "appController.appText.no_active_bots_title" in qml
    assert "appController.appText.monitoring_evaluation_pending_detail" in qml
    assert "appController.appText.binance_id_label" in qml
    assert "appController.appText.view_details_button" in qml
    assert "appController.appText.run_history_title" in qml
    assert "appController.appText.run_history_description" in qml
    assert "appController.appText.run_history_run_label" in qml
    assert "appController.appText.assistant_title" in qml
    assert "appController.appText.assistant_input_placeholder" in qml
    assert "appController.appText.assistant_send_button" in qml
    assert "appController.appText.assistant_vision_available_note" in qml
    assert "appController.appText.help_guides_title" in qml
    assert "appController.appText.open_guide_button" in qml
    assert "appController.appText.settings_title" in qml
    assert "appController.appText.privacy_data_note" in qml
    assert "appController.appText.safety_baseline_title" in qml
    assert "appController.appText.safety_stage_prefix" in qml
    assert "appController.appText.register_bot_dialog_title" in qml
    assert "appController.appText.tab_spot_grid" in qml
    assert "appController.appText.field_local_name" in qml
    assert "appController.appText.field_target_weights" in qml
    assert "appController.appText.rebalancing_import_notice_template.replace" in qml
    assert "appController.appText.app_tour_quick_tour_label" in qml
    assert "appController.appText.app_tour_finish_button" in qml
    assert "appController.wizardText.welcome_title" in qml
    assert "appController.setWizardLanguage(\"cs\")" in qml
    assert "appController.wizardLanguage" in qml
