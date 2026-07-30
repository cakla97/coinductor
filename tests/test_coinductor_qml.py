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
    assert "appController.appText.challenge_hold_title" in qml
    assert "appController.executeLocalDataReset(codes, deleteConfirm.text)" in qml
    assert "appController.appText.delete_local_data_warning" in qml
    assert "appController.checkBinanceLiveTrading" in qml
    assert "Enable mainnet preview" in qml
    assert "Arm guarded actions" in qml
    assert "Enable guarded live submit" in qml
    assert "appController.copyText" in qml
    assert "appController.lockLiveSubmit" in qml
    assert "appController.appText.overview_safety_title" in qml
    assert "appController.hasCompletedRealAnalysis" in qml
    # Arming deliberately no longer waits for a PREVIEW_READY result: the
    # engine only submits when the preview it computes in that same run is
    # ready, so a historical one guaranteed nothing while making setup
    # impossible on a HOLD day.
    assert "appController.hasReadyLivePreview" not in qml
    assert "Layout.row: 2" in qml
    assert "Layout.row: 3" in qml
    assert "appController.appText.manage_live_api_dialog_title" in qml
    assert "liveApiManagerDialog.open()" in qml
    assert "rightPadding: 18" in qml
    assert "Credentials & Safety" not in qml
    assert "appController.appText.live_api_permissions_verified" in qml
    assert "appController.appText.last_live_trade_label" in qml
    assert "activeActionPlanItem.liveLifecycle.lifecycleSteps" in qml
    assert "contentHeight: actionPlanPageContent.implicitHeight + 72" in qml
    assert "contentHeight: portfolioPageContent.implicitHeight + 72" in qml
    assert "contentHeight: runHistoryPageContent.implicitHeight + 72" in qml
    assert "REVIEW_LIFECYCLE" not in qml
    assert '"Active Strategies"' in qml
    assert "appController.activeStrategiesSummary" in qml
    assert "appController.refreshActiveStrategies()" in qml
    # A swapped button label was the only sign a run was in flight, and it
    # sits still - which reads as a hang on a button that quietly starts a
    # full analysis.
    # BusyDots is the project's own animation; Active Strategies was the one
    # page still without it.
    assert "BusyIndicator" not in qml
    assert qml.count("BusyDots {") >= 5
    assert "appController.appText.refresh_monitoring_tooltip" in qml
    assert "appController.openRunReport(modelData.reportPath)" in qml
    assert "appController.appText.open_run_report_button" in qml
    # The procedure exists to be worked through against Binance in another
    # window; every price in it had to be retyped by eye.
    assert "appController.copyManualSteps(activeActionPlanItem.manualSteps)" in qml
    assert "appController.appText.copy_manual_steps_button" in qml
    assert "selectByMouse: true" in qml
    # Values are elided, so copying is a click; drag-selection is impossible.
    assert "component CopyableValue: Text {" in qml
    # A lower bound, not an exact count: every one of these was added because a
    # value had to be retyped by eye, and the next one should not have to edit
    # this number. The confirmation phrase was the sixth.
    assert qml.count("CopyableValue {") >= 6
    assert 'modelData.value || "-"' not in qml, "a value that cannot be copied"
    assert "appController.copyValue(copyableValue.value)" in qml
    assert "strategyRegistrationDialog.open()" in qml
    assert qml.count("text: appController.appText.import_latest_recommendation_button") == 2
    assert "appController.latestGridRegistrationSuggestion" in qml
    assert "appController.latestRebalancingRegistrationSuggestion" in qml
    assert "appController.appText.grid_import_notice_template.replace" in qml
    assert "appController.registerGridStrategy(" in qml
    assert "appController.registerRebalancingStrategy(" in qml
    assert "appController.updateActiveStrategyStatus(" in qml
    assert "appController.appText.already_applied_status_checkbox" in qml
    assert "OPEN_ACTIVE_STRATEGIES" in qml
    assert "text: appController.appText.open_active_strategies_button" in qml
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
    assert "appController.appText.export_diagnostics_button" in qml
    assert "appController.exportDiagnosticsBundle()" in qml
    assert "function handleGuideLink" in qml
    assert "window.handleGuideLink(link)" in qml
    assert "function onOpenGuideRequested(guideId)" in qml
    assert "appController.appText.safety_baseline_title" in qml
    assert "appController.appText.safety_stage_prefix" in qml
    assert "appController.appText.register_bot_dialog_title" in qml
    assert "appController.appText.tab_spot_grid" in qml
    assert "appController.appText.field_local_name" in qml
    assert "appController.appText.field_target_weights" in qml
    assert "appController.appText.rebalancing_import_notice_template.replace" in qml
    assert "appController.appText.app_tour_quick_tour_label" in qml
    assert "appController.appText.app_tour_finish_button" in qml
    assert "appController.appText.strategy_monitor_note" in qml
    assert "appController.appText.update_local_record_button" in qml
    assert "appController.appText.live_api_dialog_warning" in qml
    assert "appController.appText.save_live_trading_key_button" in qml
    assert "appController.appText.confirm_safety_stage_title" in qml
    assert "appController.appText.confirmation_phrase_prefix" in qml
    assert "appController.appText.change_safety_stage_button" in qml
    assert "appController.appText.action_note_review_only" in qml
    assert "appController.appText.guard_title_trade" in qml
    assert "appController.appText.guard_ready_oco" in qml
    assert "appController.appText.challenge_hold_description" in qml
    assert "appController.appText.locked_button_fallback" in qml
    assert "appController.appText.confirm_live_trade_warning" in qml
    assert "appController.appText.ai_chat_history_title" in qml
    assert "appController.appText.confirm_oco_warning" in qml
    assert "appController.appText.confirm_earn_redeem_warning" in qml
    assert "appController.appText.deploy_tranche_dialog_title_template.replace" in qml
    # The phrase is shown beside the instruction to be copied, not embedded in
    # it to be retyped, so the sentence no longer interpolates the token.
    assert "appController.appText.submit_for_real_prefix" in qml
    assert "appController.copyValue(firstPortfolioDeployDialog.expectedConfirm)" in qml
    assert "appController.appText.mainnet_submit_warning" in qml
    assert "appController.appText.guide_footer_note" in qml
    assert "appController.appText.reset_onboarding_profile_note1" in qml
    assert "appController.appText.delete_everything_checkbox" in qml
    assert "appController.appText.type_delete_to_continue_button" in qml
    assert "appController.appText.start_analysis_button" in qml
    assert "appController.appText.mainnet_preview_locked_checkbox" in qml
    assert "appController.wizardText.next_steps_outside_title" in qml
    assert "appController.wizardText.suggested_first_basket_description" in qml
    assert "appController.appText.app_title" in qml
    assert "appController.appText.safety_summary_live_guarded" in qml
    assert "window.navLabelFor(modelData.page)" in qml
    assert "appController.appText.nav_active_strategies" in qml
    assert "function pageContentWidth()" in qml
    assert "width: window.pageContentWidth()" in qml
    assert "component StatusPill: Rectangle" in qml
    assert "component SectionCard: Rectangle" in qml
    assert "property color panelSunken" in qml
    assert qml.count('"#3a3020"') == 1
    assert "contentHeight: overviewPageContent.implicitHeight + 72" in qml
    assert "contentHeight: helpGuidesPageContent.implicitHeight + 72" in qml
    assert "contentHeight: liveActionsPageContent.implicitHeight + 72" in qml
    assert "contentHeight: settingsPageContent.implicitHeight + 72" in qml
    assert "component AppLogo: Item" in qml
    assert 'text: "C"' not in qml
    assert qml.count("AppLogo {") == 2
    assert "property int radiusMd" in qml
    assert "property int spacingLg" in qml
    assert "appController.wizardText.welcome_title" in qml
    assert "appController.setWizardLanguage(\"cs\")" in qml
    assert "appController.wizardLanguage" in qml


def test_qml_never_compares_against_a_localized_status() -> None:
    """Comparisons must use the untranslated *State properties.

    The *Status properties are display labels: in Czech "Connected" reads
    "Pripojeno", so `binanceConnectionStatus !== "Connected"` is true even when
    connected. That silently left the Finish setup banner up and kept telling a
    verified user to verify their live key.
    """
    qml = (Path(__file__).parents[1] / "coinductor" / "qml" / "Main.qml").read_text(encoding="utf-8")

    localized = ("binanceConnectionStatus", "liveTradingCheckStatus", "testnetCheckStatus")
    offenders = [
        line.strip()
        for line in qml.splitlines()
        for name in localized
        if f"appController.{name}" in line and ("===" in line or "!==" in line)
    ]

    assert not offenders, f"compare against the *State property instead: {offenders}"
