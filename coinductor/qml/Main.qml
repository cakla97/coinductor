import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts
import QtQuick.Dialogs as PlatformDialogs

ApplicationWindow {
    id: window
    width: 1240
    height: 860
    minimumWidth: 1180
    minimumHeight: 820
    visible: true
    title: "Coinductor"
    color: "#0f1318"

    // With a schedule running, closing the window hides it rather than ending
    // the process - otherwise the schedule stops the moment you close the
    // window, which is not a schedule. Without one, closing exits as it always
    // has: an app that keeps running unannounced, holding exchange
    // credentials, is not a surprise anyone should get.
    onClosing: function(close) {
        if (appController.keepRunningInTray) {
            close.accepted = false
            window.hide()
            // Said once per close, because an app that keeps running after you
            // closed it has to say so - and because an installer cannot replace
            // a running Coinductor, which is how someone first found out.
            appController.announceTrayHide()
        }
    }
    Material.theme: Material.Dark
    Material.primary: "#36c98f"
    Material.accent: "#36c98f"
    Material.background: "#171d24"
    Material.foreground: "#f2f5f7"
    font.pixelSize: 14

    property color panel: "#171d24"
    property color panelRaised: "#1d252e"
    property color panelSunken: "#12171d"
    property color border: "#2a3540"
    property color textPrimary: "#f2f5f7"
    property color textSecondary: "#9ba8b5"
    property color textTertiary: "#6b7680"
    property color accent: "#36c98f"
    property color warning: "#f1b84b"
    property color danger: "#ee6b6e"
    property color accentSoft: "#17372d"
    property color warningSoft: "#3a3020"
    property color dangerSoft: "#3a2226"

    property int spacingXs: 4
    property int spacingSm: 8
    property int spacingMd: 12
    property int spacingLg: 16
    property int spacingXl: 24
    property int spacingXxl: 32

    property int radiusSm: 8
    property int radiusMd: 12
    property int radiusLg: 16
    property int radiusPill: 999

    property int textSizeCaption: 11
    property int textSizeBody: 13
    property int textSizeLabel: 12
    property int textSizeSubtitle: 15
    property int textSizeSectionTitle: 18
    property int textSizePageTitle: 26

    function pageContentWidth() {
        return Math.max(window.width - 248 - 28 - 28, 640)
    }

    property string toastText: ""
    property int wizardStep: 0
    property bool profileChoicesEdited: false
    property string fundingCurrency: "USDC"
    property var activeGuide: ({})
    property var activeActionPlanItem: ({})
    // Remembered so the open dialog can re-resolve its item after a run
    // rebuilds the list; otherwise it keeps showing pre-run data.
    property string activeActionPlanCode: ""
    property string activeActionPlanTitle: ""

    // A Python tuple reaching a Repeater's model reports "Model size of -1";
    // a real JS array does not. Coerce dynamic sequences through this.
    function toModel(value) {
        return value ? Array.from(value) : []
    }

    function refreshActiveActionPlanItem() {
        if (!actionPlanDetailDialog.visible || activeActionPlanCode === "")
            return
        var items = appController.actionPlanItems
        for (let i = 0; i < items.length; i++) {
            if (items[i].actionCode === activeActionPlanCode && items[i].title === activeActionPlanTitle) {
                activeActionPlanItem = items[i]
                return
            }
        }
    }

    property var activeStrategyItem: ({})
    property string pendingSafetyTarget: ""
    property string pendingSafetyPhrase: ""
    property string firstPortfolioDeployAsset: ""
    property real firstPortfolioDeployTargetPct: 0
    property var wizardSteps: ["Exchange", "Portfolio", "Profile", "AI", "Binance API", "Review"]
    property var navigationItems: [
        { label: "Overview", page: 0 },
        { label: "Portfolio", page: 2 },
        { label: "Live Actions", page: 1 },
        { label: "Action Plan", page: 3 },
        { label: "Active Strategies", page: 4 },
        { label: "Run History", page: 5 },
        { label: "New listings", page: 9 },
        { label: "Automation", page: 10 },
        { label: "AI Assistant", page: 6 },
        { label: "Help & Guides", page: 7 },
        { label: "Settings", page: 8 }
    ]

    function navIndexForPage(page) {
        for (let i = 0; i < navigationItems.length; i++) {
            if (navigationItems[i].page === page)
                return i
        }
        return 0
    }
    function navLabelFor(page) {
        var labels = {
            0: appController.appText.nav_overview,
            2: appController.appText.nav_portfolio,
            1: appController.appText.nav_live_actions,
            3: appController.appText.nav_action_plan,
            4: appController.appText.nav_active_strategies,
            5: appController.appText.nav_run_history,
            9: appController.appText.nav_new_listings,
            10: appController.appText.nav_automation,
            6: appController.appText.nav_ai_assistant,
            7: appController.appText.nav_help_guides,
            8: appController.appText.nav_settings,
        }
        return labels[page] || ""
    }
    function wizardStepLabels() {
        return [
            appController.wizardText.step_name_exchange,
            appController.wizardText.step_name_portfolio,
            appController.wizardText.step_name_profile,
            appController.wizardText.step_name_ai,
            appController.wizardText.step_name_binance_api,
            appController.wizardText.step_name_review,
        ]
    }
    function firstPortfolioProgressCount(asset, mode) {
        var progress = appController.firstPortfolioDeploymentProgress
        var count = 0
        for (let i = 0; i < progress.length; i++) {
            if (progress[i].asset === asset && progress[i].mode === mode && progress[i].submitted)
                count++
        }
        return count
    }
    property var exchangeOptions: [
        { label: "Binance", value: "BINANCE" },
        { label: "Coinbase", value: "COINBASE" }
    ]
    // Labels and help text come from the backend so both languages, and the
    // numbers each choice writes into config.toml, have a single source.
    property var styleOptions: appController.profileChoices.style
    property var automationOptions: appController.profileChoices.automation
    property var cadenceOptions: appController.profileChoices.cadence
    property var drawdownOptions: appController.profileChoices.drawdown
    property var budgetOptions: appController.profileChoices.budget

    function optionHelp(options, value) {
        for (let i = 0; i < options.length; i++) {
            if (options[i].value === value)
                return options[i].help
        }
        return ""
    }

    function showToast(message) {
        toastText = message
        toastPopup.open()
        toastTimer.restart()
    }

    function openSafetyStageConfirmation(target, phrase) {
        pendingSafetyTarget = target
        pendingSafetyPhrase = phrase
        safetyStageConfirmInput.text = ""
        safetyStageConfirmDialog.open()
    }

    function safetyNextActionLabel() {
        if (appController.safetyStageCode === "SETUP")
            return appController.hasCompletedRealAnalysis ? appController.appText.safety_next_action_enable_preview : appController.appText.safety_next_action_run_analysis
        // Key setup comes first because it does not depend on the market. A
        // ready preview needs the analysis to return something tradable, so on
        // a HOLD day this step never completes - and asking for it first left
        // the recommended action re-running the same analysis forever with no
        // other progress available.
        if ((appController.safetyStageCode === "PREVIEW_ONLY" || appController.safetyStageCode === "ARMED")
                && appController.liveTradingKeyStatus !== "PASS")
            return appController.appText.safety_next_action_add_live_key
        if ((appController.safetyStageCode === "PREVIEW_ONLY" || appController.safetyStageCode === "ARMED")
                && appController.liveTradingCheckState !== "Verified")
            return appController.appText.safety_next_action_verify_api
        if (appController.safetyStageCode === "PREVIEW_ONLY")
            return appController.appText.safety_next_action_arm
        if (appController.safetyStageCode === "PREVIEW_ONLY")
            return appController.appText.safety_next_action_arm
        if (appController.safetyStageCode === "ARMED")
            return appController.appText.safety_next_action_enable_submit
        return appController.appText.safety_next_action_open_action_plan
    }

    function runSafetyNextAction() {
        if (appController.safetyStageCode === "SETUP" && !appController.hasCompletedRealAnalysis) {
            runDialog.open()
        } else if (appController.safetyStageCode === "SETUP") {
            openSafetyStageConfirmation("PREVIEW_ONLY", "Enable mainnet preview")
        } else if ((appController.safetyStageCode === "PREVIEW_ONLY" || appController.safetyStageCode === "ARMED")
                   && appController.liveTradingKeyStatus !== "PASS") {
            liveApiManagerDialog.open()
        } else if ((appController.safetyStageCode === "PREVIEW_ONLY" || appController.safetyStageCode === "ARMED")
                   && appController.liveTradingCheckState !== "Verified") {
            appController.checkBinanceLiveTrading()
        } else if (appController.safetyStageCode === "PREVIEW_ONLY") {
            openSafetyStageConfirmation("ARMED", "Arm guarded actions")
        } else if (appController.safetyStageCode === "PREVIEW_ONLY") {
            openSafetyStageConfirmation("ARMED", "Arm guarded actions")
        } else if (appController.safetyStageCode === "ARMED") {
            openSafetyStageConfirmation("LIVE_ENABLED", "Enable guarded live submit")
        } else {
            appController.setCurrentPage(3)
        }
    }

    function selectedValue(comboBox, fallback) {
        return comboBox.currentValue === undefined ? fallback : comboBox.currentValue
    }

    Connections {
        target: appController
        function onNotificationRequested(message) {
            window.showToast(message)
        }
        function onOpenGuideRequested(guideId) {
            window.openGuide(guideId)
        }
        function onActionsChanged() {
            window.refreshActiveActionPlanItem()
        }
    }

    function styleHelp(value) { return optionHelp(styleOptions, value) }
    function automationHelp(value) { return optionHelp(automationOptions, value) }
    function cadenceHelp(value) { return optionHelp(cadenceOptions, value) }
    function drawdownHelp(value) { return optionHelp(drawdownOptions, value) }

    function budgetHelp(value) {
        if (appController.onboardingPath !== "FIRST_PORTFOLIO")
            return appController.wizardText.help_budget_existing
        if (value === 0)
            return appController.wizardText.help_budget_auto
        return appController.wizardText.help_budget_amount
    }

    function botHelp(enabled) {
        return appController.profileToggleHelp[enabled ? "bots_on" : "bots_off"]
    }

    function spotTradeHelp(enabled) {
        return appController.profileToggleHelp[enabled ? "spot_on" : "spot_off"]
    }

    function markProfileEdited() {
        profileChoicesEdited = true
    }

    // One row per choice: what it is, what you picked, and what that changes.
    function profileSummaryRows() {
        let t = appController.wizardText
        return [
            { label: t.field_management_style, value: wizardStyle.currentText, effect: window.styleHelp(wizardStyle.currentValue) },
            { label: t.field_automation, value: wizardAutomation.currentText, effect: window.automationHelp(wizardAutomation.currentValue) },
            { label: t.field_drawdown_comfort, value: wizardDrawdown.currentText, effect: window.drawdownHelp(wizardDrawdown.currentValue) },
            { label: t.field_review_rhythm, value: wizardCadence.currentText, effect: window.cadenceHelp(wizardCadence.currentValue) },
            { label: t.checkbox_use_bots, value: wizardUseBots.checked ? t.value_on : t.value_off, effect: window.botHelp(wizardUseBots.checked) },
            { label: t.checkbox_allow_spot, value: wizardAllowSpot.checked ? t.value_on : t.value_off, effect: window.spotTradeHelp(wizardAllowSpot.checked) }
        ]
    }

    function indexOfValue(options, value) {
        for (let i = 0; i < options.length; i++) {
            if (options[i].value === value)
                return i
        }
        return -1
    }

    // Reopening the wizard used to show the hardcoded defaults regardless of
    // what was saved, which made it look like the profile had been reset.
    function restoreSavedProfileChoices() {
        let saved = appController.savedProfileChoices
        if (!saved || saved.style === undefined)
            return
        let apply = function (combo, options, value) {
            let index = window.indexOfValue(options, value)
            if (index >= 0)
                combo.currentIndex = index
        }
        apply(wizardStyle, window.styleOptions, saved.style)
        apply(wizardAutomation, window.automationOptions, saved.automation)
        apply(wizardCadence, window.cadenceOptions, saved.cadence)
        apply(wizardDrawdown, window.drawdownOptions, saved.drawdown)
        apply(wizardBudget, window.budgetOptions, saved.budget)
        let localeIndex = wizardLocale.model.indexOf(saved.locale)
        if (localeIndex >= 0)
            wizardLocale.currentIndex = localeIndex
        wizardUseBots.checked = saved.useBots
        wizardAllowSpot.checked = saved.allowSpotTrades
    }

    function openGuide(guideId) {
        for (let i = 0; i < appController.guides.length; i++) {
            let guide = appController.guides[i]
            if (guide.id === guideId) {
                activeGuide = guide
                guideDialog.open()
                return
            }
        }
    }

    function handleGuideLink(link) {
        if (link.indexOf("guide:") === 0) {
            window.openGuide(link.substring(6))
        } else {
            Qt.openUrlExternally(link)
        }
    }

    function canContinueWizard() {
        if (wizardStep === 0)
            return wizardExchange.currentValue === "BINANCE"
        if (wizardStep === 1)
            return appController.onboardingPath !== ""
        if (wizardStep === 2)
            return appController.userProfileConfigured
        return true
    }

    function canJumpToWizardStep(targetStep) {
        if (targetStep <= wizardStep)
            return true
        if (targetStep === 1)
            return wizardExchange.currentValue === "BINANCE"
        if (targetStep === 2)
            return wizardExchange.currentValue === "BINANCE" && appController.onboardingPath !== ""
        return wizardExchange.currentValue === "BINANCE" && appController.onboardingPath !== "" && appController.userProfileConfigured
    }

    function goNextWizardStep() {
        if (!canContinueWizard())
            return
        wizardStep = Math.min(wizardStep + 1, wizardSteps.length - 1)
    }

    function openWizardAtStep(stepIndex) {
        wizardStep = stepIndex
        appController.openOnboardingWizard()
    }

    Item {
        anchors.fill: parent
        visible: appController.onboardingWizardVisible
        // Load the saved profile once the controls exist, and again whenever the
        // wizard is reopened, so it never shows defaults over a saved profile.
        Component.onCompleted: window.restoreSavedProfileChoices()
        onVisibleChanged: if (visible) window.restoreSavedProfileChoices()

        Rectangle {
            anchors.fill: parent
            color: "#0f1318"
        }

        ScrollView {
            anchors.fill: parent
            clip: true

            ColumnLayout {
                x: Math.max(32, (window.width - 1120) / 2)
                y: 34
                width: Math.min(1120, window.width - 64)
                spacing: 16

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 14
                    AppLogo {
                        Layout.preferredWidth: 46
                        Layout.preferredHeight: 46
                        size: 46
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 3
                        Text { text: appController.wizardText.welcome_title; color: textPrimary; font.pixelSize: 28; font.bold: true }
                        Text {
                            Layout.fillWidth: true
                            text: appController.wizardText.welcome_subtitle
                            color: textSecondary
                            font.pixelSize: 14
                            wrapMode: Text.WordWrap
                        }
                    }
                    RowLayout {
                        spacing: 4
                        Button {
                            text: "English"
                            flat: appController.wizardLanguage !== "en"
                            highlighted: appController.wizardLanguage === "en"
                            onClicked: appController.setWizardLanguage("en")
                        }
                        Button {
                            text: "Čeština"
                            flat: appController.wizardLanguage !== "cs"
                            highlighted: appController.wizardLanguage === "cs"
                            onClicked: appController.setWizardLanguage("cs")
                        }
                    }
                    Button {
                        text: appController.wizardText.enter_app_button
                        enabled: appController.userProfileConfigured
                        onClicked: appController.finishOnboardingWizard()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 68
                    radius: radiusMd
                    color: panel
                    border.color: border
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 12
                        Text {
                            Layout.fillWidth: true
                            text: appController.wizardText.local_first_banner
                            color: textSecondary
                            font.pixelSize: 13
                            wrapMode: Text.WordWrap
                        }
                        StatusPill {
                            Layout.alignment: Qt.AlignVCenter
                            label: appController.wizardText.local_first_badge
                            tone: "success"
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    // Driven by the step's real content. A hardcoded per-step
                    // height table used to under-report once translated text
                    // wrapped onto more lines, pushing the last card under the
                    // "ask about this step" panel. implicitHeight depends on
                    // width, not on the height assigned here, so this is safe.
                    Layout.preferredHeight: Math.max(wizardStepPanel.implicitHeight + 36, window.height - 190)
                    Layout.minimumHeight: 420
                    spacing: 16

                    Rectangle {
                        Layout.preferredWidth: 210
                        Layout.fillHeight: true
                        radius: radiusMd
                        color: panel
                        border.color: border
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 14
                            spacing: 8
                            Text {
                                Layout.fillWidth: true
                                text: appController.wizardText.setup_steps_title
                                color: textPrimary
                                font.pixelSize: 15
                                font.bold: true
                            }
                            Repeater {
                                model: window.wizardStepLabels()
                                delegate: Rectangle {
                                    required property string modelData
                                    required property int index
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 42
                                    radius: radiusSm
                                    color: window.wizardStep === index ? panelRaised : "transparent"
                                    border.color: window.wizardStep === index ? border : "transparent"
                                    opacity: window.canJumpToWizardStep(index) ? 1.0 : 0.45
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 10
                                        anchors.rightMargin: 10
                                        spacing: 8
                                        Rectangle {
                                            Layout.preferredWidth: 20
                                            Layout.preferredHeight: 20
                                            radius: radiusPill
                                            color: window.wizardStep === index ? accent : "#27323d"
                                            Text {
                                                anchors.centerIn: parent
                                                text: String(index + 1)
                                                color: window.wizardStep === index ? "#09110e" : textSecondary
                                                font.pixelSize: 10
                                                font.bold: true
                                            }
                                        }
                                        Text {
                                            Layout.fillWidth: true
                                            text: modelData
                                            color: window.wizardStep === index ? textPrimary : textSecondary
                                            font.pixelSize: 12
                                            font.bold: window.wizardStep === index
                                            elide: Text.ElideRight
                                        }
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        enabled: window.canJumpToWizardStep(index)
                                        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                                        onClicked: window.wizardStep = index
                                    }
                                }
                            }
                            Item { Layout.fillHeight: true }
                            Text {
                                Layout.fillWidth: true
                                text: appController.wizardText.setup_steps_hint
                                color: textSecondary
                                font.pixelSize: 10
                                wrapMode: Text.WordWrap
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: radiusMd
                        color: panel
                        border.color: border
                        ColumnLayout {
                            id: wizardStepPanel
                            anchors.fill: parent
                            anchors.margins: 18
                            spacing: 14

                            StackLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                currentIndex: window.wizardStep

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 14
                                    Text { text: appController.wizardText.step1_title; color: textPrimary; font.pixelSize: 22; font.bold: true }
                                    Text {
                                        Layout.fillWidth: true
                                        text: appController.wizardText.step1_description
                                        color: textSecondary
                                        font.pixelSize: 13
                                        wrapMode: Text.WordWrap
                                    }
                                    ComboBox {
                                        id: wizardExchange
                                        Layout.preferredWidth: 320
                                        model: window.exchangeOptions
                                        textRole: "label"
                                        valueRole: "value"
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 170
                                        radius: radiusMd
                                        color: panelRaised
                                        border.color: border
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 16
                                            spacing: 8
                                            Text {
                                                text: wizardExchange.currentValue === "BINANCE" ? appController.wizardText.step1_binance_supported : appController.wizardText.step1_coinbase_planned
                                                color: wizardExchange.currentValue === "BINANCE" ? accent : warning
                                                font.pixelSize: 15
                                                font.bold: true
                                            }
                                            Text {
                                                Layout.fillWidth: true
                                                text: wizardExchange.currentValue === "BINANCE"
                                                    ? appController.wizardText.step1_binance_detail
                                                    : appController.wizardText.step1_coinbase_detail
                                                color: textSecondary
                                                font.pixelSize: 12
                                                wrapMode: Text.WordWrap
                                            }
                                            Text {
                                                Layout.fillWidth: true
                                                text: appController.wizardText.step1_manual_setup_note
                                                color: textSecondary
                                                font.pixelSize: 12
                                                wrapMode: Text.WordWrap
                                            }
                                        }
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 118
                                        radius: radiusMd
                                        color: panelRaised
                                        border.color: border
                                        visible: appController.onboardingPath !== ""
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 14
                                            spacing: 6
                                            Text {
                                                text: appController.onboardingPath === "FIRST_PORTFOLIO" ? appController.wizardText.step1_first_portfolio_selected : appController.wizardText.step1_existing_selected
                                                color: accent
                                                font.pixelSize: 14
                                                font.bold: true
                                            }
                                            Text {
                                                Layout.fillWidth: true
                                                text: appController.onboardingPath === "FIRST_PORTFOLIO"
                                                    ? appController.wizardText.step1_first_portfolio_focus
                                                    : appController.wizardText.step1_existing_focus
                                                color: textSecondary
                                                font.pixelSize: 12
                                                wrapMode: Text.WordWrap
                                            }
                                        }
                                    }
                                    Item { Layout.fillHeight: true }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 14
                                    Text { text: appController.wizardText.step2_title; color: textPrimary; font.pixelSize: 22; font.bold: true }
                                    Text {
                                        Layout.fillWidth: true
                                        text: appController.wizardText.step2_description
                                        color: textSecondary
                                        font.pixelSize: 13
                                        wrapMode: Text.WordWrap
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 12
                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 170
                                            radius: radiusMd
                                            color: appController.onboardingPath === "EXISTING" ? "#1d332d" : panelRaised
                                            border.color: appController.onboardingPath === "EXISTING" ? accent : border
                                            ColumnLayout {
                                                anchors.fill: parent
                                                anchors.margins: 16
                                                spacing: 8
                                                Text { text: appController.wizardText.step2_existing_card_title; color: textPrimary; font.pixelSize: 16; font.bold: true }
                                                Text {
                                                    Layout.fillWidth: true
                                                    text: appController.wizardText.step2_existing_card_detail
                                                    color: textSecondary
                                                    font.pixelSize: 12
                                                    wrapMode: Text.WordWrap
                                                }
                                                Item { Layout.fillHeight: true }
                                                Text { text: appController.wizardText.step2_existing_card_next; color: accent; font.pixelSize: 12; font.bold: true }
                                            }
                                            MouseArea {
                                                anchors.fill: parent
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: appController.selectOnboardingPath("EXISTING")
                                            }
                                        }
                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 170
                                            radius: radiusMd
                                            color: appController.onboardingPath === "FIRST_PORTFOLIO" ? "#1d332d" : panelRaised
                                            border.color: appController.onboardingPath === "FIRST_PORTFOLIO" ? accent : border
                                            ColumnLayout {
                                                anchors.fill: parent
                                                anchors.margins: 16
                                                spacing: 8
                                                Text { text: appController.wizardText.step2_first_card_title; color: textPrimary; font.pixelSize: 16; font.bold: true }
                                                Text {
                                                    Layout.fillWidth: true
                                                    text: appController.wizardText.step2_first_card_detail
                                                    color: textSecondary
                                                    font.pixelSize: 12
                                                    wrapMode: Text.WordWrap
                                                }
                                                Item { Layout.fillHeight: true }
                                                Text { text: appController.wizardText.step2_first_card_next; color: accent; font.pixelSize: 12; font.bold: true }
                                            }
                                            MouseArea {
                                                anchors.fill: parent
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: appController.selectOnboardingPath("FIRST_PORTFOLIO")
                                            }
                                        }
                                    }
                                    Item { Layout.fillHeight: true }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 12
                                    Text { text: appController.wizardText.step3_title; color: textPrimary; font.pixelSize: 22; font.bold: true }
                                    Text {
                                        Layout.fillWidth: true
                                        text: appController.wizardText.step3_description
                                        color: textSecondary
                                        font.pixelSize: 13
                                        wrapMode: Text.WordWrap
                                    }

                                    GridLayout {
                                        Layout.fillWidth: true
                                        columns: 3
                                        columnSpacing: 12
                                        rowSpacing: 12

                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Text { text: appController.wizardText.field_management_style; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                            ComboBox { id: wizardStyle; Layout.fillWidth: true; model: window.styleOptions; textRole: "label"; valueRole: "value"; currentIndex: 1; onActivated: window.markProfileEdited() }
                                            Text {
                                                Layout.fillWidth: true
                                                text: window.styleHelp(wizardStyle.currentValue)
                                                color: textSecondary
                                                font.pixelSize: 10
                                                wrapMode: Text.WordWrap
                                            }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Text { text: appController.wizardText.field_automation; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                            ComboBox { id: wizardAutomation; Layout.fillWidth: true; model: window.automationOptions; textRole: "label"; valueRole: "value"; onActivated: window.markProfileEdited() }
                                            Text {
                                                Layout.fillWidth: true
                                                text: window.automationHelp(wizardAutomation.currentValue)
                                                color: textSecondary
                                                font.pixelSize: 10
                                                wrapMode: Text.WordWrap
                                            }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Text { text: appController.wizardText.field_review_rhythm; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                            ComboBox { id: wizardCadence; Layout.fillWidth: true; model: window.cadenceOptions; textRole: "label"; valueRole: "value"; currentIndex: 1; onActivated: window.markProfileEdited() }
                                            Text {
                                                Layout.fillWidth: true
                                                text: window.cadenceHelp(wizardCadence.currentValue)
                                                color: textSecondary
                                                font.pixelSize: 10
                                                wrapMode: Text.WordWrap
                                            }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Text { text: appController.wizardText.field_language_region; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                            ComboBox { id: wizardLocale; Layout.fillWidth: true; model: ["en-US", "es-ES", "cs-CZ", "pt-BR"]; onActivated: window.markProfileEdited() }
                                            Text {
                                                Layout.fillWidth: true
                                                text: appController.wizardText.help_locale
                                                color: textSecondary
                                                font.pixelSize: 10
                                                wrapMode: Text.WordWrap
                                            }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Text { text: appController.wizardText.field_operating_currency; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                            Rectangle {
                                                Layout.fillWidth: true
                                                Layout.preferredHeight: 56
                                                radius: radiusSm
                                                color: panelRaised
                                                border.color: border
                                                Text {
                                                    anchors.verticalCenter: parent.verticalCenter
                                                    anchors.left: parent.left
                                                    anchors.leftMargin: 14
                                                    text: window.fundingCurrency
                                                    color: textPrimary
                                                    font.pixelSize: 14
                                                    font.bold: true
                                                }
                                            }
                                            Text { Layout.fillWidth: true; text: appController.wizardText.operating_currency_note; color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Text { text: appController.onboardingPath === "FIRST_PORTFOLIO" ? appController.wizardText.field_starting_budget : appController.wizardText.field_reference_budget; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                            ComboBox { id: wizardBudget; Layout.fillWidth: true; model: window.budgetOptions; textRole: "label"; valueRole: "value"; onActivated: window.markProfileEdited() }
                                            Text { Layout.fillWidth: true; text: window.budgetHelp(wizardBudget.currentValue); color: textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                        }
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 12
                                        ColumnLayout {
                                            Layout.preferredWidth: 300
                                            Text { text: appController.wizardText.field_drawdown_comfort; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                            ComboBox { id: wizardDrawdown; Layout.fillWidth: true; model: window.drawdownOptions; textRole: "label"; valueRole: "value"; currentIndex: 2; onActivated: window.markProfileEdited() }
                                            Text {
                                                Layout.fillWidth: true
                                                text: window.drawdownHelp(wizardDrawdown.currentValue)
                                                color: textSecondary
                                                font.pixelSize: 10
                                                wrapMode: Text.WordWrap
                                            }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            CheckBox { id: wizardUseBots; text: appController.wizardText.checkbox_use_bots; checked: true; onClicked: window.markProfileEdited() }
                                            Text { Layout.fillWidth: true; text: window.botHelp(wizardUseBots.checked); color: textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            CheckBox {
                                                id: wizardAllowSpot
                                                text: appController.wizardText.checkbox_allow_spot
                                                checked: false
                                                enabled: wizardAutomation.currentValue === "GUARDED_AUTOMATION"
                                                onClicked: window.markProfileEdited()
                                            }
                                            Text { Layout.fillWidth: true; text: window.spotTradeHelp(wizardAllowSpot.checked); color: wizardAllowSpot.enabled ? textSecondary : "#66717c"; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                        }
                                    }

                                    Rectangle {
                                        // Height follows the content: the summary lists every choice and
                                        // Czech runs longer than English, so a fixed height would clip it.
                                        Layout.fillWidth: true
                                        radius: radiusSm
                                        color: panelRaised
                                        Layout.preferredHeight: currentSelectionContent.implicitHeight + 24
                                        ColumnLayout {
                                            id: currentSelectionContent
                                            anchors.left: parent.left
                                            anchors.right: parent.right
                                            anchors.top: parent.top
                                            anchors.margins: 12
                                            spacing: 6
                                            Text { text: appController.wizardText.current_selection_title; color: textPrimary; font.pixelSize: 13; font.bold: true }
                                            Text {
                                                Layout.fillWidth: true
                                                visible: !window.profileChoicesEdited && !appController.userProfileConfigured
                                                text: appController.wizardText.current_selection_placeholder
                                                color: textSecondary
                                                font.pixelSize: 12
                                                wrapMode: Text.WordWrap
                                            }
                                            Repeater {
                                                model: window.profileChoicesEdited || appController.userProfileConfigured
                                                    ? window.profileSummaryRows()
                                                    : []
                                                delegate: RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 8
                                                    Text {
                                                        Layout.preferredWidth: 150
                                                        Layout.alignment: Qt.AlignTop
                                                        text: modelData.label
                                                        color: textPrimary
                                                        font.pixelSize: 11
                                                        font.bold: true
                                                        wrapMode: Text.WordWrap
                                                    }
                                                    Text {
                                                        Layout.preferredWidth: 130
                                                        Layout.alignment: Qt.AlignTop
                                                        text: modelData.value
                                                        color: accent
                                                        font.pixelSize: 11
                                                        wrapMode: Text.WordWrap
                                                    }
                                                    Text {
                                                        Layout.fillWidth: true
                                                        text: modelData.effect
                                                        color: textSecondary
                                                        font.pixelSize: 11
                                                        wrapMode: Text.WordWrap
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Item { Layout.fillWidth: true }
                                        Button {
                                            text: appController.wizardText.apply_safe_defaults_button
                                            ToolTip.visible: hovered
                                            ToolTip.text: appController.wizardText.apply_safe_defaults_tooltip
                                            onClicked: {
                                                appController.useSafeDefaultProfile()
                                                window.profileChoicesEdited = true
                                                window.showToast("Safe default profile saved")
                                            }
                                        }
                                        Button {
                                            text: appController.wizardText.save_profile_button
                                            ToolTip.visible: hovered
                                            ToolTip.text: appController.wizardText.save_profile_tooltip
                                            highlighted: true
                                            onClicked: {
                                                appController.saveGuidedProfile(
                                                    wizardStyle.currentValue,
                                                    wizardAutomation.currentValue,
                                                    wizardCadence.currentValue,
                                                    wizardLocale.currentText,
                                                    window.fundingCurrency,
                                                    wizardUseBots.checked,
                                                    wizardAllowSpot.checked,
                                                    wizardDrawdown.currentValue,
                                                    wizardBudget.currentValue
                                                )
                                                window.profileChoicesEdited = true
                                                window.showToast("Profile saved locally")
                                            }
                                        }
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text: appController.userProfileConfigured ? appController.wizardText.profile_saved_status : appController.wizardText.profile_not_saved_status
                                        color: appController.userProfileConfigured ? accent : warning
                                        font.pixelSize: 12
                                        font.bold: true
                                    }
                                    Item { Layout.fillHeight: true }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    Text { text: appController.wizardText.step4_title; color: textPrimary; font.pixelSize: 22; font.bold: true }
                                    Text {
                                        Layout.fillWidth: true
                                        text: appController.wizardText.step4_description
                                        color: textSecondary
                                        font.pixelSize: 13
                                        wrapMode: Text.WordWrap
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Button {
                                            text: appController.wizardText.open_local_ai_guide_button
                                            onClicked: window.openGuide("local-ai")
                                        }
                                        Button {
                                            text: appController.wizardText.open_cloud_ai_guide_button
                                            onClicked: window.openGuide("cloud-ai")
                                        }
                                        Item { Layout.fillWidth: true }
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        // Content-driven, like the notice card below it. A
                                        // fixed 104 could not hold four wrapping lines whose
                                        // length depends on the endpoint and both model names,
                                        // so the text spilled past the border.
                                        Layout.preferredHeight: currentAiProviderRow.implicitHeight + 32
                                        radius: radiusMd
                                        color: panelRaised
                                        border.color: border
                                        RowLayout {
                                            id: currentAiProviderRow
                                            anchors.left: parent.left
                                            anchors.right: parent.right
                                            anchors.verticalCenter: parent.verticalCenter
                                            anchors.leftMargin: 16
                                            anchors.rightMargin: 16
                                            spacing: 12
                                            ColumnLayout {
                                                Layout.fillWidth: true
                                                spacing: 5
                                                Text { text: appController.wizardText.current_ai_provider_title; color: textPrimary; font.pixelSize: 15; font.bold: true }
                                                Text { Layout.fillWidth: true; text: appController.aiProviderSummary; color: textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap }
                                                Text { Layout.fillWidth: true; text: appController.aiProviderHealthDetail; color: textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                                Text { Layout.fillWidth: true; text: appController.wizardText.ai_skip_hint; color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap }
                                            }
                                            Button {
                                                text: appController.checkingAiProvider ? appController.wizardText.checking_status : appController.wizardText.check_ai_provider_button
                                                enabled: !appController.checkingAiProvider
                                                onClicked: appController.checkAiProvider()
                                            }
                                        }
                                    }
                                    Rectangle {
                                        // The two panels below are alternatives, not
                                        // independent settings: they write the same
                                        // LLM_* variables, so one replaces the other.
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: aiProviderNoticeColumn.implicitHeight + 20
                                        radius: radiusSm
                                        color: panelRaised
                                        border.color: appController.activeAiProviderKind === "CLOUD" ? warning : border
                                        ColumnLayout {
                                            id: aiProviderNoticeColumn
                                            anchors.left: parent.left
                                            anchors.right: parent.right
                                            anchors.verticalCenter: parent.verticalCenter
                                            anchors.leftMargin: 12
                                            anchors.rightMargin: 12
                                            spacing: 3
                                            Text {
                                                Layout.fillWidth: true
                                                text: appController.activeAiProviderKind === "LOCAL" ? appController.wizardText.ai_active_local
                                                    : appController.activeAiProviderKind === "CLOUD" ? appController.wizardText.ai_active_cloud
                                                    : appController.wizardText.ai_active_none
                                                color: appController.activeAiProviderKind === "CLOUD" ? warning : accent
                                                font.pixelSize: 11
                                                font.bold: true
                                                wrapMode: Text.WordWrap
                                            }
                                            Text {
                                                Layout.fillWidth: true
                                                text: appController.wizardText.ai_one_provider_notice
                                                color: textSecondary
                                                font.pixelSize: 10
                                                wrapMode: Text.WordWrap
                                            }
                                        }
                                    }
                                    GridLayout {
                                        id: aiProviderGrid
                                        Layout.fillWidth: true
                                        columns: width < 760 ? 1 : 2
                                        columnSpacing: 12
                                        rowSpacing: 12
                                        Rectangle {
                                            Layout.fillWidth: true
                                            // Content-driven. This used to be hand-computed
                                            // arithmetic over model/recommendation counts,
                                            // which under-reported and let the detected-models
                                            // panel collide with the card's bottom edge.
                                            Layout.preferredHeight: localAiCardContent.implicitHeight + 32
                                            radius: radiusMd
                                            color: panelRaised
                                            // Accent marks the provider actually in use.
                                            border.color: appController.activeAiProviderKind === "LOCAL" ? accent : border
                                            ColumnLayout {
                                                id: localAiCardContent
                                                anchors.left: parent.left
                                                anchors.right: parent.right
                                                anchors.top: parent.top
                                                anchors.margins: 16
                                                spacing: 10
                                                Text { text: "Local AI with Ollama"; color: textPrimary; font.pixelSize: 15; font.bold: true }
                                                Text {
                                                    Layout.fillWidth: true
                                                    text: "Best for privacy. For portfolio analysis, 14B-class models are the preferred minimum when hardware allows it; smaller models are mainly for basic app help and may be less reliable."
                                                    color: textSecondary
                                                    font.pixelSize: 11
                                                    wrapMode: Text.WordWrap
                                                }
                                                Text { Layout.fillWidth: true; text: "1. Install Ollama.  2. Pull a text model.  3. Optionally pull a vision model for screenshots.  4. Keep Ollama running and save both model tags."; color: textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 8
                                                    TextField {
                                                        id: localAiBaseUrl
                                                        Layout.fillWidth: true
                                                        placeholderText: "Local endpoint"
                                                        text: appController.activeAiProviderKind === "LOCAL" && appController.aiProviderBaseUrl.length > 0
                                                            ? appController.aiProviderBaseUrl : "http://127.0.0.1:11434/v1"
                                                    }
                                                }
                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 8
                                                    TextField {
                                                        id: localAiModel
                                                        Layout.fillWidth: true
                                                        // Without a minimum the fields keep their
                                                        // placeholder-sized implicit width and the
                                                        // card clips them.
                                                        Layout.minimumWidth: 120
                                                        placeholderText: "Text model, e.g. qwen3:14b"
                                                        text: appController.activeAiProviderKind === "LOCAL" && appController.aiTextModel.length > 0
                                                            ? appController.aiTextModel : "qwen3:14b"
                                                    }
                                                    TextField {
                                                        id: localAiVisionModel
                                                        Layout.fillWidth: true
                                                        Layout.minimumWidth: 120
                                                        placeholderText: "Vision model (optional)"
                                                        text: appController.activeAiProviderKind === "LOCAL" ? appController.aiVisionModel : ""
                                                    }
                                                }
                                                // Flow, not RowLayout: three buttons do not fit
                                                // side by side when the grid is in two columns,
                                                // and the card clips whatever overflows.
                                                Flow {
                                                    Layout.fillWidth: true
                                                    spacing: 8
                                                    Button {
                                                        text: "Save local AI"
                                                        ToolTip.visible: hovered
                                                        ToolTip.text: appController.wizardText.ai_switch_to_local_clears_key
                                                        onClicked: {
                                                            appController.saveLocalAiProvider(localAiBaseUrl.text, localAiModel.text, localAiVisionModel.text)
                                                            window.showToast("Local AI settings saved")
                                                        }
                                                    }
                                                    Button {
                                                        // The scan shells out to OS tools and can take
                                                        // seconds; say so instead of looking frozen.
                                                        text: appController.scanningLocalAiHardware
                                                            ? appController.wizardText.checking_status
                                                            : "Scan hardware"
                                                        enabled: !appController.scanningLocalAiHardware
                                                        onClicked: appController.scanLocalAiHardware()
                                                    }
                                                    Button {
                                                        text: appController.discoveringAiModels ? "Detecting..." : "Detect installed models"
                                                        enabled: !appController.discoveringAiModels
                                                        onClicked: appController.discoverLocalAiModels(localAiBaseUrl.text)
                                                    }
                                                    // No anchors here: this is a Flow, and anchoring a
                                                    // child breaks the whole layout.
                                                    BusyDots {
                                                        visible: appController.discoveringAiModels
                                                    }
                                                }
                                                Text {
                                                    Layout.fillWidth: true
                                                    text: "Local scan only: reads RAM and GPU/VRAM from OS tools. 14B-class models are preferred for portfolio commentary when hardware supports them; smaller models are mainly for basic help."
                                                    color: textSecondary
                                                    font.pixelSize: 10
                                                    wrapMode: Text.WordWrap
                                                }
                                                Text { Layout.fillWidth: true; text: appController.localAiHardwareSummary; color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap }
                                                Rectangle {
                                                    visible: appController.localAiDiscoveredModels.length > 0 || appController.discoveringAiModels || appController.localAiDiscoveryState === "BLOCK"
                                                    Layout.fillWidth: true
                                                    Layout.bottomMargin: 10
                                                    // Row height follows the buttons, so a per-row
                                                    // pixel estimate clipped the last entry.
                                                    Layout.minimumHeight: 90
                                                    Layout.preferredHeight: appController.localAiDiscoveredModels.length > 0
                                                        ? 60 + Math.min(appController.localAiDiscoveredModels.length, 4) * 54
                                                        : 90
                                                    radius: radiusSm
                                                    color: "#10161d"
                                                    border.color: border
                                                    clip: true
                                                    ColumnLayout {
                                                        anchors.fill: parent
                                                        anchors.margins: 10
                                                        spacing: 6
                                                        RowLayout {
                                                            Layout.fillWidth: true
                                                            Text { text: "Installed models detected"; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                                            Item { Layout.fillWidth: true }
                                                            Text { text: appController.localAiDiscoveredModels.length > 4 ? "Scroll for all" : ""; color: textSecondary; font.pixelSize: 10 }
                                                        }
                                                        Text {
                                                            visible: appController.localAiDiscoveredModels.length === 0
                                                            Layout.fillWidth: true
                                                            text: appController.localAiDiscoveryDetail
                                                            color: appController.localAiDiscoveryState === "BLOCK" ? warning : textSecondary
                                                            font.pixelSize: 10
                                                            wrapMode: Text.WordWrap
                                                        }
                                                        ListView {
                                                            visible: appController.localAiDiscoveredModels.length > 0
                                                            Layout.fillWidth: true
                                                            Layout.fillHeight: true
                                                            clip: true
                                                            interactive: true
                                                            boundsBehavior: Flickable.StopAtBounds
                                                            spacing: 6
                                                            model: appController.localAiDiscoveredModels
                                                            ScrollBar.vertical: ScrollBar { policy: appController.localAiDiscoveredModels.length > 4 ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded }
                                                            delegate: Rectangle {
                                                                required property string modelData
                                                                width: ListView.view.width - 12
                                                                height: modelRow.implicitHeight + 8
                                                                radius: radiusSm
                                                                color: "#141a21"
                                                                border.color: border
                                                                RowLayout {
                                                                    id: modelRow
                                                                    anchors.fill: parent
                                                                    anchors.leftMargin: 10
                                                                    anchors.rightMargin: 6
                                                                    spacing: 6
                                                                    Text { Layout.fillWidth: true; Layout.minimumWidth: 0; text: modelData; color: accent; font.pixelSize: 11; elide: Text.ElideRight }
                                                                    // No implicitHeight override: forcing one collapses
                                                                    // the label in the Material style and the buttons
                                                                    // render as empty pills. minimumWidth stops the
                                                                    // layout squeezing them in the narrow grid column.
                                                                    Button {
                                                                        text: "Use as text"
                                                                        font.pixelSize: 9
                                                                        leftPadding: 10
                                                                        rightPadding: 10
                                                                        Layout.minimumWidth: implicitWidth
                                                                        onClicked: localAiModel.text = modelData
                                                                    }
                                                                    Button {
                                                                        text: "Use as vision"
                                                                        font.pixelSize: 9
                                                                        leftPadding: 10
                                                                        rightPadding: 10
                                                                        Layout.minimumWidth: implicitWidth
                                                                        onClicked: localAiVisionModel.text = modelData
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                                Rectangle {
                                                    visible: appController.localAiModelRecommendations.length > 0
                                                    Layout.fillWidth: true
                                                    Layout.bottomMargin: 16
                                                    Layout.minimumHeight: 230
                                                    Layout.preferredHeight: 70 + Math.min(appController.localAiModelRecommendations.length, 4) * 58
                                                    radius: radiusSm
                                                    color: "#10161d"
                                                    border.color: border
                                                    clip: true
                                                    ColumnLayout {
                                                        anchors.fill: parent
                                                        anchors.margins: 10
                                                        spacing: 8
                                                        RowLayout {
                                                            Layout.fillWidth: true
                                                            Text { text: "Recommended local models"; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                                            Item { Layout.fillWidth: true }
                                                            Text { text: appController.localAiModelRecommendations.length > 4 ? "Scroll for all" : "All recommendations"; color: textSecondary; font.pixelSize: 10 }
                                                        }
                                                        ListView {
                                                            Layout.fillWidth: true
                                                            Layout.fillHeight: true
                                                            clip: true
                                                            interactive: true
                                                            boundsBehavior: Flickable.StopAtBounds
                                                            spacing: 6
                                                            model: appController.localAiModelRecommendations
                                                            ScrollBar.vertical: ScrollBar { policy: appController.localAiModelRecommendations.length > 4 ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded }
                                                            delegate: Rectangle {
                                                                required property var modelData
                                                                width: ListView.view.width - 12
                                                                height: 52
                                                                radius: radiusSm
                                                                color: "#141a21"
                                                                border.color: border
                                                                RowLayout {
                                                                    anchors.fill: parent
                                                                    anchors.leftMargin: 10
                                                                    anchors.rightMargin: 10
                                                                    spacing: 8
                                                                    Text { Layout.preferredWidth: 88; text: modelData.model; color: accent; font.pixelSize: 11; font.bold: true; elide: Text.ElideRight }
                                                                    Text { Layout.preferredWidth: 44; text: modelData.purpose; color: modelData.purpose === "Vision" ? warning : textSecondary; font.pixelSize: 9; font.bold: true }
                                                                    Text { Layout.preferredWidth: 72; text: modelData.fit; color: textPrimary; font.pixelSize: 10; font.bold: true; elide: Text.ElideRight }
                                                                    Text { Layout.fillWidth: true; text: modelData.reason; color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap; maximumLineCount: 2; elide: Text.ElideRight }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: appController.localAiModelRecommendations.length > 0 ? (aiProviderGrid.columns === 1 ? 430 : 690) : 460
                                            Layout.minimumHeight: 410
                                            radius: radiusMd
                                            color: panelRaised
                                            border.color: appController.activeAiProviderKind === "CLOUD" ? accent : border
                                            clip: true
                                            ColumnLayout {
                                                anchors.fill: parent
                                                anchors.margins: 16
                                                spacing: 10
                                                Text { text: "Cloud AI provider"; color: textPrimary; font.pixelSize: 15; font.bold: true }
                                                Text {
                                                    Layout.fillWidth: true
                                                    text: "Best quality, but selected report/profile context can leave your computer. Use your own provider API key; subscriptions are optional and provider-specific."
                                                    color: textSecondary
                                                    font.pixelSize: 11
                                                    wrapMode: Text.WordWrap
                                                }
                                                Text {
                                                    Layout.fillWidth: true
                                                    text: 'OpenAI example: create an API key in <a href="https://platform.openai.com/">OpenAI Platform &gt; API keys</a>, then use https://api.openai.com/v1 and your chosen model. A ChatGPT subscription is separate from API usage.'
                                                    textFormat: Text.RichText
                                                    linkColor: accent
                                                    color: textSecondary
                                                    font.pixelSize: 11
                                                    wrapMode: Text.WordWrap
                                                    onLinkActivated: (link) => Qt.openUrlExternally(link)
                                                    MouseArea {
                                                        anchors.fill: parent
                                                        acceptedButtons: Qt.NoButton
                                                        cursorShape: parent.hoveredLink ? Qt.PointingHandCursor : Qt.ArrowCursor
                                                    }
                                                }
                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 8
                                                    TextField { id: cloudAiBaseUrl; Layout.fillWidth: true; placeholderText: "https://api.openai.com/v1"
                                                        text: appController.activeAiProviderKind === "CLOUD" ? appController.aiProviderBaseUrl : "" }
                                                }
                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 8
                                                    TextField { id: cloudAiModel; Layout.fillWidth: true; placeholderText: "Text model"
                                                        text: appController.activeAiProviderKind === "CLOUD" ? appController.aiTextModel : "" }
                                                    TextField { id: cloudAiVisionModel; Layout.fillWidth: true; placeholderText: "Vision model (optional)"
                                                        text: appController.activeAiProviderKind === "CLOUD" ? appController.aiVisionModel : "" }
                                                }
                                                TextField { id: cloudAiKey; Layout.fillWidth: true; placeholderText: "API key"; echoMode: TextInput.Password }
                                                Button {
                                                    text: "Save cloud AI"
                                                    enabled: cloudAiBaseUrl.text.trim().length > 0 && cloudAiModel.text.trim().length > 0 && cloudAiKey.text.trim().length > 0
                                                    onClicked: {
                                                        appController.saveCloudAiProvider(cloudAiBaseUrl.text, cloudAiModel.text, cloudAiVisionModel.text, cloudAiKey.text)
                                                        cloudAiKey.text = ""
                                                        window.showToast("Cloud AI settings saved")
                                                    }
                                                }
                                                Item { Layout.fillHeight: true }
                                            }
                                        }
                                    }
                                    Item { Layout.fillHeight: true }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    Text { text: appController.wizardText.step5_title; color: textPrimary; font.pixelSize: 22; font.bold: true }
                                    Text {
                                        Layout.fillWidth: true
                                        text: appController.wizardText.step5_description
                                        color: textSecondary
                                        font.pixelSize: 13
                                        wrapMode: Text.WordWrap
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Button {
                                            text: appController.wizardText.open_binance_guide_button
                                            onClicked: window.openGuide("binance-api")
                                        }
                                        Item { Layout.fillWidth: true }
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 205
                                        radius: radiusMd
                                        color: panelRaised
                                        border.color: border
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 16
                                            spacing: 6
                                            Text { text: "Manual Binance steps"; color: textPrimary; font.pixelSize: 15; font.bold: true }
                                            Text { Layout.fillWidth: true; text: "1. Binance: User profile > Account > API Management > Create API > System generated."; color: textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap }
                                            Text { Layout.fillWidth: true; text: "2. Label suggestion: coinductor-readonly. Finish two-factor verification and copy both API Key and Secret Key immediately."; color: textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap }
                                            Text { Layout.fillWidth: true; text: "3. Edit restrictions: keep Enable Reading on. For read-only setup, do not enable withdrawals, futures, margin transfer, or universal transfer."; color: textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap }
                                            Text { Layout.fillWidth: true; text: "4. If Binance forces IP restriction for future trading keys, choose Restrict access to trusted IPs only and use your current public/static IP. Dynamic IP users should stay read-only or use a trusted always-on host later."; color: textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap }
                                            Text { Layout.fillWidth: true; text: "5. Trading/write access belongs to a separate later key, after testnet/preview confidence. Never enable withdrawals."; color: warning; font.pixelSize: 12; wrapMode: Text.WordWrap }
                                        }
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 136
                                        radius: radiusMd
                                        color: panelRaised
                                        border.color: border
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 16
                                            spacing: 8
                                            Text { text: appController.wizardText.connect_readonly_title; color: textPrimary; font.pixelSize: 15; font.bold: true }
                                            RowLayout {
                                                Layout.fillWidth: true
                                                TextField { id: binanceReadKey; Layout.fillWidth: true; placeholderText: "API Key" }
                                                TextField { id: binanceReadSecret; Layout.fillWidth: true; placeholderText: "Secret Key"; echoMode: TextInput.Password }
                                                Button {
                                                    text: appController.wizardText.save_key_button
                                                    enabled: binanceReadKey.text.trim().length > 0 && binanceReadSecret.text.trim().length > 0
                                                    onClicked: {
                                                        appController.saveBinanceReadOnlyCredentials(binanceReadKey.text, binanceReadSecret.text)
                                                        // Clear both: the value is stored, and leaving a
                                                        // credential on screen is needless exposure.
                                                        binanceReadKey.text = ""
                                                        binanceReadSecret.text = ""
                                                        window.showToast("Read-only Binance key saved")
                                                    }
                                                }
                                            }
                                            Text { Layout.fillWidth: true; Layout.topMargin: 2; text: appController.wizardText.key_storage_note; color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap }
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Button {
                                            text: appController.checkingConnection ? appController.wizardText.checking_status : appController.wizardText.check_readonly_button
                                            enabled: !appController.checkingConnection
                                            onClicked: appController.checkBinanceReadOnly()
                                        }
                                        StatusPill {
                                            Layout.alignment: Qt.AlignVCenter
                                            label: appController.binanceConnectionStatus
                                            tone: appController.binanceConnectionState === "Connected" ? "success"
                                                : appController.binanceConnectionState === "Blocked" ? "danger" : "neutral"
                                        }
                                    }
                                    Text { Layout.fillWidth: true; text: appController.binanceConnectionDetail; color: textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        // Content-driven: a fixed height pushed the
                                        // wrapped description and status detail
                                        // outside the card in longer translations.
                                        Layout.preferredHeight: testnetPanelContent.implicitHeight + 32
                                        radius: radiusMd
                                        color: panelRaised
                                        border.color: border
                                        ColumnLayout {
                                            id: testnetPanelContent
                                            anchors.left: parent.left
                                            anchors.right: parent.right
                                            anchors.top: parent.top
                                            anchors.margins: 16
                                            spacing: 8
                                            RowLayout {
                                                Layout.fillWidth: true
                                                Text { text: appController.wizardText.testnet_practice_title; color: textPrimary; font.pixelSize: 15; font.bold: true }
                                                Item { Layout.fillWidth: true }
                                                Button { text: appController.wizardText.open_testnet_guide_button; onClicked: window.openGuide("binance-testnet") }
                                            }
                                            Text {
                                                Layout.fillWidth: true
                                                text: appController.wizardText.testnet_description
                                                color: textSecondary
                                                font.pixelSize: 12
                                                wrapMode: Text.WordWrap
                                            }
                                            RowLayout {
                                                Layout.fillWidth: true
                                                spacing: 8
                                                TextField { id: binanceTestnetKey; Layout.fillWidth: true; placeholderText: "Testnet API Key" }
                                                TextField { id: binanceTestnetSecret; Layout.fillWidth: true; placeholderText: "Testnet Secret Key"; echoMode: TextInput.Password }
                                                Button {
                                                    text: appController.wizardText.save_testnet_key_button
                                                    enabled: binanceTestnetKey.text.trim().length > 0 && binanceTestnetSecret.text.trim().length > 0
                                                    onClicked: {
                                                        appController.saveBinanceTestnetCredentials(binanceTestnetKey.text, binanceTestnetSecret.text)
                                                        binanceTestnetKey.text = ""
                                                        binanceTestnetSecret.text = ""
                                                        window.showToast("Testnet key saved")
                                                    }
                                                }
                                            }
                                            RowLayout {
                                                Layout.fillWidth: true
                                                spacing: 10
                                                Button {
                                                    text: appController.checkingTestnet ? appController.wizardText.checking_status : appController.wizardText.check_testnet_button
                                                    enabled: !appController.checkingTestnet
                                                    onClicked: appController.checkBinanceTestnet()
                                                }
                                                StatusPill {
                                                    Layout.alignment: Qt.AlignVCenter
                                                    label: appController.testnetCheckStatus
                                                    tone: appController.testnetCheckState === "Verified" ? "success"
                                                        : appController.testnetCheckState === "Blocked" ? "danger" : "neutral"
                                                }
                                            }
                                            Text { Layout.fillWidth: true; text: appController.testnetCheckDetail; color: textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                        }
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        // Content-driven: a fixed height clipped the
                                        // wrapped note in longer translations.
                                        Layout.preferredHeight: liveTradeNoteRow.implicitHeight + 28
                                        radius: radiusMd
                                        color: panelRaised
                                        border.color: border
                                        RowLayout {
                                            id: liveTradeNoteRow
                                            anchors.left: parent.left
                                            anchors.right: parent.right
                                            anchors.verticalCenter: parent.verticalCenter
                                            anchors.leftMargin: 14
                                            anchors.rightMargin: 14
                                            spacing: 12
                                            Text {
                                                Layout.fillWidth: true
                                                text: appController.wizardText.live_trade_note
                                                color: textSecondary
                                                font.pixelSize: 12
                                                wrapMode: Text.WordWrap
                                            }
                                            Button {
                                                text: appController.wizardText.open_live_trade_guide_button
                                                onClicked: window.openGuide("binance-live-api")
                                            }
                                        }
                                    }
                                    Item { Layout.fillHeight: true }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 14
                                    Text { text: appController.wizardText.step6_title; color: textPrimary; font.pixelSize: 22; font.bold: true }
                                    Text {
                                        Layout.fillWidth: true
                                        text: appController.wizardText.step6_description
                                        color: textSecondary
                                        font.pixelSize: 13
                                        wrapMode: Text.WordWrap
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Button {
                                            text: appController.wizardText.open_safety_guide_button
                                            onClicked: window.openGuide("safety-model")
                                        }
                                        Button {
                                            text: appController.wizardText.open_portfolio_roles_guide_button
                                            onClicked: window.openGuide("portfolio-roles")
                                        }
                                        Item { Layout.fillWidth: true }
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        // The first-portfolio path needs room for the
                                        // basket list; the existing-portfolio path is
                                        // just two lines, so size it to the text
                                        // instead of leaving a large empty block.
                                        Layout.preferredHeight: appController.onboardingPath === "FIRST_PORTFOLIO"
                                            ? 300
                                            : summaryStepTitle.implicitHeight + summaryStepText.implicitHeight + 40
                                        radius: radiusMd
                                        color: panelRaised
                                        border.color: border
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 16
                                            spacing: 8
                                            Text {
                                                id: summaryStepTitle
                                                text: appController.onboardingPath === "FIRST_PORTFOLIO"
                                                    ? appController.wizardText.first_portfolio_plan_title
                                                    : appController.wizardText.existing_portfolio_next_step_title
                                                color: textPrimary
                                                font.pixelSize: 15
                                                font.bold: true
                                            }
                                            Text {
                                                id: summaryStepText
                                                Layout.fillWidth: true
                                                text: appController.onboardingPath === "FIRST_PORTFOLIO" ? appController.firstPortfolioPlanSummary : appController.readinessNextStep
                                                color: textSecondary
                                                font.pixelSize: 12
                                                wrapMode: Text.WordWrap
                                            }
                                            ListView {
                                                Layout.fillWidth: true
                                                Layout.fillHeight: true
                                                visible: appController.onboardingPath === "FIRST_PORTFOLIO"
                                                interactive: false
                                                spacing: 5
                                                model: appController.firstPortfolioFunding
                                                delegate: RowLayout {
                                                    required property var modelData
                                                    width: ListView.view.width
                                                    height: 26
                                                    Text { Layout.preferredWidth: 120; text: modelData.name; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                                    Text { Layout.preferredWidth: 110; text: modelData.value; color: accent; font.pixelSize: 11; font.bold: true }
                                                    ElidedDetail { Layout.fillWidth: true; text: modelData.detail; font.pixelSize: 10 }
                                                }
                                            }
                                        }
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 64 + appController.exchangeOnboardingSteps.length * 34
                                        radius: radiusMd
                                        color: panelRaised
                                        border.color: border
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 16
                                            spacing: 6
                                            Text { text: appController.wizardText.next_steps_outside_title; color: textPrimary; font.pixelSize: 15; font.bold: true }
                                            ListView {
                                                Layout.fillWidth: true
                                                Layout.fillHeight: true
                                                interactive: false
                                                spacing: 4
                                                model: appController.exchangeOnboardingSteps
                                                delegate: RowLayout {
                                                    required property var modelData
                                                    width: ListView.view.width
                                                    height: 26
                                                    Text { Layout.preferredWidth: 130; text: modelData.name; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                                    Text { Layout.preferredWidth: 100; text: modelData.value; color: accent; font.pixelSize: 11; font.bold: true }
                                                    ElidedDetail { Layout.fillWidth: true; text: modelData.detail; font.pixelSize: 10 }
                                                }
                                            }
                                        }
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 140 + appController.firstPortfolioAllocation.length * 28 + appController.firstPortfolioSteps.length * 34
                                        radius: radiusMd
                                        color: panelRaised
                                        border.color: border
                                        visible: appController.onboardingPath === "FIRST_PORTFOLIO"
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 16
                                            spacing: 8
                                            Text { text: appController.wizardText.suggested_first_basket_title; color: textPrimary; font.pixelSize: 15; font.bold: true }
                                            Text {
                                                Layout.fillWidth: true
                                                text: appController.wizardText.suggested_first_basket_description
                                                color: textSecondary
                                                font.pixelSize: 11
                                                wrapMode: Text.WordWrap
                                            }
                                            ListView {
                                                Layout.fillWidth: true
                                                Layout.preferredHeight: appController.firstPortfolioAllocation.length * 26
                                                interactive: false
                                                spacing: 2
                                                model: appController.firstPortfolioAllocation
                                                delegate: RowLayout {
                                                    required property var modelData
                                                    width: ListView.view.width
                                                    height: 24
                                                    Text { Layout.preferredWidth: 60; text: modelData.asset; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                                    Text { Layout.preferredWidth: 60; text: modelData.target; color: accent; font.pixelSize: 11; font.bold: true }
                                                    Text { Layout.fillWidth: true; text: modelData.role; color: textSecondary; font.pixelSize: 10; elide: Text.ElideRight }
                                                }
                                            }
                                            ListView {
                                                Layout.fillWidth: true
                                                Layout.preferredHeight: appController.firstPortfolioSteps.length * 30
                                                interactive: false
                                                spacing: 4
                                                model: appController.firstPortfolioSteps
                                                delegate: RowLayout {
                                                    required property var modelData
                                                    width: ListView.view.width
                                                    height: 28
                                                    Text { Layout.preferredWidth: 110; text: modelData.name; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                                    ElidedDetail { Layout.fillWidth: true; text: modelData.detail; font.pixelSize: 10 }
                                                }
                                            }
                                        }
                                    }
                                    ListView {
                                        Layout.fillWidth: true
                                        // Fits all rows: a fixed height cut the last one off.
                                        Layout.preferredHeight: contentHeight
                                        interactive: false
                                        spacing: 6
                                        model: appController.readinessSteps
                                        delegate: Rectangle {
                                            required property var modelData
                                            width: ListView.view.width
                                            height: 34
                                            radius: radiusSm
                                            color: panelRaised
                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.leftMargin: 12
                                                anchors.rightMargin: 12
                                                spacing: 10
                                                // Elides so a long translated label cannot run
                                                // into the status column.
                                                Text { Layout.preferredWidth: 180; text: modelData.name; color: textPrimary; font.pixelSize: 11; font.bold: true; elide: Text.ElideRight }
                                                Text { Layout.preferredWidth: 75; text: modelData.status; color: modelData.status === "READY" ? accent : modelData.status === "NEXT" ? warning : textSecondary; font.pixelSize: 10; font.bold: true }
                                                Text { Layout.fillWidth: true; text: modelData.action; color: textSecondary; font.pixelSize: 10; elide: Text.ElideRight }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: wizardAskAiContent.implicitHeight + 28
                    radius: radiusMd
                    color: panel
                    border.color: border
                    ColumnLayout {
                        id: wizardAskAiContent
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 14
                        spacing: 8
                        Text { text: appController.wizardText.ask_ai_title; color: textPrimary; font.pixelSize: 13; font.bold: true }
                        Text {
                            Layout.fillWidth: true
                            text: appController.wizardText.ask_ai_description
                            color: textSecondary
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            Layout.fillWidth: true
                            text: (appController.aiProviderBaseUrl.length > 0 && appController.aiTextModel.length > 0)
                                ? appController.wizardText.ask_ai_provider_status_configured + " " + appController.aiTextModel
                                : appController.wizardText.ask_ai_provider_status_missing
                            color: (appController.aiProviderBaseUrl.length > 0 && appController.aiTextModel.length > 0) ? accent : warning
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            TextField {
                                id: wizardAskAiInput
                                Layout.fillWidth: true
                                placeholderText: appController.wizardText.ask_ai_placeholder
                                onAccepted: {
                                    if (text.trim().length > 0 && !appController.wizardAssistantBusy)
                                        appController.askWizardAssistant(text, window.wizardSteps[window.wizardStep])
                                }
                            }
                            Button {
                                text: appController.wizardAssistantBusy ? appController.wizardText.ask_ai_asking_status : appController.wizardText.ask_ai_button
                                enabled: !appController.wizardAssistantBusy && wizardAskAiInput.text.trim().length > 0
                                onClicked: appController.askWizardAssistant(wizardAskAiInput.text, window.wizardSteps[window.wizardStep])
                            }
                        }
                        Text {
                            visible: appController.wizardAssistantAnswer.length > 0
                            Layout.fillWidth: true
                            text: appController.wizardAssistantAnswer
                            color: textPrimary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 58
                    Layout.bottomMargin: 18
                    Button {
                        text: appController.wizardText.back_button
                        enabled: window.wizardStep > 0
                        onClicked: window.wizardStep = Math.max(0, window.wizardStep - 1)
                    }
                    Text {
                        Layout.fillWidth: true
                        text: !window.canContinueWizard()
                            ? (window.wizardStep === 0 ? appController.wizardText.warn_choose_binance : window.wizardStep === 1 ? appController.wizardText.warn_choose_starting : appController.wizardText.warn_save_profile)
                            : ""
                        color: warning
                        font.pixelSize: 12
                    }
                    Button {
                        text: window.wizardStep === window.wizardSteps.length - 1 ? appController.wizardText.enter_coinductor_button : appController.wizardText.next_button
                        highlighted: true
                        enabled: window.wizardStep === window.wizardSteps.length - 1 ? appController.userProfileConfigured : window.canContinueWizard()
                        onClicked: {
                            if (window.wizardStep === window.wizardSteps.length - 1) {
                                appController.finishOnboardingWizard()
                            } else {
                                window.goNextWizardStep()
                            }
                        }
                    }
                }

                Item { Layout.fillWidth: true; Layout.preferredHeight: 24 }
            }
        }
    }

    RowLayout {
        visible: !appController.onboardingWizardVisible
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.preferredWidth: 248
            Layout.fillHeight: true
            color: panelSunken

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: spacingLg
                spacing: spacingXs

                RowLayout {
                    Layout.bottomMargin: spacingXl
                    spacing: spacingMd
                    AppLogo {
                        size: 38
                    }
                    Column {
                        Text { text: appController.appText.app_title; color: textPrimary; font.pixelSize: 19; font.bold: true }
                        Text { text: appController.appText.app_tagline; color: textSecondary; font.pixelSize: textSizeCaption }
                    }
                }

                Repeater {
                    id: navigationRepeater
                    model: window.navigationItems
                    delegate: Rectangle {
                        required property var modelData
                        required property int index
                        property bool current: appController.currentPage === modelData.page
                        Layout.fillWidth: true
                        Layout.preferredHeight: 42
                        radius: radiusSm
                        color: current ? panelRaised : "transparent"
                        Rectangle {
                            visible: parent.current
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            width: 3
                            height: 20
                            radius: 2
                            color: accent
                        }
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left
                            anchors.leftMargin: spacingLg
                            text: window.navLabelFor(modelData.page)
                            color: parent.current ? textPrimary : textSecondary
                            font.pixelSize: 14
                            font.bold: parent.current
                        }
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: appController.setCurrentPage(modelData.page)
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 86
                    radius: radiusSm
                    color: panel
                    border.color: appController.safetyAllowsLiveSubmit ? accent
                        : appController.safetyAllowsLivePreview ? warning : border
                    Column {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 6
                        Text { text: appController.appText.sidebar_safety_caption; color: textSecondary; font.pixelSize: 10; font.bold: true }
                        Row {
                            spacing: 8
                            Rectangle {
                                width: 8
                                height: 8
                                radius: 4
                                color: appController.safetyAllowsLiveSubmit ? accent
                                    : appController.safetyAllowsLivePreview ? warning : accent
                                anchors.verticalCenter: parent.verticalCenter
                            }
                            Text { text: appController.safetyStage; color: textPrimary; font.pixelSize: 13; font.bold: true }
                        }
                        Text {
                            width: parent.width
                            text: appController.safetyAllowsLiveSubmit ? appController.appText.safety_summary_live_guarded : appController.safetyAllowsLivePreview ? appController.appText.safety_summary_preview_only : appController.appText.safety_summary_no_exchange_changes
                            color: textSecondary
                            font.pixelSize: 10
                            elide: Text.ElideRight
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 72
                    radius: radiusSm
                    color: panel
                    border.color: border
                    Column {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 6
                        Text { text: appController.appText.sidebar_binance_caption; color: textSecondary; font.pixelSize: 10; font.bold: true }
                        Row {
                            spacing: 8
                            Rectangle {
                                width: 8
                                height: 8
                                radius: 4
                                color: appController.binanceConnectionState === "Connected" ? accent
                                    : appController.binanceConnectionState === "Checking" ? warning
                                    : appController.binanceConnectionState === "Blocked" ? "#ee6b6e" : textSecondary
                                anchors.verticalCenter: parent.verticalCenter
                            }
                            Text { text: appController.binanceConnectionStatus; color: textPrimary; font.pixelSize: 13 }
                        }
                    }
                }
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: appController.currentPage === 0
            contentWidth: availableWidth
            contentHeight: overviewPageContent.implicitHeight + 72
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                id: overviewPageContent
                x: 28
                y: 28
                width: window.pageContentWidth()
                spacing: 18

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: finishSetupBannerColumn.implicitHeight + 28
                    visible: appController.userProfileConfigured
                        && (!appController.binanceReadOnlyConfigured || appController.aiProviderBaseUrl.length === 0)
                    radius: radiusLg
                    color: warningSoft
                    border.color: warning
                    ColumnLayout {
                        id: finishSetupBannerColumn
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 14
                        spacing: 8
                        Text { text: appController.appText.overview_finish_setup_title; color: warning; font.pixelSize: 14; font.bold: true }
                        RowLayout {
                            Layout.fillWidth: true
                            visible: !appController.binanceReadOnlyConfigured
                            spacing: 12
                            Text {
                                Layout.fillWidth: true
                                text: appController.appText.overview_finish_setup_binance
                                color: textPrimary
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                            }
                            Button { text: appController.appText.overview_complete_binance_setup_button; onClicked: window.openWizardAtStep(4) }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            visible: appController.aiProviderBaseUrl.length === 0
                            spacing: 12
                            Text {
                                Layout.fillWidth: true
                                text: appController.appText.overview_finish_setup_ai
                                color: textSecondary
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                            }
                            Button { text: appController.appText.overview_setup_ai_button; onClicked: window.openWizardAtStep(3) }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text { text: appController.appText.overview_title; color: textPrimary; font.pixelSize: 26; font.bold: true }
                        Text {
                            Layout.fillWidth: true
                            text: appController.appText.overview_subtitle
                            color: textSecondary
                            font.pixelSize: 13
                            elide: Text.ElideRight
                        }
                    }
                    BusyDots {
                        Layout.alignment: Qt.AlignVCenter
                        visible: appController.busy
                    }
                    Button {
                        text: appController.busy ? appController.appText.running_status : appController.appText.overview_run_analysis_button
                        enabled: !appController.busy
                        highlighted: true
                        onClicked: runDialog.open()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: overviewSafetyContent.implicitHeight + 32
                    radius: radiusMd
                    color: panel
                    border.color: appController.safetyAllowsLiveSubmit ? accent
                        : appController.safetyAllowsLivePreview ? warning : border
                    ColumnLayout {
                        id: overviewSafetyContent
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 8
                        RowLayout {
                            Layout.fillWidth: true
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 3
                                Text { text: appController.appText.overview_safety_title; color: textPrimary; font.pixelSize: 15; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: appController.safetyStageCode === "SETUP"
                                        ? appController.hasCompletedRealAnalysis
                                            ? appController.appText.overview_safety_setup_with_analysis
                                            : appController.appText.overview_safety_setup_no_analysis
                                        : appController.safetyDetail
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                            }
                            StatusPill {
                                Layout.alignment: Qt.AlignVCenter
                                label: appController.safetyStage
                                tone: appController.safetyAllowsLiveSubmit ? "success" : appController.safetyAllowsLivePreview ? "warning" : "neutral"
                            }
                            Button {
                                text: appController.safetyStageCode === "SETUP" && !appController.hasCompletedRealAnalysis
                                    ? appController.appText.overview_run_analysis_button
                                    : appController.appText.overview_open_live_actions_button
                                onClicked: {
                                    if (appController.safetyStageCode === "SETUP" && !appController.hasCompletedRealAnalysis)
                                        runDialog.open()
                                    else
                                        appController.setCurrentPage(1)
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.appText.overview_safety_never_places_order
                            color: warning
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                ProgressBar {
                    Layout.fillWidth: true
                    visible: appController.busy
                    from: 0
                    to: 100
                    value: appController.progress
                }
                Text {
                    visible: appController.busy
                    text: appController.statusText
                    color: textSecondary
                    font.pixelSize: 12
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 4
                    columnSpacing: 12
                    rowSpacing: 12
                    MetricCard { title: appController.appText.metric_portfolio_title; value: appController.portfolioValue; accentColor: accent; helpText: appController.appText.metric_portfolio_help }
                    MetricCard { title: appController.appText.metric_liquid_title; value: appController.liquidValue; accentColor: "#5aa9e6"; helpText: appController.appText.metric_liquid_help }
                    MetricCard { title: appController.appText.metric_locked_title; value: appController.lockedValue; accentColor: warning; helpText: appController.appText.metric_locked_help }
                    // The reason is repeated in the tooltip so it stays fully
                    // readable even when the card has to truncate it.
                    MetricCard {
                        title: appController.appText.metric_risk_gate_title
                        value: appController.riskState
                        accentColor: "#d66b75"
                        helpText: appController.appText.metric_risk_gate_help + "\n\n" + appController.riskState
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 148
                    radius: radiusMd
                    color: panel
                    border.color: border
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 8
                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: appController.appText.overview_latest_decision_title; color: textSecondary; font.pixelSize: 12; font.bold: true }
                            Item { Layout.fillWidth: true }
                            StatusPill {
                                label: appController.decision
                                tone: appController.decision === "HOLD" ? "warning" : "success"
                                MouseArea {
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.WhatsThisCursor
                                    ToolTip.visible: containsMouse
                                    ToolTip.text: appController.appText.overview_decision_tooltip
                                    ToolTip.delay: 300
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.decisionSummary
                            color: textPrimary
                            font.pixelSize: 16
                            wrapMode: Text.WordWrap
                        }
                        Item { Layout.fillHeight: true }
                        Button {
                            text: appController.appText.open_detailed_report_button
                            enabled: appController.hasReport
                            onClicked: appController.openReport()
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop
                    spacing: 14
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 280
                        radius: radiusMd
                        color: panel
                        border.color: border
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 18
                            Text { text: appController.appText.overview_recommended_actions_title; color: textPrimary; font.pixelSize: 16; font.bold: true }
                            ListView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                spacing: 8
                                clip: true
                                model: appController.actions
                                delegate: Rectangle {
                                    required property var modelData
                                    width: ListView.view.width
                                    height: actionColumn.implicitHeight + 20
                                    radius: radiusSm
                                    color: panelRaised
                                    Column {
                                        id: actionColumn
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.top: parent.top
                                        anchors.margins: 10
                                        spacing: 4
                                        Text {
                                            text: modelData.priority + "  " + modelData.action
                                            color: textPrimary
                                            font.pixelSize: 13
                                            font.bold: true
                                            width: parent.width
                                            wrapMode: Text.WordWrap
                                        }
                                        Text {
                                            text: modelData.reason
                                            color: textSecondary
                                            font.pixelSize: 11
                                            width: parent.width
                                            wrapMode: Text.WordWrap
                                        }
                                    }
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.preferredWidth: 360
                        Layout.preferredHeight: 280
                        radius: radiusMd
                        color: panel
                        border.color: border
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 18
                            Text { text: appController.appText.overview_ai_summary_title; color: textPrimary; font.pixelSize: 16; font.bold: true }
                            // The model decides how much it writes, so this
                            // panel scrolls rather than spilling past its own
                            // border. Selectable too: it is the one thing here
                            // worth quoting back when a model misbehaves.
                            ScrollView {
                                id: aiSummaryScroll
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                                TextEdit {
                                    // Not parent.width: inside a ScrollView the
                                    // parent is the internal Flickable, whose
                                    // width follows the content rather than the
                                    // view. Binding to it leaves the width
                                    // unresolved, wrapMode has nothing to wrap
                                    // against, and the model's summary runs off
                                    // the panel on a single line.
                                    width: aiSummaryScroll.availableWidth
                                    text: appController.aiSummary
                                    color: textSecondary
                                    font.pixelSize: 13
                                    wrapMode: TextEdit.Wrap
                                    readOnly: true
                                    selectByMouse: true
                                    selectionColor: accent
                                }
                            }
                        }
                    }
                }
            }
        }

        ScrollView {
            id: portfolioScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: appController.currentPage === 2
            contentWidth: availableWidth
            contentHeight: portfolioPageContent.implicitHeight + 72
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                id: portfolioPageContent
                x: 28
                y: 28
                width: window.pageContentWidth()
                spacing: 18

                Text { text: appController.appText.portfolio_title; color: textPrimary; font.pixelSize: 26; font.bold: true }
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: appController.appText.portfolio_subtitle
                        color: textSecondary
                        font.pixelSize: 14
                        elide: Text.ElideRight
                    }
                    ComboBox {
                        Layout.preferredWidth: 190
                        Layout.preferredHeight: 34
                        model: [
                            { label: appController.appText.portfolio_sort_value_desc, value: "VALUE_DESC" },
                            { label: appController.appText.portfolio_sort_value_asc, value: "VALUE_ASC" },
                            { label: appController.appText.portfolio_sort_asset_asc, value: "ASSET_ASC" },
                            { label: appController.appText.portfolio_sort_role_asc, value: "ROLE_ASC" }
                        ]
                        textRole: "label"
                        valueRole: "value"
                        currentIndex: appController.portfolioSortMode === "VALUE_ASC" ? 1
                            : appController.portfolioSortMode === "ASSET_ASC" ? 2
                            : appController.portfolioSortMode === "ROLE_ASC" ? 3 : 0
                        onActivated: function(index) {
                            appController.setPortfolioSortMode(model[index].value)
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 42
                    color: panelRaised
                    border.color: border
                    radius: radiusSm
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 14
                        anchors.rightMargin: 14
                        spacing: 12
                        Text { Layout.preferredWidth: 70; text: appController.appText.portfolio_col_asset; color: textSecondary; font.pixelSize: 10; font.bold: true }
                        Text { Layout.preferredWidth: 210; text: appController.appText.portfolio_col_policy; color: textSecondary; font.pixelSize: 11; font.bold: true }
                        Text { Layout.preferredWidth: 120; text: appController.appText.portfolio_col_value; color: textSecondary; font.pixelSize: 10; font.bold: true }
                        Text { Layout.preferredWidth: 75; text: appController.appText.portfolio_col_share; color: textSecondary; font.pixelSize: 10; font.bold: true }
                        Text { Layout.fillWidth: true; text: appController.appText.portfolio_col_liquidity; color: textSecondary; font.pixelSize: 10; font.bold: true }
                        Text { Layout.preferredWidth: 120; text: appController.appText.portfolio_col_source; color: textSecondary; font.pixelSize: 10; font.bold: true }
                    }
                }

                Rectangle {
                    // Connecting a key proves access; it fetches nothing. The
                    // table reads the latest real run, so before the first one
                    // it is empty - which looked like a failure to load.
                    Layout.fillWidth: true
                    Layout.preferredHeight: portfolioEmptyColumn.implicitHeight + 28
                    visible: appController.portfolioAssets.length === 0
                    radius: radiusSm
                    color: panelRaised
                    border.color: border
                    ColumnLayout {
                        id: portfolioEmptyColumn
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: 16
                        anchors.rightMargin: 16
                        spacing: 6
                        Text {
                            Layout.fillWidth: true
                            text: appController.appText.portfolio_empty_title
                            color: textPrimary
                            font.pixelSize: 13
                            font.bold: true
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.appText.portfolio_empty_detail
                            color: textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Button {
                            text: appController.appText.portfolio_empty_action
                            onClicked: runDialog.open()
                        }
                    }
                }

                ListView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: appController.portfolioAssets.length === 0 ? 0 : Math.max(420, contentHeight)
                    visible: appController.portfolioAssets.length > 0
                    spacing: 6
                    model: appController.portfolioAssets
                    delegate: Rectangle {
                        required property var modelData
                        width: ListView.view.width
                        height: 76
                        radius: radiusSm
                        color: panel
                        border.color: border
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 14
                            anchors.rightMargin: 14
                            spacing: 12
                            Text { Layout.preferredWidth: 70; text: modelData.asset; color: textPrimary; font.pixelSize: 14; font.bold: true }
                            ColumnLayout {
                                Layout.preferredWidth: 210
                                spacing: 3
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.roleLabel
                                    color: modelData.policySource === "MANUAL" ? accent : textSecondary
                                    font.pixelSize: 12
                                    font.bold: modelData.policySource === "MANUAL"
                                    elide: Text.ElideRight
                                }
                                ComboBox {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 30
                                    model: appController.assetRoleOptionItems
                                    textRole: "label"
                                    valueRole: "value"
                                    currentIndex: appController.assetRoleOptions.indexOf(modelData.roleOverride)
                                    font.pixelSize: 11
                                    onActivated: function(index) {
                                        appController.saveAssetRoleOverride(modelData.asset, currentValue)
                                        window.showToast(appController.appText.portfolio_policy_changed_toast.replace("{asset}", modelData.asset).replace("{role}", currentText))
                                    }
                                    ToolTip.visible: hovered
                                    ToolTip.text: modelData.roleHelp
                                }
                            }
                            Text { Layout.preferredWidth: 120; text: modelData.value; color: textPrimary; font.pixelSize: 13 }
                            Text { Layout.preferredWidth: 75; text: modelData.allocation; color: textPrimary; font.pixelSize: 13 }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Text { text: appController.appText.portfolio_spot_label + " " + modelData.spot + "   " + appController.appText.portfolio_flexible_label + " " + modelData.flexible; color: textSecondary; font.pixelSize: 11 }
                                Text { text: appController.appText.portfolio_locked_label + " " + modelData.locked; color: textSecondary; font.pixelSize: 11 }
                            }
                            ColumnLayout {
                                Layout.preferredWidth: 120
                                spacing: 3
                                Text {
                                    text: modelData.policySourceLabel
                                    color: modelData.policySource === "MANUAL" ? accent : textSecondary
                                    font.pixelSize: 11
                                    font.bold: true
                                }
                                Text {
                                    text: modelData.action
                                    color: modelData.action === "HOLD" ? textSecondary : accent
                                    font.pixelSize: 10
                                    elide: Text.ElideRight
                                }
                            }
                        }
                    }
                }
            }
        }

        ScrollView {
            id: actionPlanScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: appController.currentPage === 3
            contentWidth: availableWidth
            contentHeight: actionPlanPageContent.implicitHeight + 72
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                id: actionPlanPageContent
                x: 28
                y: 28
                width: window.pageContentWidth()
                spacing: 18

                RowLayout {
                    width: parent.width
                    Layout.fillWidth: true
                    spacing: 16
                    ColumnLayout {
                        spacing: 4
                        Text { text: appController.appText.action_plan_title; color: textPrimary; font.pixelSize: 26; font.bold: true }
                        Text { text: appController.appText.action_plan_subtitle; color: textSecondary; font.pixelSize: 13 }
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        text: appController.appText.open_detailed_report_button
                        enabled: appController.hasReport
                        onClicked: appController.openReport()
                    }
                }

                Loader {
                    Layout.fillWidth: true
                    Layout.preferredHeight: item && item.visible ? item.implicitHeight : 0
                    sourceComponent: nextReviewPanelComponent
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: firstPortfolioDeploymentContent.implicitHeight + 32
                    visible: appController.onboardingPath === "FIRST_PORTFOLIO" && appController.firstPortfolioAllocation.length > 0
                    radius: radiusMd
                    color: panel
                    border.color: border
                    ColumnLayout {
                        id: firstPortfolioDeploymentContent
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        Text { text: appController.appText.first_portfolio_deployment_title; color: textPrimary; font.pixelSize: 16; font.bold: true }
                        Text {
                            Layout.fillWidth: true
                            text: appController.appText.first_portfolio_deployment_description
                            color: textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Repeater {
                            model: appController.firstPortfolioAllocation
                            delegate: Rectangle {
                                required property var modelData
                                Layout.fillWidth: true
                                // Tall enough for a default Material button. It
                                // was 40, which is shorter than the button asks
                                // for - shrinking the button instead made these
                                // the only odd-sized buttons in the app.
                                Layout.preferredHeight: 56
                                radius: radiusSm
                                color: panelRaised
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 12
                                    anchors.rightMargin: 12
                                    spacing: 10
                                    Text { Layout.preferredWidth: 60; text: modelData.asset; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                    Text { Layout.preferredWidth: 50; text: modelData.target; color: accent; font.pixelSize: 12 }
                                    Text {
                                        Layout.fillWidth: true
                                        text: appController.appText.first_portfolio_testnet_label + " " + window.firstPortfolioProgressCount(modelData.asset, "TESTNET") + "/" + firstPortfolioTranchesInput.value
                                            + "  ·  " + appController.appText.first_portfolio_mainnet_label + " " + window.firstPortfolioProgressCount(modelData.asset, "MAINNET") + "/" + firstPortfolioTranchesInput.value
                                        color: textSecondary
                                        font.pixelSize: 11
                                    }
                                    Button {
                                        text: appController.appText.first_portfolio_deploy_button
                                        enabled: !appController.busy
                                        onClicked: {
                                            firstPortfolioDeployAsset = modelData.asset
                                            firstPortfolioDeployTargetPct = modelData.targetPct
                                            firstPortfolioConfirmInput.text = ""
                                            firstPortfolioDeployDialog.open()
                                        }
                                    }
                                }
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Text { text: appController.appText.first_portfolio_budget_label; color: textSecondary; font.pixelSize: 11 }
                            TextField { id: firstPortfolioBudgetInput; Layout.preferredWidth: 120; placeholderText: "e.g. 400" }
                            Text { text: appController.appText.first_portfolio_tranches_label; color: textSecondary; font.pixelSize: 11 }
                            SpinBox { id: firstPortfolioTranchesInput; from: 1; to: 10; value: 3 }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.appText.first_portfolio_budget_warning
                            color: warning
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    visible: appController.actionPlanItems.length > 0
                    spacing: 16
                    Row {
                        spacing: 6
                        Rectangle { width: 10; height: 10; radius: 5; color: accent; anchors.verticalCenter: parent.verticalCenter }
                        Text { text: appController.appText.legend_ready; color: textSecondary; font.pixelSize: 11 }
                    }
                    Row {
                        spacing: 6
                        Rectangle { width: 10; height: 10; radius: 5; color: warning; anchors.verticalCenter: parent.verticalCenter }
                        Text { text: appController.appText.legend_watch; color: textSecondary; font.pixelSize: 11 }
                    }
                    Row {
                        spacing: 6
                        Rectangle { width: 10; height: 10; radius: 5; color: textSecondary; anchors.verticalCenter: parent.verticalCenter }
                        Text { text: appController.appText.legend_other; color: textSecondary; font.pixelSize: 11 }
                    }
                    Item { Layout.fillWidth: true }
                }

                ListView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.max(620, contentHeight)
                    spacing: 10
                    model: appController.actionPlanItems
                    delegate: Rectangle {
                        required property var modelData
                        width: ListView.view.width
                        height: Math.max(216, actionPlanCardContent.implicitHeight + 40)
                        radius: radiusMd
                        color: panel
                        border.color: modelData.tone === "ready" ? accent : warning
                        ColumnLayout {
                            id: actionPlanCardContent
                            anchors.fill: parent
                            anchors.margins: 18
                            spacing: 10
                            RowLayout {
                                Layout.fillWidth: true
                                Text { Layout.fillWidth: true; text: modelData.title; color: textPrimary; font.pixelSize: 17; font.bold: true; elide: Text.ElideRight }
                                StatusPill {
                                    label: modelData.status
                                    tone: modelData.tone === "ready" ? "success" : modelData.tone === "watch" ? "warning" : "neutral"
                                }
                            }
                            GridLayout {
                                Layout.fillWidth: true
                                columns: 4
                                columnSpacing: 20
                                rowSpacing: 8
                                Repeater {
                                    model: window.toModel(modelData.parameters)
                                    delegate: ColumnLayout {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        spacing: 2
                                        Text { text: modelData.label; color: textSecondary; font.pixelSize: 10; font.bold: true }
                                        CopyableValue {
                                            Layout.fillWidth: true
                                            value: modelData.value
                                            font.pixelSize: 12
                                        }
                                    }
                                }
                            }
                            // Full width and wrapping. A blocker is a sentence,
                            // and in the tile grid beside "Grids: 8" it could
                            // only ever be cut off mid-word.
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 3
                                visible: (modelData.blockers || []).length > 0
                                Text {
                                    text: appController.appText.blockers_label
                                    color: textSecondary
                                    font.pixelSize: 10
                                    font.bold: true
                                }
                                Repeater {
                                    model: window.toModel(modelData.blockers)
                                    delegate: Text {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        text: "- " + modelData
                                        color: warning
                                        font.pixelSize: 12
                                        wrapMode: Text.WordWrap
                                    }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: tradeLifecycleSummary.implicitHeight + 22
                                visible: modelData.liveLifecycle !== undefined && modelData.liveLifecycle !== null
                                radius: radiusSm
                                color: panelRaised
                                border.color: modelData.liveLifecycle && modelData.liveLifecycle.tone === "ready" ? accent : border
                                RowLayout {
                                    id: tradeLifecycleSummary
                                    anchors.fill: parent
                                    anchors.margins: 11
                                    spacing: 12
                                    Text {
                                        text: appController.appText.last_live_trade_label
                                        color: textPrimary
                                        font.pixelSize: 11
                                        font.bold: true
                                    }
                                    Text {
                                        text: modelData.liveLifecycle ? modelData.liveLifecycle.status : ""
                                        color: modelData.liveLifecycle && modelData.liveLifecycle.tone === "ready" ? accent : warning
                                        font.pixelSize: 11
                                        font.bold: true
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text: modelData.liveLifecycle ? modelData.liveLifecycle.detail : ""
                                        color: textSecondary
                                        font.pixelSize: 10
                                        elide: Text.ElideRight
                                    }
                                }
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 12
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.detail
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                    maximumLineCount: 3
                                    elide: Text.ElideRight
                                }
                                Button {
                                    Layout.alignment: Qt.AlignVCenter
                                    Layout.minimumWidth: 170
                                    text: modelData.primaryLabel || appController.appText.review_button
                                    enabled: modelData.actionCode !== "NONE"
                                    highlighted: modelData.tone === "ready"
                                    onClicked: {
                                        window.activeActionPlanCode = modelData.actionCode || ""
                                        window.activeActionPlanTitle = modelData.title || ""
                                        window.activeActionPlanItem = modelData
                                        actionPlanDetailDialog.open()
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: appController.currentPage === 4
            contentWidth: availableWidth
            contentHeight: activeStrategiesContent.implicitHeight + 72
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                id: activeStrategiesContent
                x: 28
                y: 28
                width: window.pageContentWidth()
                spacing: 18

                RowLayout {
                    Layout.fillWidth: true
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text { text: appController.appText.active_strategies_title; color: textPrimary; font.pixelSize: 26; font.bold: true }
                        Text { Layout.fillWidth: true; text: appController.activeStrategiesSummary; color: textSecondary; font.pixelSize: 13; wrapMode: Text.WordWrap }
                    }
                    // A swapped label was the only sign this was working, and it
                    // sits still for the whole run - which reads as a hang on a
                    // button that quietly starts a full analysis. Every other
                    // page already animates with BusyDots; this one was missed.
                    BusyDots {
                        Layout.alignment: Qt.AlignVCenter
                        visible: appController.busy
                    }
                    Button {
                        text: appController.busy ? appController.appText.refreshing_status : appController.appText.refresh_monitoring_button
                        enabled: !appController.busy
                        onClicked: appController.refreshActiveStrategies()
                        ToolTip.visible: hovered
                        ToolTip.text: appController.appText.refresh_monitoring_tooltip
                    }
                    Button {
                        text: appController.appText.register_active_bot_button
                        enabled: !appController.busy
                        onClicked: strategyRegistrationDialog.open()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    // Content-driven: a fixed height plus a greedy spacer left a
                    // large empty block under this short empty-state text.
                    Layout.preferredHeight: noActiveBotsContent.implicitHeight + 36
                    visible: appController.activeStrategies.length === 0
                    radius: radiusMd
                    color: panel
                    border.color: border
                    ColumnLayout {
                        id: noActiveBotsContent
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 18
                        spacing: 10
                        Text {
                            text: appController.registeredStrategyCount > 0 ? appController.appText.monitoring_evaluation_pending_title : appController.appText.no_active_bots_title
                            color: textPrimary
                            font.pixelSize: 17
                            font.bold: true
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.registeredStrategyCount > 0
                                  ? appController.appText.monitoring_evaluation_pending_detail
                                  : appController.appText.no_active_bots_detail
                            color: textSecondary
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Item { Layout.fillWidth: true }
                            Button { text: appController.appText.register_active_bot_button; onClicked: strategyRegistrationDialog.open() }
                            Button { text: appController.appText.open_action_plan_button; onClicked: appController.setCurrentPage(3) }
                        }
                    }
                }

                Component {
                    id: nextReviewPanelComponent
                    Rectangle {
                    implicitHeight: nextReviewContent.implicitHeight + 36
                    visible: Object.keys(appController.nextReview).length > 0
                    radius: radiusMd
                    color: panel
                    border.color: appController.nextReview.tone === "blocked" ? warning : border
                    ColumnLayout {
                        id: nextReviewContent
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 12
                        RowLayout {
                            Layout.fillWidth: true
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 3
                                Text { text: appController.appText.next_review_title; color: textPrimary; font.pixelSize: 17; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: appController.nextReview.headline || ""
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                            }
                            StatusPill {
                                label: appController.nextReview.status || appController.appText.next_review_not_scheduled
                                tone: appController.nextReview.tone === "blocked" ? "warning" : "neutral"
                            }
                        }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: width < 760 ? 1 : 3
                            columnSpacing: 24
                            rowSpacing: 8
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.next_review_suggested_timing; color: textSecondary; font.pixelSize: 10; font.bold: true }
                                Text { Layout.fillWidth: true; text: appController.nextReview.timing || appController.appText.next_review_not_available; color: textPrimary; font.pixelSize: 12; wrapMode: Text.WordWrap }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.next_review_scheduled_from_run; color: textSecondary; font.pixelSize: 10; font.bold: true }
                                Text { Layout.fillWidth: true; text: appController.nextReview.scheduledAt || appController.appText.next_review_not_available; color: textPrimary; font.pixelSize: 12; wrapMode: Text.WordWrap }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.next_review_profile_cadence; color: textSecondary; font.pixelSize: 10; font.bold: true }
                                Text { Layout.fillWidth: true; text: appController.nextReview.profileCadence || appController.appText.next_review_not_configured; color: textPrimary; font.pixelSize: 12; wrapMode: Text.WordWrap }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.nextReview.reason || ""
                            color: textSecondary
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                        }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: width < 760 ? 1 : 2
                            columnSpacing: 28
                            rowSpacing: 12
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 5
                                Text { text: appController.appText.next_review_run_earlier_if_title; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: appController.appText.next_review_run_earlier_if_description
                                    color: textSecondary
                                    font.pixelSize: 10
                                    wrapMode: Text.WordWrap
                                }
                                Repeater {
                                    model: window.toModel(appController.nextReview.triggers)
                                    delegate: Text {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        text: "- " + modelData
                                        color: textSecondary
                                        font.pixelSize: 11
                                        wrapMode: Text.WordWrap
                                    }
                                }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 5
                                Text { text: appController.appText.next_review_resolve_before_rerun_title; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: appController.appText.next_review_resolve_before_rerun_description
                                    color: textSecondary
                                    font.pixelSize: 10
                                    wrapMode: Text.WordWrap
                                }
                                Text {
                                    Layout.fillWidth: true
                                    visible: (appController.nextReview.manualSteps || []).length === 0
                                    text: appController.appText.next_review_no_manual_prerequisite
                                    color: textSecondary
                                    font.pixelSize: 11
                                    wrapMode: Text.WordWrap
                                }
                                Repeater {
                                    model: window.toModel(appController.nextReview.manualSteps)
                                    delegate: Text {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        text: "- " + modelData
                                        color: warning
                                        font.pixelSize: 11
                                        font.bold: true
                                        wrapMode: Text.WordWrap
                                    }
                                }
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                Layout.fillWidth: true
                                text: appController.appText.next_review_ai_disclaimer_prefix + " " + (appController.nextReview.sourceRun || "-") + ". " + appController.appText.next_review_ai_disclaimer_suffix
                                color: textSecondary
                                font.pixelSize: 10
                                wrapMode: Text.WordWrap
                            }
                            Button {
                                text: appController.appText.run_analysis_now_button
                                enabled: !appController.busy
                                onClicked: runDialog.open()
                            }
                        }
                    }
                }
                }

                ListView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: contentHeight
                    visible: appController.activeStrategies.length > 0
                    interactive: false
                    spacing: 12
                    model: appController.activeStrategies
                    delegate: Rectangle {
                        required property var modelData
                        width: ListView.view.width
                        height: Math.max(250, activeStrategyCardContent.implicitHeight + 36)
                        radius: radiusMd
                        color: panel
                        border.color: modelData.tone === "ready" ? accent : warning
                        ColumnLayout {
                            id: activeStrategyCardContent
                            anchors.fill: parent
                            anchors.margins: 18
                            spacing: 12
                            RowLayout {
                                Layout.fillWidth: true
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 3
                                    Text { text: modelData.name; color: textPrimary; font.pixelSize: 17; font.bold: true }
                                    Text { text: modelData.type + "  |  " + appController.appText.binance_id_label + " " + modelData.botId; color: textSecondary; font.pixelSize: 11 }
                                }
                                StatusPill {
                                    label: modelData.health
                                    tone: modelData.tone === "ready" ? "success" : modelData.tone === "watch" ? "warning" : "danger"
                                }
                            }
                            Text { text: modelData.state; color: modelData.tone === "ready" ? accent : warning; font.pixelSize: 11; font.bold: true }
                            GridLayout {
                                Layout.fillWidth: true
                                columns: 4
                                columnSpacing: 18
                                rowSpacing: 8
                                Repeater {
                                    model: window.toModel(modelData.parameters)
                                    delegate: ColumnLayout {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        spacing: 2
                                        Text { text: modelData.label; color: textSecondary; font.pixelSize: 10; font.bold: true }
                                        CopyableValue { Layout.fillWidth: true; value: modelData.value; font.pixelSize: 11 }
                                    }
                                }
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 12
                                Text { Layout.fillWidth: true; text: modelData.recommendation; color: textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap; maximumLineCount: 3; elide: Text.ElideRight }
                                Button {
                                    Layout.minimumWidth: 150
                                    text: appController.appText.view_details_button
                                    onClicked: {
                                        window.activeStrategyItem = modelData
                                        activeStrategyDetailDialog.open()
                                    }
                                }
                            }
                        }
                    }
                }
                Item { Layout.fillWidth: true; Layout.preferredHeight: 36 }
            }
        }

        ScrollView {
            id: runHistoryScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: appController.currentPage === 5
            contentWidth: availableWidth
            contentHeight: runHistoryPageContent.implicitHeight + 72
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                id: runHistoryPageContent
                x: 28
                y: 28
                width: window.pageContentWidth()
                spacing: 18

                Text { text: appController.appText.run_history_title; color: textPrimary; font.pixelSize: 26; font.bold: true }
                Text { Layout.fillWidth: true; text: appController.appText.run_history_subtitle; color: textSecondary; font.pixelSize: 13; wrapMode: Text.WordWrap }
                Text {
                    Layout.fillWidth: true
                    text: appController.appText.run_history_description
                    color: textSecondary
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }

                ListView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.max(480, contentHeight)
                    spacing: 6
                    model: appController.runHistory
                    delegate: Rectangle {
                        required property var modelData
                        width: ListView.view.width
                        height: 78
                        radius: radiusSm
                        color: panel
                        border.color: border
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 14
                            spacing: 14
                            ColumnLayout {
                                Layout.preferredWidth: 85
                                Text { text: appController.appText.run_history_run_label + " " + modelData.runId; color: textPrimary; font.pixelSize: 13; font.bold: true }
                                Text { text: modelData.dataMode; color: modelData.dataMode === "REAL" ? accent : warning; font.pixelSize: 10; font.bold: true }
                            }
                            ColumnLayout {
                                // Widened for the timezone suffix: the stored
                                // time is UTC, so it has to say which clock it
                                // is on now that it is converted.
                                Layout.preferredWidth: 190
                                Text { text: modelData.startedAt; color: textSecondary; font.pixelSize: 10; elide: Text.ElideRight }
                                Text { text: modelData.status; color: textPrimary; font.pixelSize: 11 }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: modelData.decision; color: textPrimary; font.pixelSize: 13; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.summary
                                    color: textSecondary
                                    font.pixelSize: 11
                                    elide: Text.ElideRight
                                }
                            }
                            Button {
                                text: appController.appText.open_run_report_button
                                visible: modelData.reportPath !== ""
                                onClicked: appController.openRunReport(modelData.reportPath)
                            }
                        }
                    }
                }
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: appController.currentPage === 6

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 28
                spacing: 14

                Text { text: appController.appText.assistant_title; color: textPrimary; font.pixelSize: 26; font.bold: true }
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: appController.appText.assistant_context_prefix + " " + appController.assistantContextPage
                        color: textSecondary
                        font.pixelSize: 14
                    }
                    Rectangle {
                        Layout.preferredWidth: 280
                        Layout.minimumWidth: 180
                        Layout.preferredHeight: 34
                        radius: radiusSm
                        color: panel
                        border.color: border
                        Text {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            verticalAlignment: Text.AlignVCenter
                            text: appController.appText.assistant_active_ai_prefix + " " + appController.aiProviderSummary
                            color: textSecondary
                            font.pixelSize: 12
                            elide: Text.ElideRight
                        }
                    }
                    Button {
                        text: appController.appText.assistant_history_button
                        onClicked: assistantHistoryDialog.open()
                    }
                    Button {
                        text: appController.appText.assistant_new_chat_button
                        enabled: !appController.assistantBusy
                        onClicked: appController.newAssistantChat()
                    }
                }

                ListView {
                    id: assistantList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 10
                    clip: true
                    model: appController.assistantMessages
                    onCountChanged: positionViewAtEnd()
                    delegate: Item {
                        id: assistantMessageDelegate
                        required property var modelData
                        property bool isTyping: modelData.role === "typing"
                        property bool hasImage: !isTyping && modelData.imageUrl !== undefined && String(modelData.imageUrl).length > 0
                        width: ListView.view.width
                        height: isTyping ? 44 : messageBubble.implicitHeight
                        Rectangle {
                            id: messageBubble
                            width: assistantMessageDelegate.isTyping ? 72 : Math.min(parent.width * 0.72, Math.max(assistantMessageDelegate.hasImage ? 380 : 280, messageText.implicitWidth + 30))
                            implicitHeight: assistantMessageDelegate.isTyping ? 44 : messageContent.implicitHeight + 24
                            anchors.right: modelData.role === "user" ? parent.right : undefined
                            anchors.left: modelData.role === "user" ? undefined : parent.left
                            radius: radiusMd
                            color: modelData.role === "user" ? "#234f43" : panel
                            border.color: modelData.role === "user" ? "#337660" : border
                            Column {
                                id: messageContent
                                anchors.fill: parent
                                anchors.margins: 12
                                visible: !assistantMessageDelegate.isTyping
                                spacing: 8
                                Image {
                                    width: parent.width
                                    height: assistantMessageDelegate.hasImage ? 180 : 0
                                    visible: assistantMessageDelegate.hasImage
                                    source: assistantMessageDelegate.hasImage ? modelData.imageUrl : ""
                                    fillMode: Image.PreserveAspectFit
                                    asynchronous: true
                                    sourceSize.width: 640
                                    sourceSize.height: 360
                                }
                                TextEdit {
                                    id: messageText
                                    width: parent.width
                                    text: modelData.text
                                    color: textPrimary
                                    font.pixelSize: 13
                                    wrapMode: TextEdit.Wrap
                                    textFormat: TextEdit.PlainText
                                    readOnly: true
                                    selectByMouse: true
                                    persistentSelection: true
                                    selectionColor: accent
                                    selectedTextColor: "#08130f"
                                }
                            }
                            Row {
                                visible: assistantMessageDelegate.isTyping
                                anchors.centerIn: parent
                                spacing: 6
                                Repeater {
                                    model: 3
                                    delegate: Rectangle {
                                        required property int index
                                        width: 7
                                        height: 7
                                        radius: 4
                                        color: accent
                                        opacity: 0.25
                                        SequentialAnimation on opacity {
                                            running: assistantMessageDelegate.isTyping
                                            loops: Animation.Infinite
                                            PauseAnimation { duration: index * 140 }
                                            NumberAnimation { from: 0.25; to: 1.0; duration: 320; easing.type: Easing.InOutQuad }
                                            NumberAnimation { from: 1.0; to: 0.25; duration: 320; easing.type: Easing.InOutQuad }
                                            PauseAnimation { duration: (2 - index) * 140 }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: assistantActionContent.implicitHeight + 28
                    visible: Object.keys(appController.assistantPendingAction).length > 0
                    radius: radiusMd
                    color: panelRaised
                    border.color: accent

                    ColumnLayout {
                        id: assistantActionContent
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 14
                        spacing: 8
                        Text { Layout.fillWidth: true; text: appController.assistantPendingAction.title || appController.appText.assistant_proposed_action_title; color: textPrimary; font.pixelSize: 15; font.bold: true; wrapMode: Text.WordWrap }
                        Text { Layout.fillWidth: true; text: appController.assistantPendingAction.description || ""; color: textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap }
                        RowLayout {
                            Layout.alignment: Qt.AlignRight
                            spacing: 8
                            Button { text: appController.appText.assistant_dismiss_button; onClicked: appController.dismissAssistantAction() }
                            Button { text: appController.assistantPendingAction.confirmLabel || appController.appText.assistant_confirm_button; highlighted: true; onClicked: appController.confirmAssistantAction() }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 92
                    visible: Object.keys(appController.assistantAttachment).length > 0
                    radius: radiusMd
                    color: panelRaised
                    border.color: appController.assistantVisionAvailable ? accent : warning

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 12
                        Image {
                            Layout.preferredWidth: 70
                            Layout.preferredHeight: 70
                            source: appController.assistantAttachment.url || ""
                            fillMode: Image.PreserveAspectFit
                            asynchronous: true
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 3
                            Text {
                                Layout.fillWidth: true
                                text: appController.assistantAttachment.name || appController.appText.assistant_attached_image_fallback
                                color: textPrimary
                                font.pixelSize: 13
                                font.bold: true
                                elide: Text.ElideMiddle
                            }
                            Text {
                                Layout.fillWidth: true
                                text: appController.assistantVisionAvailable
                                      ? appController.appText.assistant_vision_available_note
                                      : appController.assistantVisionDetail
                                color: appController.assistantVisionAvailable ? textSecondary : warning
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                        }
                        Button {
                            text: appController.appText.assistant_remove_button
                            enabled: !appController.assistantBusy
                            onClicked: appController.clearAssistantAttachment()
                        }
                    }
                }

                // With no provider the assistant used to accept the question and
                // answer "LLM_BASE_URL is not set." - an environment variable
                // name, in English, to someone who never chose to have one.
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: noAiContent.implicitHeight + 28
                    visible: appController.activeAiProviderKind === "NONE"
                    radius: radiusMd
                    color: panelRaised
                    border.color: warning
                    RowLayout {
                        id: noAiContent
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: 16
                        anchors.rightMargin: 16
                        spacing: 12
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text {
                                text: appController.appText.no_ai_provider_title
                                color: warning
                                font.pixelSize: 14
                                font.bold: true
                            }
                            Text {
                                Layout.fillWidth: true
                                text: appController.appText.no_ai_provider_assistant_detail
                                color: textSecondary
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                        }
                        Button {
                            text: appController.appText.no_ai_provider_setup_button
                            onClicked: appController.setCurrentPage(8)
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    Button {
                        text: appController.appText.assistant_attach_image_button
                        enabled: !appController.assistantBusy && appController.activeAiProviderKind !== "NONE"
                        onClicked: assistantImageDialog.open()
                    }
                    TextField {
                        id: assistantInput
                        Layout.fillWidth: true
                        placeholderText: appController.activeAiProviderKind === "NONE"
                            ? appController.appText.no_ai_provider_input_placeholder
                            : appController.appText.assistant_input_placeholder
                        enabled: !appController.assistantBusy && appController.activeAiProviderKind !== "NONE"
                        Keys.onPressed: function(event) {
                            if (event.key === Qt.Key_V && (event.modifiers & Qt.ControlModifier)) {
                                event.accepted = appController.pasteAssistantImageFromClipboard()
                            }
                        }
                        onAccepted: {
                            if ((text.trim().length > 0 || Object.keys(appController.assistantAttachment).length > 0)
                                    && (Object.keys(appController.assistantAttachment).length === 0 || appController.assistantVisionAvailable)) {
                                appController.askAssistant(text)
                                clear()
                            }
                        }
                    }
                    BusyDots { visible: appController.assistantBusy }
                    // Replaces Send while a question is running, so a slow answer
                    // can be abandoned and the question reworded.
                    Button {
                        visible: appController.assistantBusy
                        text: appController.appText.assistant_stop_button
                        onClicked: appController.cancelAssistant()
                    }
                    Button {
                        visible: !appController.assistantBusy
                        text: appController.appText.assistant_send_button
                        enabled: appController.activeAiProviderKind !== "NONE"
                                 && (assistantInput.text.trim().length > 0 || Object.keys(appController.assistantAttachment).length > 0)
                                 && (Object.keys(appController.assistantAttachment).length === 0 || appController.assistantVisionAvailable)
                        onClicked: {
                            appController.askAssistant(assistantInput.text)
                            assistantInput.clear()
                        }
                    }
                }
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: appController.currentPage === 7
            contentWidth: availableWidth
            contentHeight: helpGuidesPageContent.implicitHeight + 72
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                id: helpGuidesPageContent
                x: 28
                y: 28
                width: window.pageContentWidth()
                spacing: 18

                Text { text: appController.appText.help_guides_title; color: textPrimary; font.pixelSize: 26; font.bold: true }
                Text {
                    Layout.fillWidth: true
                    text: appController.appText.help_guides_subtitle
                    color: textSecondary
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 12
                    rowSpacing: 12
                    Repeater {
                        model: appController.guides
                        delegate: Rectangle {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 152
                            radius: radiusMd
                            color: panel
                            border.color: border
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 16
                                spacing: 8
                                RowLayout {
                                    Layout.fillWidth: true
                                    Text { Layout.fillWidth: true; text: modelData.title; color: textPrimary; font.pixelSize: 16; font.bold: true; elide: Text.ElideRight }
                                    StatusPill { label: modelData.section; tone: "neutral" }
                                }
                                Text {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    text: modelData.summary
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                                Button {
                                    text: appController.appText.open_guide_button
                                    onClicked: window.openGuide(modelData.id)
                                }
                            }
                        }
                    }
                }
                Item { Layout.fillWidth: true; Layout.preferredHeight: 44 }
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: appController.currentPage === 1
            contentWidth: availableWidth
            contentHeight: liveActionsPageContent.implicitHeight + 72
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            GridLayout {
                id: liveActionsPageContent
                x: 28
                y: 28
                width: window.pageContentWidth()
                columns: 1
                rowSpacing: 18
                Text { Layout.row: 0; text: appController.appText.live_actions_title; color: textPrimary; font.pixelSize: 26; font.bold: true }
                RowLayout {
                    Layout.row: 1
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: appController.appText.live_actions_subtitle
                        color: textSecondary
                        font.pixelSize: 13
                        wrapMode: Text.WordWrap
                    }
                    Button {
                        text: appController.appText.open_live_api_guide_button
                        onClicked: window.openGuide("binance-live-api")
                    }
                    Button {
                        text: appController.appText.refresh_checks_button
                        onClicked: appController.refreshSetup()
                    }
                }

                Rectangle {
                    objectName: "guardedCentrePanel"
                    Layout.row: 3
                    Layout.fillWidth: true
                    Layout.preferredHeight: 330
                    radius: radiusMd
                    color: panel
                    border.color: border
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 14
                        RowLayout {
                            Layout.fillWidth: true
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 5
                                Text { text: appController.appText.guarded_action_center_title; color: textPrimary; font.pixelSize: 16; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: appController.appText.guarded_action_center_description
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                            }
                            StatusPill {
                                Layout.alignment: Qt.AlignVCenter
                                label: appController.safetyStage
                                tone: appController.safetyAllowsLiveSubmit ? "success" : "warning"
                            }
                        }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: 3
                            columnSpacing: 22
                            rowSpacing: 14
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                Text { text: appController.appText.trade_preview_title; color: textPrimary; font.pixelSize: 14; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 54
                                    text: appController.appText.trade_preview_description
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8
                                    Button {
                                        text: appController.busy ? appController.appText.running_status : appController.appText.prepare_trade_preview_button
                                        enabled: !appController.busy
                                        onClicked: appController.prepareTradePreview()
                                    }
                                    BusyDots { Layout.alignment: Qt.AlignVCenter; visible: appController.busy }
                                    Item { Layout.fillWidth: true }
                                }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                Text { text: appController.appText.bot_plan_title; color: textPrimary; font.pixelSize: 14; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 54
                                    text: appController.appText.bot_plan_description
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8
                                    Button {
                                        text: appController.busy ? appController.appText.running_status : appController.appText.prepare_bot_plan_button
                                        enabled: !appController.busy
                                        onClicked: appController.prepareBotPlan()
                                    }
                                    BusyDots { Layout.alignment: Qt.AlignVCenter; visible: appController.busy }
                                    Item { Layout.fillWidth: true }
                                }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                Text { text: appController.appText.custom_analysis_title; color: textPrimary; font.pixelSize: 14; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 54
                                    text: appController.appText.custom_analysis_description
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                                Button {
                                    text: appController.appText.open_run_dialog_button
                                    enabled: !appController.busy
                                    onClicked: runDialog.open()
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.safetyAllowsLiveSubmit
                                ? appController.appText.guarded_submission_available_note
                                : appController.appText.guarded_submission_locked_note
                            color: warning
                            font.pixelSize: 12
                            font.bold: true
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                Rectangle {
                    Layout.row: 2
                    Layout.fillWidth: true
                    Layout.preferredHeight: safetyStageContent.implicitHeight + 36
                    radius: radiusMd
                    color: panel
                    border.color: appController.safetyAllowsLiveSubmit ? accent : border
                    ColumnLayout {
                        id: safetyStageContent
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 12
                        RowLayout {
                            Layout.fillWidth: true
                            Text { Layout.fillWidth: true; text: appController.appText.safety_stage_title; color: textPrimary; font.pixelSize: 16; font.bold: true }
                            Text { text: appController.safetyStage; color: appController.safetyAllowsLiveSubmit ? accent : warning; font.pixelSize: 12; font.bold: true }
                        }
                        Text { Layout.fillWidth: true; text: appController.safetyDetail; color: textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap }
                        Rectangle {
                            // The profile can lock submit even when the stage allows it,
                            // so say so here rather than leaving buttons quietly absent.
                            Layout.fillWidth: true
                            Layout.preferredHeight: automationLockText.implicitHeight + 20
                            visible: !appController.automationAllowsSubmit
                            radius: radiusSm
                            color: panelRaised
                            border.color: warning
                            Text {
                                id: automationLockText
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.leftMargin: 12
                                anchors.rightMargin: 12
                                text: appController.appText.automation_locks_submit
                                color: warning
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: liveApiSummaryContent.implicitHeight + 24
                            radius: radiusSm
                            color: panelRaised
                            border.color: appController.liveTradingCheckState === "Verified" ? accent : border
                            RowLayout {
                                id: liveApiSummaryContent
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 12
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Text { text: appController.appText.live_api_title; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                    Text {
                                        Layout.fillWidth: true
                                        text: (appController.liveTradingKeyStatus === "PASS" ? appController.appText.live_api_credentials_configured : appController.appText.live_api_credentials_not_configured)
                                            + "  |  " + (appController.liveTradingCheckState === "Verified" ? appController.appText.live_api_permissions_verified : appController.appText.live_api_permissions_not_verified)
                                        color: textSecondary
                                        font.pixelSize: 11
                                        wrapMode: Text.WordWrap
                                    }
                                }
                                StatusPill {
                                    Layout.alignment: Qt.AlignVCenter
                                    label: appController.liveTradingCheckState === "Verified" ? "VERIFIED" : appController.liveTradingKeyStatus === "PASS" ? "CONFIGURED" : "LOCKED"
                                    tone: appController.liveTradingCheckState === "Verified" ? "success" : "warning"
                                }
                                Button {
                                    text: appController.appText.manage_live_api_button
                                    onClicked: liveApiManagerDialog.open()
                                }
                                Button {
                                    text: appController.checkingLiveTrading ? appController.appText.verifying_status : appController.appText.verify_permissions_button
                                    enabled: appController.liveTradingKeyStatus === "PASS" && !appController.checkingLiveTrading
                                    onClicked: appController.checkBinanceLiveTrading()
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.safetyStageCode === "SETUP" && !appController.hasCompletedRealAnalysis
                                ? appController.appText.prerequisite_analysis
                                : (appController.safetyStageCode === "PREVIEW_ONLY" || appController.safetyStageCode === "ARMED") && appController.liveTradingKeyStatus !== "PASS"
                                    ? appController.appText.prerequisite_live_key
                                    : (appController.safetyStageCode === "PREVIEW_ONLY" || appController.safetyStageCode === "ARMED") && appController.liveTradingCheckState !== "Verified"
                                        ? appController.appText.prerequisite_verify_api
                                        : appController.appText.prerequisite_all_available
                            color: warning
                            font.pixelSize: 11
                            font.bold: true
                            wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                Layout.fillWidth: true
                                text: appController.appText.recommended_next_step_label
                                color: textSecondary
                                font.pixelSize: 11
                                font.bold: true
                            }
                            RowLayout {
                                spacing: 8
                                Button {
                                    // This starts the same long analysis as the
                                    // Guarded Action Center buttons, which do show
                                    // progress; greying out alone read as a freeze.
                                    text: appController.busy
                                        ? appController.appText.running_status
                                        : window.safetyNextActionLabel()
                                    highlighted: true
                                    enabled: !appController.busy && !appController.checkingLiveTrading
                                    onClicked: window.runSafetyNextAction()
                                }
                                BusyDots { Layout.alignment: Qt.AlignVCenter; visible: appController.busy }
                            }
                        }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: 3
                            columnSpacing: 12
                            Rectangle {
                                Layout.fillWidth: true; Layout.preferredHeight: 72; radius: radiusSm; color: panelRaised; border.color: appController.safetyAllowsLivePreview ? accent : border
                                Column {
                                    anchors.fill: parent; anchors.margins: 10; spacing: 4
                                    Text { text: appController.appText.safety_step1_title; color: textPrimary; font.bold: true }
                                    Text { width: parent.width; text: appController.appText.safety_step1_detail; color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true; Layout.preferredHeight: 72; radius: radiusSm; color: panelRaised; border.color: appController.safetyStageCode === "ARMED" || appController.safetyAllowsLiveSubmit ? accent : border
                                Column {
                                    anchors.fill: parent; anchors.margins: 10; spacing: 4
                                    Text { text: appController.appText.safety_step2_title; color: textPrimary; font.bold: true }
                                    Text { width: parent.width; text: appController.appText.safety_step2_detail; color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true; Layout.preferredHeight: 72; radius: radiusSm; color: panelRaised; border.color: appController.safetyAllowsLiveSubmit ? accent : border
                                Column {
                                    anchors.fill: parent; anchors.margins: 10; spacing: 4
                                    Text { text: appController.appText.safety_step3_title; color: textPrimary; font.bold: true }
                                    Text { width: parent.width; text: appController.appText.safety_step3_detail; color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap }
                                }
                            }
                        }
                        Flow {
                            Layout.fillWidth: true
                            spacing: 10
                            Button {
                                text: appController.appText.safety_enable_preview_button
                                enabled: appController.safetyStageCode === "SETUP" && appController.hasCompletedRealAnalysis
                                onClicked: window.openSafetyStageConfirmation("PREVIEW_ONLY", "Enable mainnet preview")
                            }
                            Button {
                                text: appController.appText.safety_arm_button
                                enabled: appController.safetyStageCode === "PREVIEW_ONLY"
                                    && appController.liveTradingCheckState === "Verified"
                                onClicked: window.openSafetyStageConfirmation("ARMED", "Arm guarded actions")
                            }
                            Button {
                                text: appController.appText.safety_enable_submit_button
                                enabled: appController.safetyStageCode === "ARMED" && appController.liveTradingCheckState === "Verified"
                                onClicked: window.openSafetyStageConfirmation("LIVE_ENABLED", "Enable guarded live submit")
                            }
                            Button {
                                text: appController.appText.safety_lock_button
                                enabled: appController.safetyStageCode === "ARMED" || appController.safetyAllowsLiveSubmit
                                onClicked: appController.lockLiveSubmit()
                            }
                        }
                        Text { Layout.fillWidth: true; text: appController.appText.safety_stage_disclaimer; color: warning; font.pixelSize: 11; font.bold: true; wrapMode: Text.WordWrap }
                    }
                }
                // Funding, not sizing: how much of the user's savings the app
                // may reach for to pay for an approved action. Kept as its own
                // card because merging it with the sizing panel above is the
                // same confusion that had an Earn limit capping trade size.
                Rectangle {
                    objectName: "earnFundingPanel"
                    Layout.row: 7
                    Layout.fillWidth: true
                    // Fixed, like every card on this page; measured rather than
                    // guessed, see the panel above.
                    Layout.preferredHeight: 500
                    radius: radiusMd
                    color: panel
                    border.color: border
                    ColumnLayout {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        Text {
                            text: appController.appText.earn_funding_title
                            color: textPrimary
                            font.pixelSize: 16
                            font.bold: true
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.appText.earn_funding_description
                            color: textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: 3
                            columnSpacing: 10
                            rowSpacing: 6

                            Text {
                                text: appController.appText.earn_funding_run_pct_label
                                color: textSecondary; font.pixelSize: 12
                                Layout.preferredWidth: 230
                                Layout.maximumWidth: 230
                                wrapMode: Text.WordWrap
                            }
                            TextField { id: runPctInput; Layout.preferredWidth: 90; text: appController.earnFunding.runPct }
                            Text {
                                Layout.fillWidth: true
                                text: appController.appText.earn_funding_run_pct_help
                                color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap
                            }

                            Text {
                                text: appController.appText.earn_funding_run_amount_label
                                color: textSecondary; font.pixelSize: 12
                                Layout.preferredWidth: 230
                                Layout.maximumWidth: 230
                                wrapMode: Text.WordWrap
                            }
                            TextField { id: runAmountInput; Layout.preferredWidth: 90; text: appController.earnFunding.runAmount }
                            Text {
                                Layout.fillWidth: true
                                text: appController.appText.earn_funding_run_amount_help
                                color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap
                            }

                            Text {
                                text: appController.appText.earn_funding_day_pct_label
                                color: textSecondary; font.pixelSize: 12
                                Layout.preferredWidth: 230
                                Layout.maximumWidth: 230
                                wrapMode: Text.WordWrap
                            }
                            TextField { id: dayPctInput; Layout.preferredWidth: 90; text: appController.earnFunding.dayPct }
                            Text {
                                Layout.fillWidth: true
                                text: appController.appText.earn_funding_day_pct_help
                                color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap
                            }

                            Text {
                                text: appController.appText.earn_funding_day_amount_label
                                color: textSecondary; font.pixelSize: 12
                                Layout.preferredWidth: 230
                                Layout.maximumWidth: 230
                                wrapMode: Text.WordWrap
                            }
                            TextField { id: dayAmountInput; Layout.preferredWidth: 90; text: appController.earnFunding.dayAmount }
                            Text {
                                Layout.fillWidth: true
                                text: appController.appText.earn_funding_day_amount_help
                                color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap
                            }

                            Text {
                                text: appController.appText.earn_funding_reserve_label
                                color: textSecondary; font.pixelSize: 12
                                Layout.preferredWidth: 230
                                Layout.maximumWidth: 230
                                wrapMode: Text.WordWrap
                            }
                            TextField { id: reserveInput; Layout.preferredWidth: 90; text: appController.earnFunding.reserve }
                            Text {
                                Layout.fillWidth: true
                                text: appController.appText.earn_funding_reserve_help
                                color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Button {
                                text: appController.appText.earn_funding_save_button
                                onClicked: appController.saveEarnFunding({
                                    "runPct": runPctInput.text,
                                    "runAmount": runAmountInput.text,
                                    "dayPct": dayPctInput.text,
                                    "dayAmount": dayAmountInput.text,
                                    "reserve": reserveInput.text
                                })
                            }
                            Item { Layout.fillWidth: true }
                        }
                    }
                }
                // Bottom spacer, so it has to stay the last row on the page.
                Item { Layout.row: 8; Layout.fillWidth: true; Layout.preferredHeight: 44 }
                // The cap used to be reachable only by opening config.toml, which
                // is the one thing this app promises nobody has to do.
                Rectangle {
                    objectName: "orderCapsPanel"
                    Layout.row: 5
                    Layout.fillWidth: true
                    // Fixed, like every other card on this page. Deriving the
                    // height from a child that is anchored to this Rectangle
                    // is circular inside a GridLayout: it resolved to zero, the
                    // panel collapsed, and its anchored contents drew at 0,0 -
                    // on top of the page title. It works on the ColumnLayout
                    // pages, which is why it survived the move unnoticed.
                    Layout.preferredHeight: 210
                    radius: radiusMd
                    color: panel
                    border.color: appController.orderCaps.aboveSuggestion ? warning : border
                    ColumnLayout {
                        id: orderCapsContent
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        Text {
                            text: appController.appText.order_caps_title
                            color: textPrimary
                            font.pixelSize: 16
                            font.bold: true
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.appText.order_caps_description
                            color: textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Text {
                                text: appController.appText.order_caps_testnet_label
                                color: textSecondary
                                font.pixelSize: 12
                            }
                            TextField {
                                id: testnetCapInput
                                Layout.preferredWidth: 110
                                text: appController.orderCaps.testnet
                            }
                            Item { Layout.preferredWidth: 12 }
                            Text {
                                text: appController.appText.order_caps_mainnet_label
                                color: textSecondary
                                font.pixelSize: 12
                            }
                            TextField {
                                id: mainnetCapInput
                                Layout.preferredWidth: 110
                                text: appController.orderCaps.mainnet
                            }
                            Button {
                                text: appController.appText.order_caps_save_button
                                onClicked: appController.saveOrderCaps(testnetCapInput.text, mainnetCapInput.text)
                            }
                            Item { Layout.fillWidth: true }
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: appController.orderCaps.hasPortfolio
                            text: appController.appText.order_caps_suggestion_template
                                .replace("{suggested}", appController.orderCaps.suggested)
                            color: appController.orderCaps.aboveSuggestion ? warning : textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                    }
                }
                // One layer earlier than the cap above: what size the analysis
                // considers appropriate, rather than what may reach the
                // exchange. Three of these were readable only in config.toml
                // and, until the sizing change, did nothing at all.
                Rectangle {
                    objectName: "tradeSizingPanel"
                    Layout.row: 6
                    Layout.fillWidth: true
                    // Fixed for the same reason as the panel above: a height
                    // derived from anchored children is circular in a
                    // GridLayout and collapses the card to zero.
                    //
                    // 500 rather than a guess: the content measures 462 at its
                    // tallest, which is English at the window's minimum width
                    // (Czech wraps to 451), plus the 16px margin at each end.
                    Layout.preferredHeight: 500
                    radius: radiusMd
                    color: panel
                    border.color: border
                    ColumnLayout {
                        id: tradeSizingContent
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        Text {
                            text: appController.appText.trade_sizing_title
                            color: textPrimary
                            font.pixelSize: 16
                            font.bold: true
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.appText.trade_sizing_description
                            color: textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: 3
                            columnSpacing: 10
                            rowSpacing: 6

                            Text {
                                text: appController.appText.trade_sizing_trade_pct_label
                                color: textSecondary; font.pixelSize: 12
                                // Wraps rather than overflowing: a label wider
                                // than its column drew straight over the input
                                // beside it, and label lengths change with both
                                // the language and the user's font.
                                Layout.preferredWidth: 230
                                Layout.maximumWidth: 230
                                wrapMode: Text.WordWrap
                            }
                            TextField { id: tradePctInput; Layout.preferredWidth: 90; text: appController.tradeSizing.tradePct }
                            Text {
                                Layout.fillWidth: true
                                text: appController.appText.trade_sizing_trade_pct_help
                                color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap
                            }

                            Text {
                                text: appController.appText.trade_sizing_trade_amount_label
                                color: textSecondary; font.pixelSize: 12
                                // Wraps rather than overflowing: a label wider
                                // than its column drew straight over the input
                                // beside it, and label lengths change with both
                                // the language and the user's font.
                                Layout.preferredWidth: 230
                                Layout.maximumWidth: 230
                                wrapMode: Text.WordWrap
                            }
                            TextField { id: tradeAmountInput; Layout.preferredWidth: 90; text: appController.tradeSizing.tradeAmount }
                            Text {
                                Layout.fillWidth: true
                                text: appController.appText.trade_sizing_trade_amount_help
                                color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap
                            }

                            Text {
                                text: appController.appText.trade_sizing_position_pct_label
                                color: textSecondary; font.pixelSize: 12
                                // Wraps rather than overflowing: a label wider
                                // than its column drew straight over the input
                                // beside it, and label lengths change with both
                                // the language and the user's font.
                                Layout.preferredWidth: 230
                                Layout.maximumWidth: 230
                                wrapMode: Text.WordWrap
                            }
                            TextField { id: positionPctInput; Layout.preferredWidth: 90; text: appController.tradeSizing.positionPct }
                            Text {
                                Layout.fillWidth: true
                                text: appController.appText.trade_sizing_position_pct_help
                                color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap
                            }

                            Text {
                                text: appController.appText.trade_sizing_capital_pct_label
                                color: textSecondary; font.pixelSize: 12
                                // Wraps rather than overflowing: a label wider
                                // than its column drew straight over the input
                                // beside it, and label lengths change with both
                                // the language and the user's font.
                                Layout.preferredWidth: 230
                                Layout.maximumWidth: 230
                                wrapMode: Text.WordWrap
                            }
                            TextField { id: capitalPctInput; Layout.preferredWidth: 90; text: appController.tradeSizing.capitalPct }
                            Text {
                                Layout.fillWidth: true
                                text: appController.appText.trade_sizing_capital_pct_help
                                color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap
                            }

                            Text {
                                text: appController.appText.trade_sizing_risk_pct_label
                                color: textSecondary; font.pixelSize: 12
                                // Wraps rather than overflowing: a label wider
                                // than its column drew straight over the input
                                // beside it, and label lengths change with both
                                // the language and the user's font.
                                Layout.preferredWidth: 230
                                Layout.maximumWidth: 230
                                wrapMode: Text.WordWrap
                            }
                            TextField { id: riskPctInput; Layout.preferredWidth: 90; text: appController.tradeSizing.riskPct }
                            Text {
                                Layout.fillWidth: true
                                text: appController.appText.trade_sizing_risk_pct_help
                                color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Button {
                                text: appController.appText.trade_sizing_save_button
                                onClicked: appController.saveTradeSizing({
                                    "tradePct": tradePctInput.text,
                                    "tradeAmount": tradeAmountInput.text,
                                    "positionPct": positionPctInput.text,
                                    "capitalPct": capitalPctInput.text,
                                    "riskPct": riskPctInput.text
                                })
                            }
                            Item { Layout.fillWidth: true }
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: appController.tradeSizing.lastBoundBy !== ""
                            text: appController.tradeSizing.lastBoundBy
                            color: textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }
        }


        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: appController.currentPage === 9
            contentWidth: availableWidth
            contentHeight: listingsPageContent.implicitHeight + 72
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                id: listingsPageContent
                x: 28
                y: 28
                width: window.pageContentWidth()
                spacing: 18

                Text { text: appController.appText.listings_title; color: textPrimary; font.pixelSize: 26; font.bold: true }
                Text {
                    Layout.fillWidth: true
                    text: appController.appText.listings_subtitle
                    color: textSecondary
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                }

                // Says plainly what this is not, on the screen where someone
                // would otherwise assume it is a trading signal.
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: listingsWarning.implicitHeight + 28
                    radius: radiusMd
                    color: warningSoft
                    border.color: warning
                    Text {
                        id: listingsWarning
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: 16
                        anchors.rightMargin: 16
                        text: appController.appText.listings_not_a_signal
                        color: warning
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: listingsControls.implicitHeight + 32
                    radius: radiusMd
                    color: panel
                    border.color: appController.automation.watchListings ? accent : border
                    ColumnLayout {
                        id: listingsControls
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            CheckBox {
                                id: listingWatchEnabled
                                text: appController.appText.listings_watch_checkbox
                                checked: appController.automation.watchListings
                            }
                            Text { text: appController.appText.listings_interval_label; color: textSecondary; font.pixelSize: 12 }
                            SpinBox {
                                id: listingWatchInterval
                                from: appController.automation.minListingMinutes
                                to: appController.automation.maxListingMinutes
                                value: appController.automation.listingIntervalMinutes
                                editable: true
                            }
                            Button {
                                text: appController.appText.listings_save_button
                                onClicked: appController.saveListingWatch(
                                    listingWatchEnabled.checked, String(listingWatchInterval.value))
                            }
                            Button {
                                text: appController.appText.listings_check_now_button
                                enabled: appController.automation.watchListings && !appController.listingScanBusy
                                onClicked: appController.scanListings()
                            }
                            // A scan finishes in about a second, which is long
                            // enough to wonder whether the click registered.
                            BusyDots { visible: appController.listingScanBusy }
                            Item { Layout.fillWidth: true }
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: appController.listingStatus.length > 0
                            text: appController.listingStatus
                            color: textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    visible: appController.listings.length === 0
                    text: appController.appText.listings_empty
                    color: textSecondary
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                }

                Repeater {
                    model: appController.listings
                    delegate: Rectangle {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.preferredHeight: 62
                        radius: radiusSm
                        color: panelRaised
                        border.color: modelData.acknowledged ? accent : border
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 14
                            anchors.rightMargin: 14
                            spacing: 12
                            ColumnLayout {
                                Layout.preferredWidth: 190
                                spacing: 2
                                CopyableValue { value: modelData.symbol; font.pixelSize: 14; font.bold: true }
                                Text {
                                    text: modelData.baseAsset + " / " + modelData.quoteAsset
                                    color: textSecondary
                                    font.pixelSize: 10
                                }
                            }
                            ElidedDetail {
                                Layout.fillWidth: true
                                text: appController.appText.listings_first_seen_template
                                    .replace("{when}", modelData.firstSeenAt)
                                font.pixelSize: 11
                            }
                            Button {
                                text: modelData.acknowledged
                                    ? appController.appText.listings_allowed_button
                                    : appController.appText.listings_allow_button
                                enabled: !modelData.acknowledged
                                onClicked: appController.addAllowedSymbol(modelData.symbol)
                            }
                        }
                    }
                }
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: appController.currentPage === 10
            contentWidth: availableWidth
            contentHeight: automationPageContent.implicitHeight + 72
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                id: automationPageContent
                x: 28
                y: 28
                width: window.pageContentWidth()
                spacing: 18

                Text { text: appController.appText.automation_page_title; color: textPrimary; font.pixelSize: 26; font.bold: true }
                Text {
                    Layout.fillWidth: true
                    text: appController.appText.automation_page_subtitle
                    color: textSecondary
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: automationContent.implicitHeight + 32
                    radius: radiusMd
                    color: panel
                    border.color: appController.automation.enabled ? accent : border
                    ColumnLayout {
                        id: automationContent
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        Text {
                            text: appController.appText.automation_title
                            color: textPrimary
                            font.pixelSize: 16
                            font.bold: true
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.appText.automation_description
                            color: textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        CheckBox {
                            id: automationEnabled
                            text: appController.appText.automation_enable_checkbox
                            checked: appController.automation.enabled
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Text {
                                text: appController.appText.automation_interval_label
                                color: textSecondary
                                font.pixelSize: 12
                            }
                            SpinBox {
                                id: automationInterval
                                from: appController.automation.minHours
                                to: appController.automation.maxHours
                                value: appController.automation.intervalHours
                                editable: true
                            }
                            CheckBox {
                                id: automationAi
                                text: appController.appText.automation_ai_checkbox
                                // Same rule as the run dialog: without a model
                                // there is nothing to ask.
                                enabled: appController.activeAiProviderKind !== "NONE"
                                checked: appController.automation.aiSummary
                                        && appController.activeAiProviderKind !== "NONE"
                            }
                            CheckBox {
                                id: automationPreview
                                text: appController.appText.automation_preview_checkbox
                                enabled: appController.safetyAllowsLivePreview
                                checked: appController.automation.livePreview
                                        && appController.safetyAllowsLivePreview
                            }
                            Button {
                                text: appController.appText.automation_save_button
                                onClicked: appController.saveAutomation(
                                    automationEnabled.checked,
                                    String(automationInterval.value),
                                    automationAi.checked,
                                    automationPreview.checked
                                )
                            }
                            Item { Layout.fillWidth: true }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.appText.automation_tray_note
                            color: appController.automation.enabled ? accent : textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: taskContent.implicitHeight + 32
                    visible: appController.scheduledTask.supported
                    radius: radiusMd
                    color: panel
                    border.color: appController.scheduledTask.registered ? accent : border
                    ColumnLayout {
                        id: taskContent
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        Text {
                            text: appController.appText.task_title
                            color: textPrimary
                            font.pixelSize: 16
                            font.bold: true
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.appText.task_description
                            color: textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Text { text: appController.appText.task_time_label; color: textSecondary; font.pixelSize: 12 }
                            TextField {
                                id: taskTime
                                Layout.preferredWidth: 90
                                text: appController.scheduledTask.time
                                placeholderText: "07:30"
                            }
                            Button {
                                text: appController.appText.task_register_button
                                onClicked: appController.registerScheduledTask(taskTime.text)
                            }
                            Button {
                                text: appController.appText.task_remove_button
                                enabled: appController.scheduledTask.registered
                                onClicked: appController.removeScheduledTask()
                            }
                            Item { Layout.fillWidth: true }
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: !appController.scheduledTask.registered
                            text: appController.appText.task_state_absent
                            color: textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        // The registered task, shown here rather than left to a
                        // terminal: someone should be able to see what they
                        // scheduled without leaving the app that scheduled it.
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 56
                            visible: appController.scheduledTask.registered
                            radius: radiusSm
                            color: panelRaised
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 14
                                anchors.rightMargin: 14
                                spacing: 16
                                ColumnLayout {
                                    Layout.preferredWidth: 230
                                    spacing: 2
                                    Text {
                                        text: appController.appText.task_state_registered
                                        color: accent
                                        font.pixelSize: 12
                                        font.bold: true
                                    }
                                    Text {
                                        text: appController.appText.task_catch_up_note
                                        color: textSecondary
                                        font.pixelSize: 10
                                        elide: Text.ElideRight
                                    }
                                }
                                ColumnLayout {
                                    spacing: 2
                                    Text { text: appController.appText.task_next_run_label; color: textSecondary; font.pixelSize: 10 }
                                    Text { text: appController.scheduledTask.nextRun || "-"; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                }
                                ColumnLayout {
                                    spacing: 2
                                    Text { text: appController.appText.task_status_label; color: textSecondary; font.pixelSize: 10 }
                                    Text { text: appController.scheduledTask.status || "-"; color: textPrimary; font.pixelSize: 12 }
                                }
                                Item { Layout.fillWidth: true }
                            }
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    visible: !appController.schedules.some(function (item) { return item.active })
                    text: appController.appText.automation_page_empty
                    color: textSecondary
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                }

                Repeater {
                    model: appController.schedules
                    delegate: Rectangle {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.preferredHeight: 74
                        radius: radiusSm
                        color: panelRaised
                        border.color: modelData.active ? accent : border
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 14
                            anchors.rightMargin: 14
                            spacing: 16
                            Rectangle {
                                Layout.preferredWidth: 10
                                Layout.preferredHeight: 10
                                radius: 5
                                color: modelData.active ? accent : border
                            }
                            ColumnLayout {
                                Layout.preferredWidth: 250
                                spacing: 2
                                Text { text: modelData.name; color: textPrimary; font.pixelSize: 14; font.bold: true }
                                ElidedDetail { Layout.fillWidth: true; text: modelData.detail; font.pixelSize: 10 }
                            }
                            ColumnLayout {
                                Layout.preferredWidth: 150
                                spacing: 2
                                Text { text: appController.appText.automation_next_run; color: textSecondary; font.pixelSize: 10 }
                                Text {
                                    text: modelData.active
                                        ? (modelData.nextRun || modelData.cadence)
                                        : appController.appText.automation_inactive
                                    color: modelData.active ? accent : textSecondary
                                    font.pixelSize: 13
                                    font.bold: true
                                }
                            }
                            Text {
                                Layout.fillWidth: true
                                text: modelData.active ? modelData.cadence : ""
                                color: textSecondary
                                font.pixelSize: 11
                            }
                            Button {
                                // Only for a schedule configured elsewhere; the
                                // other two have their panels directly above.
                                visible: modelData.page !== appController.currentPage
                                text: appController.appText.automation_configure
                                onClicked: appController.setCurrentPage(modelData.page)
                            }
                        }
                    }
                }
            }
        }
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: appController.currentPage === 8
            contentWidth: availableWidth
            contentHeight: settingsPageContent.implicitHeight + 72
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                id: settingsPageContent
                x: 28
                y: 28
                width: window.pageContentWidth()
                spacing: 18
                Text { text: appController.appText.settings_title; color: textPrimary; font.pixelSize: 26; font.bold: true }
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: appController.appText.settings_subtitle
                        color: textSecondary
                        font.pixelSize: 13
                        elide: Text.ElideRight
                    }
                    Button {
                        text: appController.appText.setup_wizard_button
                        onClicked: appController.openOnboardingWizard()
                    }
                    Button {
                        text: appController.appText.replay_app_tour_button
                        onClicked: appController.startAppTour()
                    }
                    Button {
                        text: appController.appText.refresh_checks_button
                        onClicked: appController.refreshSetup()
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Text { text: appController.appText.language_toggle_label; color: textSecondary; font.pixelSize: 12 }
                    Button {
                        text: "English"
                        flat: appController.wizardLanguage !== "en"
                        highlighted: appController.wizardLanguage === "en"
                        onClicked: appController.setWizardLanguage("en")
                    }
                    Button {
                        text: "Čeština"
                        flat: appController.wizardLanguage !== "cs"
                        highlighted: appController.wizardLanguage === "cs"
                        onClicked: appController.setWizardLanguage("cs")
                    }
                    Item { Layout.fillWidth: true }
                }




                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 104
                    radius: radiusMd
                    color: panel
                    border.color: border
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 16
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            Text { text: appController.appText.binance_readonly_connection_title; color: textPrimary; font.pixelSize: 16; font.bold: true }
                            Text {
                                Layout.fillWidth: true
                                text: appController.binanceConnectionDetail
                                color: textSecondary
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                            }
                        }
                        StatusPill {
                            Layout.alignment: Qt.AlignVCenter
                            label: appController.binanceConnectionStatus
                            tone: appController.binanceConnectionState === "Connected" ? "success"
                                : appController.binanceConnectionState === "Checking" ? "warning"
                                : appController.binanceConnectionState === "Blocked" ? "danger" : "neutral"
                        }
                        Button {
                            text: appController.checkingConnection ? appController.appText.settings_checking_status : appController.appText.check_readonly_access_button
                            enabled: !appController.checkingConnection
                            onClicked: appController.checkBinanceReadOnly()
                        }
                    }
                }


                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 330
                    radius: radiusMd
                    color: panel
                    border.color: border
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 12
                        RowLayout {
                            Layout.fillWidth: true
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 5
                                Text { text: appController.appText.settings_ai_provider_title; color: textPrimary; font.pixelSize: 16; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: appController.aiProviderSummary
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                            }
                            StatusPill {
                                Layout.alignment: Qt.AlignVCenter
                                label: appController.aiProviderHealthStatus
                                tone: appController.aiProviderHealthState === "Connected" ? "success"
                                    : appController.aiProviderHealthState === "Checking" ? "warning"
                                    : appController.aiProviderHealthState === "Blocked" ? "danger" : "neutral"
                            }
                            Button {
                                text: appController.checkingAiProvider ? appController.appText.settings_checking_status : appController.appText.settings_check_ai_provider_button
                                enabled: !appController.checkingAiProvider
                                onClicked: appController.checkAiProvider()
                            }
                            Button {
                                text: appController.appText.configure_ai_models_button
                                onClicked: {
                                    window.wizardStep = 3
                                    appController.openOnboardingWizard()
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.aiProviderHealthDetail
                            color: textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12
                            ListView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                interactive: false
                                spacing: 6
                                model: appController.aiProviderChecks
                                delegate: Rectangle {
                                    required property var modelData
                                    width: ListView.view.width
                                    height: 38
                                    radius: 5
                                    color: panelRaised
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 12
                                        anchors.rightMargin: 12
                                        spacing: 10
                                        Rectangle {
                                            Layout.preferredWidth: 7
                                            Layout.preferredHeight: 7
                                            radius: 4
                                            color: modelData.status === "PASS" ? accent
                                                : modelData.status === "WARN" ? warning : "#ee6b6e"
                                        }
                                        Text { Layout.preferredWidth: 92; text: modelData.name; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                        Text { Layout.preferredWidth: 60; text: modelData.group; color: textSecondary; font.pixelSize: 10 }
                                        ElidedDetail { Layout.fillWidth: true; text: modelData.detail; font.pixelSize: 10 }
                                    }
                                }
                            }
                            ListView {
                                Layout.preferredWidth: 370
                                Layout.fillHeight: true
                                interactive: false
                                spacing: 6
                                model: appController.aiContextSections
                                delegate: Rectangle {
                                    required property var modelData
                                    width: ListView.view.width
                                    height: 48
                                    radius: 5
                                    color: "#141a21"
                                    border.color: border
                                    Column {
                                        anchors.fill: parent
                                        anchors.margins: 10
                                        spacing: 3
                                        Text { text: modelData.name; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                        ElidedDetail { width: parent.width; text: modelData.detail; font.pixelSize: 10 }
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 285
                    radius: radiusMd
                    color: panel
                    border.color: border
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 12
                        RowLayout {
                            Layout.fillWidth: true
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4
                                Text { text: appController.appText.onboarding_profile_title; color: textPrimary; font.pixelSize: 16; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: appController.userProfileSummary
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                            }
                            Button {
                                text: appController.appText.open_wizard_button
                                onClicked: appController.openOnboardingWizard()
                            }
                            Button {
                                text: appController.appText.use_safe_defaults_button
                                onClicked: appController.useSafeDefaultProfile()
                            }
                        }
                        ListView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            interactive: true
                            clip: true
                            spacing: 6
                            model: appController.userProfileFields
                            delegate: Rectangle {
                                required property var modelData
                                width: ListView.view.width
                                height: 36
                                radius: 5
                                color: panelRaised
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 12
                                    anchors.rightMargin: 12
                                    spacing: 12
                                    Text { Layout.preferredWidth: 120; text: modelData.name; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                    Text { Layout.preferredWidth: 150; text: modelData.value; color: accent; font.pixelSize: 11; font.bold: true; elide: Text.ElideRight }
                                    ElidedDetail { Layout.fillWidth: true; text: modelData.detail; font.pixelSize: 10 }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 335
                    radius: radiusMd
                    color: panel
                    border.color: border
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 12
                        RowLayout {
                            Layout.fillWidth: true
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4
                                Text { text: appController.appText.privacy_data_title; color: textPrimary; font.pixelSize: 16; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: appController.appText.privacy_data_description
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                            }
                            Flow {
                                Layout.preferredWidth: implicitWidth
                                spacing: 8
                                Button {
                                    text: appController.appText.export_diagnostics_button
                                    onClicked: appController.exportDiagnosticsBundle()
                                }
                                Button {
                                    text: appController.appText.reset_onboarding_button
                                    enabled: appController.userProfileConfigured
                                    onClicked: deleteProfileDialog.open()
                                }
                                Button {
                                    text: appController.appText.delete_local_data_button
                                    onClicked: localDataResetDialog.open()
                                }
                            }
                        }
                        ListView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            interactive: false
                            spacing: 6
                            model: appController.privacyDataItems
                            delegate: Rectangle {
                                required property var modelData
                                width: ListView.view.width
                                height: 44
                                radius: 5
                                color: panelRaised
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 12
                                    anchors.rightMargin: 12
                                    spacing: 12
                                    Text { Layout.preferredWidth: 150; text: modelData.name; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                    Text { Layout.preferredWidth: 125; text: modelData.value; color: accent; font.pixelSize: 11; font.bold: true; elide: Text.ElideRight }
                                    ElidedDetail { Layout.fillWidth: true; text: modelData.detail; font.pixelSize: 10 }
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.appText.privacy_data_note
                            color: textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text { text: appController.appText.system_readiness_title; color: textPrimary; font.pixelSize: 16; font.bold: true }
                    Item { Layout.fillWidth: true }
                    Text { text: appController.setupSummary; color: textSecondary; font.pixelSize: 12 }
                }

                ListView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: contentHeight
                    interactive: false
                    spacing: 6
                    model: appController.setupChecks
                    delegate: Rectangle {
                        required property var modelData
                        width: ListView.view.width
                        height: 54
                        radius: 6
                        color: panel
                        border.color: border
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 14
                            anchors.rightMargin: 14
                            spacing: 12
                            Rectangle {
                                Layout.preferredWidth: 8
                                Layout.preferredHeight: 8
                                radius: 4
                                color: modelData.status === "PASS" ? accent
                                    : modelData.status === "WARN" ? warning : "#ee6b6e"
                            }
                            Text { Layout.preferredWidth: 155; text: modelData.name; color: textPrimary; font.pixelSize: 12; font.bold: true }
                            Text { Layout.preferredWidth: 70; text: modelData.group; color: textSecondary; font.pixelSize: 10 }
                            ElidedDetail { Layout.fillWidth: true; text: modelData.detail; font.pixelSize: 11 }
                            Text {
                                Layout.preferredWidth: 55
                                text: modelData.status
                                color: modelData.status === "PASS" ? accent
                                    : modelData.status === "WARN" ? warning : "#ee6b6e"
                                font.pixelSize: 10
                                font.bold: true
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 132
                    radius: radiusMd
                    color: panel
                    border.color: border
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 9
                        Text { text: appController.appText.safety_baseline_title; color: textPrimary; font.pixelSize: 16; font.bold: true }
                        Text { text: appController.appText.safety_baseline_secrets_note; color: textSecondary; font.pixelSize: 12 }
                        Text { text: appController.appText.safety_baseline_path_note; color: textSecondary; font.pixelSize: 12 }
                        Text { text: appController.appText.safety_baseline_live_note; color: textSecondary; font.pixelSize: 12 }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 190
                    radius: radiusMd
                    color: panel
                    border.color: border
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 10
                        RowLayout {
                            Layout.fillWidth: true
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4
                                Text { text: appController.appText.safety_stage_title; color: textPrimary; font.pixelSize: 16; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: appController.safetyDetail
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                            }
                            Rectangle {
                                Layout.preferredWidth: 130
                                Layout.preferredHeight: 30
                                radius: 5
                                color: "transparent"
                                border.color: "transparent"
                                Text {
                                    anchors.centerIn: parent
                                    text: appController.appText.safety_stage_prefix + " " + appController.safetyStage
                                    color: appController.safetyAllowsLiveSubmit ? accent
                                        : appController.safetyAllowsLivePreview ? warning : accent
                                    font.pixelSize: 11
                                    font.bold: true
                                }
                            }
                        }
                        ListView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            interactive: false
                            spacing: 6
                            model: appController.safetyChecks
                            delegate: Rectangle {
                                required property var modelData
                                width: ListView.view.width
                                height: 34
                                radius: 5
                                color: panelRaised
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 12
                                    anchors.rightMargin: 12
                                    spacing: 12
                                    Text { Layout.preferredWidth: 120; text: modelData.name; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                    Text { Layout.preferredWidth: 100; text: modelData.status; color: modelData.status === "LOCKED" ? warning : accent; font.pixelSize: 11; font.bold: true }
                                    ElidedDetail { Layout.fillWidth: true; text: modelData.detail; font.pixelSize: 10 }
                                }
                            }
                        }
                    }
                }
                Item { Layout.fillWidth: true; Layout.preferredHeight: 44 }
            }
        }
    }

    Dialog {
        id: strategyRegistrationDialog
        property string importNotice: ""
        title: appController.appText.register_bot_dialog_title
        modal: true
        anchors.centerIn: parent
        width: Math.min(window.width - 56, 920)
        height: Math.min(window.height - 56, 780)
        closePolicy: Popup.CloseOnEscape
        onOpened: {
            gridVerified.checked = false
            rebalancingVerified.checked = false
            importNotice = ""
        }

        contentItem: ScrollView {
            id: strategyRegistrationScroll
            clip: true
            contentWidth: availableWidth
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            rightPadding: 18

            ColumnLayout {
                width: strategyRegistrationScroll.availableWidth - strategyRegistrationScroll.rightPadding
                spacing: 14

                Text {
                    Layout.fillWidth: true
                    text: appController.appText.register_bot_warning
                    color: warning
                    font.pixelSize: 12
                    font.bold: true
                    wrapMode: Text.WordWrap
                }
                Text {
                    Layout.fillWidth: true
                    visible: strategyRegistrationDialog.importNotice.length > 0
                    text: strategyRegistrationDialog.importNotice
                    color: accent
                    font.pixelSize: 12
                    font.bold: true
                    wrapMode: Text.WordWrap
                }

                TabBar {
                    id: strategyRegistrationTabs
                    Layout.fillWidth: true
                    TabButton { text: appController.appText.tab_spot_grid }
                    TabButton { text: appController.appText.tab_rebalancing }
                }

                StackLayout {
                    Layout.fillWidth: true
                    currentIndex: strategyRegistrationTabs.currentIndex

                    ColumnLayout {
                        spacing: 14
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                Layout.fillWidth: true
                                text: appController.appText.grid_tab_description
                                color: textSecondary
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                            }
                            Button {
                                text: appController.appText.import_latest_recommendation_button
                                enabled: Boolean(appController.latestGridRegistrationSuggestion.available)
                                onClicked: {
                                    var suggestion = appController.latestGridRegistrationSuggestion
                                    gridName.text = suggestion.name || ""
                                    var symbolIndex = gridSymbol.find(suggestion.symbol || "")
                                    if (symbolIndex >= 0) gridSymbol.currentIndex = symbolIndex
                                    var typeIndex = gridType.find(suggestion.gridType || "ARITHMETIC")
                                    if (typeIndex >= 0) gridType.currentIndex = typeIndex
                                    gridRangeLow.text = suggestion.rangeLow || ""
                                    gridRangeHigh.text = suggestion.rangeHigh || ""
                                    gridCount.text = suggestion.gridCount || ""
                                    gridInvestment.text = suggestion.investment || ""
                                    gridEntryPrice.text = suggestion.entryPrice || ""
                                    gridStopLoss.text = suggestion.stopLoss || ""
                                    gridTakeProfit.text = suggestion.takeProfit || ""
                                    gridVerified.checked = false
                                    strategyRegistrationDialog.importNotice = appController.appText.grid_import_notice_template.replace("{run}", suggestion.sourceRun)
                                }
                            }
                        }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: width >= 700 ? 2 : 1
                            columnSpacing: 14
                            rowSpacing: 12

                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_local_name; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridName; Layout.fillWidth: true; placeholderText: "Example: BTC range bot" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_binance_bot_id; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridBotId; Layout.fillWidth: true; placeholderText: "Optional, but recommended" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_symbol; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                ComboBox { id: gridSymbol; Layout.fillWidth: true; model: appController.gridRegistrationSymbols }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_grid_spacing; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                ComboBox { id: gridType; Layout.fillWidth: true; model: ["ARITHMETIC", "GEOMETRIC"] }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_lower_price; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridRangeLow; Layout.fillWidth: true; placeholderText: "Lower range shown in Binance" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_upper_price; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridRangeHigh; Layout.fillWidth: true; placeholderText: "Upper range shown in Binance" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_number_of_grids; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridCount; Layout.fillWidth: true; placeholderText: "Example: 10" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_investment_usdc; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridInvestment; Layout.fillWidth: true; placeholderText: "Exact allocated amount" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_entry_price; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridEntryPrice; Layout.fillWidth: true; placeholderText: "Price when the bot was created" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_created_at; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridCreatedAt; Layout.fillWidth: true; placeholderText: "Optional ISO date, e.g. 2026-07-13T12:00:00+02:00" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_stop_loss; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridStopLoss; Layout.fillWidth: true; placeholderText: "Must be below the lower range" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_take_profit; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridTakeProfit; Layout.fillWidth: true; placeholderText: "Must be above the upper range" }
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: appController.appText.field_local_notes; color: textPrimary; font.pixelSize: 11; font.bold: true }
                            TextField { id: gridNotes; Layout.fillWidth: true; placeholderText: "Optional context for future reviews" }
                        }
                        CheckBox {
                            id: gridVerified
                            Layout.fillWidth: true
                            text: appController.appText.verified_matches_bot_checkbox
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Item { Layout.fillWidth: true }
                            Button {
                                text: appController.busy ? appController.appText.working_status : appController.appText.register_and_refresh_button
                                enabled: gridVerified.checked && !appController.busy
                                onClicked: {
                                    if (appController.registerGridStrategy(
                                            gridName.text, gridBotId.text, gridSymbol.currentText,
                                            gridRangeLow.text, gridRangeHigh.text, gridCount.text,
                                            gridType.currentText, gridInvestment.text, gridEntryPrice.text,
                                            gridStopLoss.text, gridTakeProfit.text, gridCreatedAt.text,
                                            gridNotes.text, gridVerified.checked)) {
                                        strategyRegistrationDialog.close()
                                    }
                                }
                            }
                        }
                    }

                    ColumnLayout {
                        spacing: 14
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                Layout.fillWidth: true
                                text: appController.appText.rebalancing_tab_description
                                color: textSecondary
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                            }
                            Button {
                                text: appController.appText.import_latest_recommendation_button
                                enabled: Boolean(appController.latestRebalancingRegistrationSuggestion.available)
                                onClicked: {
                                    var suggestion = appController.latestRebalancingRegistrationSuggestion
                                    rebalancingName.text = suggestion.name || ""
                                    rebalancingAssets.text = suggestion.assets || ""
                                    rebalancingWeights.text = suggestion.targetWeights || ""
                                    rebalancingEntryPrices.text = suggestion.entryPrices || ""
                                    rebalancingInvestment.text = suggestion.investment || ""
                                    rebalancingThreshold.text = suggestion.threshold || ""
                                    rebalancingVerified.checked = false
                                    strategyRegistrationDialog.importNotice = appController.appText.rebalancing_import_notice_template.replace("{run}", suggestion.sourceRun)
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.appText.allowed_assets_prefix + " " + appController.rebalancingRegistrationAssets.join(", ")
                            color: accent
                            font.pixelSize: 11
                            font.bold: true
                            wrapMode: Text.WordWrap
                        }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: width >= 700 ? 2 : 1
                            columnSpacing: 14
                            rowSpacing: 12

                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_local_name; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: rebalancingName; Layout.fillWidth: true; placeholderText: "Example: Core portfolio basket" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_binance_bot_id; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: rebalancingBotId; Layout.fillWidth: true; placeholderText: "Optional, but recommended" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_assets; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: rebalancingAssets; Layout.fillWidth: true; placeholderText: "BTC, ETH, SOL" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_target_weights; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: rebalancingWeights; Layout.fillWidth: true; placeholderText: "50, 25, 25" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_entry_prices_usdc; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: rebalancingEntryPrices; Layout.fillWidth: true; placeholderText: "One price for each asset" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_investment_usdc; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: rebalancingInvestment; Layout.fillWidth: true; placeholderText: "Exact allocated amount" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_rebalance_threshold; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: rebalancingThreshold; Layout.fillWidth: true; placeholderText: "Example: 10" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: appController.appText.field_created_at; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: rebalancingCreatedAt; Layout.fillWidth: true; placeholderText: "Optional ISO date; empty means now" }
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: appController.appText.field_local_notes; color: textPrimary; font.pixelSize: 11; font.bold: true }
                            TextField { id: rebalancingNotes; Layout.fillWidth: true; placeholderText: "Optional context for future reviews" }
                        }
                        CheckBox {
                            id: rebalancingVerified
                            Layout.fillWidth: true
                            text: appController.appText.verified_matches_bot_checkbox
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Item { Layout.fillWidth: true }
                            Button {
                                text: appController.busy ? appController.appText.working_status : appController.appText.register_and_refresh_button
                                enabled: rebalancingVerified.checked && !appController.busy
                                onClicked: {
                                    if (appController.registerRebalancingStrategy(
                                            rebalancingName.text, rebalancingBotId.text, rebalancingAssets.text,
                                            rebalancingWeights.text, rebalancingEntryPrices.text,
                                            rebalancingInvestment.text, rebalancingThreshold.text,
                                            rebalancingCreatedAt.text, rebalancingNotes.text,
                                            rebalancingVerified.checked)) {
                                        strategyRegistrationDialog.close()
                                    }
                                }
                            }
                        }
                    }
                }
                Item { Layout.fillWidth: true; Layout.preferredHeight: 12 }
            }
        }

        footer: DialogButtonBox {
            Button {
                text: appController.appText.close_button
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
                onClicked: strategyRegistrationDialog.close()
            }
        }
    }

    Item {
        id: appTourOverlay
        anchors.fill: parent
        visible: !appController.onboardingWizardVisible && appController.appTourVisible
        z: 1000

        property var targetItem: navigationRepeater.itemAt(window.navIndexForPage(appController.currentAppTourStep.page || 0))
        property point targetPosition: targetItem
            ? targetItem.mapToItem(appTourOverlay, 0, 0)
            : Qt.point(16, 120)
        property real holeX: Math.max(8, targetPosition.x - 6)
        property real holeY: Math.max(8, targetPosition.y - 3)
        property real holeWidth: targetItem ? targetItem.width + 12 : 220
        property real holeHeight: targetItem ? targetItem.height + 6 : 48
        property color shade: "#c4000000"

        MouseArea { anchors.fill: parent }

        Rectangle { x: 0; y: 0; width: parent.width; height: appTourOverlay.holeY; color: appTourOverlay.shade }
        Rectangle {
            x: 0
            y: appTourOverlay.holeY
            width: appTourOverlay.holeX
            height: appTourOverlay.holeHeight
            color: appTourOverlay.shade
        }
        Rectangle {
            x: appTourOverlay.holeX + appTourOverlay.holeWidth
            y: appTourOverlay.holeY
            width: Math.max(0, parent.width - x)
            height: appTourOverlay.holeHeight
            color: appTourOverlay.shade
        }
        Rectangle {
            x: 0
            y: appTourOverlay.holeY + appTourOverlay.holeHeight
            width: parent.width
            height: Math.max(0, parent.height - y)
            color: appTourOverlay.shade
        }

        Rectangle {
            x: appTourOverlay.holeX
            y: appTourOverlay.holeY
            width: appTourOverlay.holeWidth
            height: appTourOverlay.holeHeight
            radius: 8
            color: "transparent"
            border.width: 2
            border.color: accent
        }

        Rectangle {
            id: appTourCard
            width: Math.min(540, appTourOverlay.width - 300)
            implicitHeight: appTourCardContent.implicitHeight + 40
            x: Math.min(appTourOverlay.width - width - 28, appTourOverlay.holeX + appTourOverlay.holeWidth + 28)
            y: Math.max(28, Math.min(appTourOverlay.height - height - 28, appTourOverlay.holeY - 18))
            radius: 7
            color: panel
            border.color: accent
            border.width: 1

            ColumnLayout {
                id: appTourCardContent
                anchors.fill: parent
                anchors.margins: 20
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: appController.appText.app_tour_quick_tour_label + "  " + (appController.appTourStep + 1) + " / " + appController.appTourStepCount
                        color: accent
                        font.pixelSize: 10
                        font.bold: true
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        text: appController.appText.app_tour_skip_button
                        flat: true
                        onClicked: appController.skipAppTour()
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: appController.currentAppTourStep.title || ""
                    color: textPrimary
                    font.pixelSize: 20
                    font.bold: true
                    wrapMode: Text.WordWrap
                }
                Text {
                    Layout.fillWidth: true
                    text: appController.currentAppTourStep.detail || ""
                    color: textSecondary
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: appTourTip.implicitHeight + 24
                    radius: 6
                    color: panelRaised
                    border.color: border
                    Text {
                        id: appTourTip
                        anchors.fill: parent
                        anchors.margins: 12
                        text: appController.currentAppTourStep.tip || ""
                        color: textPrimary
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Repeater {
                        model: appController.appTourStepCount
                        delegate: Rectangle {
                            required property int index
                            Layout.preferredWidth: index === appController.appTourStep ? 20 : 7
                            Layout.preferredHeight: 7
                            radius: 4
                            color: index === appController.appTourStep ? accent : border
                        }
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        text: appController.appText.app_tour_back_button
                        enabled: appController.appTourStep > 0
                        onClicked: appController.previousAppTourStep()
                    }
                    Button {
                        text: appController.appTourStep === appController.appTourStepCount - 1 ? appController.appText.app_tour_finish_button : appController.appText.app_tour_next_button
                        highlighted: true
                        onClicked: appController.nextAppTourStep()
                    }
                }
            }
        }
    }

    Dialog {
        id: activeStrategyDetailDialog
        title: activeStrategyItem.name || appController.appText.active_strategy_fallback_title
        modal: true
        anchors.centerIn: parent
        width: Math.min(860, window.width - 96)
        height: Math.min(680, window.height - 96)
        standardButtons: Dialog.Close
        onOpened: {
            strategyStatusChoice.currentIndex = 0
            strategyStatusVerified.checked = false
        }

        ScrollView {
            id: activeStrategyDetailScroll
            anchors.fill: parent
            anchors.margins: 12
            rightPadding: 18
            clip: true
            contentWidth: availableWidth
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical.policy: ScrollBar.AsNeeded
            ColumnLayout {
                width: activeStrategyDetailScroll.availableWidth
                spacing: 14
                RowLayout {
                    Layout.fillWidth: true
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 3
                        Text { text: activeStrategyItem.name || ""; color: textPrimary; font.pixelSize: 22; font.bold: true }
                        Text { text: (activeStrategyItem.type || "") + "  |  " + appController.appText.binance_id_label + " " + (activeStrategyItem.botId || "-"); color: textSecondary; font.pixelSize: 12 }
                    }
                    Text { text: activeStrategyItem.health || appController.appText.unknown_status_fallback; color: activeStrategyItem.tone === "ready" ? accent : warning; font.pixelSize: 12; font.bold: true }
                }
                Text { text: activeStrategyItem.state || ""; color: activeStrategyItem.tone === "ready" ? accent : warning; font.pixelSize: 12; font.bold: true }
                Text { Layout.fillWidth: true; text: activeStrategyItem.recommendation || ""; color: textSecondary; font.pixelSize: 13; wrapMode: Text.WordWrap }
                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: border }
                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 12
                    rowSpacing: 10
                    Repeater {
                        model: window.toModel(activeStrategyItem.parameters)
                        delegate: Rectangle {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 68
                            radius: radiusSm
                            color: panelRaised
                            border.color: border
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 3
                                Text { text: modelData.label; color: textSecondary; font.pixelSize: 10; font.bold: true }
                                CopyableValue { Layout.fillWidth: true; value: modelData.value; font.pixelSize: 12 }
                            }
                        }
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: strategyMonitorNote.implicitHeight + 24
                    radius: radiusMd
                    color: warningSoft
                    border.color: warning
                    Text {
                        id: strategyMonitorNote
                        anchors.fill: parent
                        anchors.margins: 12
                        text: appController.appText.strategy_monitor_note
                        color: warning
                        font.pixelSize: 11
                        font.bold: true
                        wrapMode: Text.WordWrap
                    }
                }
                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: border }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    Text { text: appController.appText.update_local_monitoring_status_title; color: textPrimary; font.pixelSize: 16; font.bold: true }
                    Text {
                        Layout.fillWidth: true
                        text: appController.appText.update_local_status_warning
                        color: warning
                        font.pixelSize: 11
                        font.bold: true
                        wrapMode: Text.WordWrap
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: appController.appText.new_local_status_label; color: textSecondary; font.pixelSize: 10; font.bold: true }
                            ComboBox {
                                id: strategyStatusChoice
                                Layout.fillWidth: true
                                model: ["Paused", "Stopped", "Closed"]
                            }
                        }
                        Button {
                            text: appController.busy ? appController.appText.working_status : appController.appText.update_local_record_button
                            enabled: strategyStatusVerified.checked && !appController.busy
                            onClicked: {
                                if (appController.updateActiveStrategyStatus(
                                    activeStrategyItem.type || "",
                                    activeStrategyItem.name || "",
                                    strategyStatusChoice.currentText,
                                    strategyStatusVerified.checked)) {
                                    activeStrategyDetailDialog.close()
                                }
                            }
                        }
                    }
                    CheckBox {
                        id: strategyStatusVerified
                        Layout.fillWidth: true
                        text: appController.appText.already_applied_status_checkbox
                    }
                    Text {
                        Layout.fillWidth: true
                        text: appController.appText.status_records_note
                        color: textSecondary
                        font.pixelSize: 10
                        wrapMode: Text.WordWrap
                    }
                }
            }
        }
    }

    Dialog {
        id: liveApiManagerDialog
        title: appController.appText.manage_live_api_dialog_title
        modal: true
        anchors.centerIn: parent
        width: Math.min(840, window.width - 96)
        height: Math.min(720, window.height - 96)
        standardButtons: Dialog.NoButton
        onClosed: {
            liveTradingApiKey.text = ""
            liveTradingApiSecret.text = ""
            liveSeparateKey.checked = false
            liveIpRestricted.checked = false
            liveNoWithdrawals.checked = false
        }

        ScrollView {
            id: liveApiManagerScroll
            anchors.fill: parent
            anchors.margins: 12
            clip: true
            rightPadding: 18
            contentWidth: availableWidth
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical.policy: ScrollBar.AsNeeded

            ColumnLayout {
                width: liveApiManagerScroll.availableWidth
                spacing: 14
                Text {
                    Layout.fillWidth: true
                    text: appController.appText.live_api_dialog_description
                    color: textSecondary
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: liveApiWarningText.implicitHeight + 24
                    radius: radiusMd
                    color: warningSoft
                    border.color: warning
                    Text {
                        id: liveApiWarningText
                        anchors.fill: parent
                        anchors.margins: 12
                        text: appController.appText.live_api_dialog_warning
                        color: warning
                        font.pixelSize: 12
                        font.bold: true
                        wrapMode: Text.WordWrap
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: appController.liveTradingKeyDetail
                        color: textSecondary
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }
                    Button {
                        text: appController.appText.open_setup_guide_button
                        onClicked: window.openGuide("binance-live-api")
                    }
                }
                GridLayout {
                    Layout.fillWidth: true
                    columns: liveApiManagerDialog.width < 680 ? 1 : 2
                    columnSpacing: 10
                    rowSpacing: 10
                    TextField { id: liveTradingApiKey; Layout.fillWidth: true; placeholderText: "Live trading API key" }
                    TextField { id: liveTradingApiSecret; Layout.fillWidth: true; placeholderText: "Live trading secret key"; echoMode: TextInput.Password }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    CheckBox { id: liveSeparateKey; text: appController.appText.live_api_checkbox_separate_key; checked: false }
                    CheckBox { id: liveIpRestricted; text: appController.appText.live_api_checkbox_ip_restricted; checked: false }
                    CheckBox { id: liveNoWithdrawals; text: appController.appText.live_api_checkbox_no_withdrawals; checked: false }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Button {
                        text: appController.appText.save_live_trading_key_button
                        enabled: liveTradingApiKey.text.trim().length > 0
                            && liveTradingApiSecret.text.trim().length > 0
                            && liveSeparateKey.checked
                            && liveIpRestricted.checked
                            && liveNoWithdrawals.checked
                        onClicked: {
                            appController.saveBinanceLiveTradingCredentials(liveTradingApiKey.text, liveTradingApiSecret.text)
                            liveTradingApiKey.text = ""
                            liveTradingApiSecret.text = ""
                            liveSeparateKey.checked = false
                            liveIpRestricted.checked = false
                            liveNoWithdrawals.checked = false
                            window.showToast(appController.appText.live_trading_key_saved_toast)
                        }
                    }
                    Button {
                        text: appController.checkingLiveTrading ? appController.appText.checking_permissions_status : appController.appText.verify_permissions_button
                        enabled: appController.liveTradingKeyStatus === "PASS" && !appController.checkingLiveTrading
                        onClicked: appController.checkBinanceLiveTrading()
                    }
                    Item { Layout.fillWidth: true }
                    StatusPill {
                        label: appController.liveTradingCheckState === "Verified" ? "VERIFIED" : appController.liveTradingKeyStatus === "PASS" ? "CONFIGURED" : "LOCKED"
                        tone: appController.liveTradingCheckState === "Verified" ? "success" : "warning"
                    }
                }
                Text {
                    Layout.fillWidth: true
                    text: appController.liveTradingCheckDetail
                    color: textSecondary
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }
                Text {
                    Layout.fillWidth: true
                    text: appController.appText.live_submit_control_note
                    color: warning
                    font.pixelSize: 11
                    font.bold: true
                    wrapMode: Text.WordWrap
                }
                RowLayout {
                    Layout.fillWidth: true
                    Item { Layout.fillWidth: true }
                    Button { text: appController.appText.close_button; onClicked: liveApiManagerDialog.close() }
                }
            }
        }
    }

    Dialog {
        id: safetyStageConfirmDialog
        title: appController.appText.confirm_safety_stage_title
        modal: true
        anchors.centerIn: parent
        width: Math.min(680, window.width - 120)
        standardButtons: Dialog.NoButton

        ColumnLayout {
            width: safetyStageConfirmDialog.width - 48
            spacing: 14
            Text {
                Layout.fillWidth: true
                text: pendingSafetyTarget === "LIVE_ENABLED"
                    ? appController.appText.safety_confirm_live_enabled_note
                    : pendingSafetyTarget === "ARMED"
                        ? appController.appText.safety_confirm_armed_note
                        : appController.appText.safety_confirm_preview_note
                color: textSecondary
                font.pixelSize: 13
                wrapMode: Text.WordWrap
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: safetyPhraseRow.implicitHeight + 24
                radius: radiusMd
                color: warningSoft
                border.color: warning
                RowLayout {
                    id: safetyPhraseRow
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 12
                    Text {
                        Layout.fillWidth: true
                        text: appController.appText.confirmation_phrase_prefix + " " + pendingSafetyPhrase
                        color: warning
                        font.pixelSize: 12
                        font.bold: true
                        wrapMode: Text.WordWrap
                    }
                    Button {
                        text: appController.appText.copy_phrase_button
                        onClicked: appController.copyText(pendingSafetyPhrase)
                    }
                }
            }
            TextField {
                id: safetyStageConfirmInput
                Layout.fillWidth: true
                placeholderText: pendingSafetyPhrase
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Button { text: appController.appText.cancel_button; onClicked: safetyStageConfirmDialog.close() }
                Button {
                    text: appController.appText.change_safety_stage_button
                    enabled: safetyStageConfirmInput.text === pendingSafetyPhrase
                    onClicked: {
                        appController.promoteSafetyStage(pendingSafetyTarget, safetyStageConfirmInput.text)
                        safetyStageConfirmDialog.close()
                    }
                }
                Item { Layout.fillWidth: true; Layout.preferredHeight: 36 }
            }
        }
    }

    Dialog {
        id: actionPlanDetailDialog
        // Named so a screenshot test can open it without guessing at child types.
        objectName: "actionPlanDetailDialog"
        title: activeActionPlanItem.title || appController.appText.action_detail_fallback_title
        modal: true
        anchors.centerIn: parent
        width: Math.min(920, window.width - 96)
        height: Math.min(700, window.height - 96)
        standardButtons: Dialog.Close

        ScrollView {
            id: actionPlanDetailScroll
            anchors.fill: parent
            anchors.margins: 12
            clip: true
            // The vertical scrollbar is an overlay, so reserve its width or it
            // covers the right edge of the content (matches the other dialogs).
            rightPadding: 18
            contentWidth: availableWidth
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ColumnLayout {
                width: actionPlanDetailScroll.availableWidth
                spacing: 16
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: activeActionPlanItem.title || ""
                        color: textPrimary
                        font.pixelSize: 22
                        font.bold: true
                    }
                    StatusPill {
                        label: activeActionPlanItem.status || "UNKNOWN"
                        tone: activeActionPlanItem.tone === "ready" ? "success" : activeActionPlanItem.tone === "watch" ? "warning" : "neutral"
                    }
                }
                Text {
                    Layout.fillWidth: true
                    text: activeActionPlanItem.detail || ""
                    color: textSecondary
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                }
                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: border }
                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 14
                    rowSpacing: 10
                    Repeater {
                        model: window.toModel(activeActionPlanItem.parameters)
                        delegate: Rectangle {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 68
                            radius: radiusSm
                            color: panelRaised
                            border.color: border
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 3
                                Text { text: modelData.label; color: textSecondary; font.pixelSize: 10; font.bold: true }
                                CopyableValue {
                                    Layout.fillWidth: true
                                    value: modelData.value
                                    font.pixelSize: 13
                                }
                            }
                        }
                    }
                }
                ColumnLayout {
                    // The numbered procedure for setting the bot up on Binance.
                    // It lived only in the Markdown report, so the dialog showed
                    // the numbers to retype with no procedure to retype them into.
                    Layout.fillWidth: true
                    visible: (activeActionPlanItem.manualSteps || []).length > 0
                    spacing: 10
                    Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: border }
                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            Layout.fillWidth: true
                            text: appController.appText.manual_steps_title
                            color: textPrimary
                            font.pixelSize: 16
                            font.bold: true
                        }
                        // The whole point of this list is to be worked through
                        // against Binance in another window, and every price and
                        // count in it had to be retyped by eye.
                        Button {
                            text: appController.appText.copy_manual_steps_button
                            onClicked: appController.copyManualSteps(activeActionPlanItem.manualSteps)
                        }
                    }
                    Repeater {
                        model: window.toModel(activeActionPlanItem.manualSteps)
                        delegate: RowLayout {
                            required property var modelData
                            required property int index
                            Layout.fillWidth: true
                            spacing: 10
                            Text {
                                Layout.alignment: Qt.AlignTop
                                Layout.preferredWidth: 20
                                text: (index + 1) + "."
                                color: textSecondary
                                font.pixelSize: 12
                                font.bold: true
                            }
                            // TextEdit, not Text: read-only but selectable, so a
                            // single price can be dragged out without copying
                            // the entire procedure.
                            TextEdit {
                                Layout.fillWidth: true
                                text: modelData
                                color: textPrimary
                                font.pixelSize: 12
                                wrapMode: TextEdit.Wrap
                                readOnly: true
                                selectByMouse: true
                                selectionColor: accent
                                activeFocusOnPress: true
                            }
                        }
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    visible: activeActionPlanItem.liveLifecycle !== undefined && activeActionPlanItem.liveLifecycle !== null
                    spacing: 12
                    Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: border }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { Layout.fillWidth: true; text: appController.appText.last_live_trade_label; color: textPrimary; font.pixelSize: 16; font.bold: true }
                        Text {
                            text: activeActionPlanItem.liveLifecycle ? activeActionPlanItem.liveLifecycle.status : ""
                            color: activeActionPlanItem.liveLifecycle && activeActionPlanItem.liveLifecycle.tone === "ready" ? accent : warning
                            font.pixelSize: 11
                            font.bold: true
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        text: activeActionPlanItem.liveLifecycle ? activeActionPlanItem.liveLifecycle.detail : ""
                        color: textSecondary
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                    }
                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 12
                        rowSpacing: 12
                        Repeater {
                            model: window.toModel(activeActionPlanItem.liveLifecycle ? activeActionPlanItem.liveLifecycle.lifecycleSteps : [])
                            delegate: Rectangle {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.preferredHeight: 76
                                radius: radiusSm
                                color: panelRaised
                                border.color: modelData.status === "Done" ? accent : modelData.status === "Action needed" ? warning : border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    spacing: 3
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Text { Layout.fillWidth: true; text: modelData.label; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                        Text { text: modelData.status; color: modelData.status === "Done" ? accent : modelData.status === "Action needed" ? warning : textSecondary; font.pixelSize: 10; font.bold: true }
                                    }
                                    Text { Layout.fillWidth: true; text: modelData.detail; color: textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                }
                            }
                        }
                    }
                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 12
                        rowSpacing: 10
                        Repeater {
                            model: window.toModel(activeActionPlanItem.liveLifecycle ? activeActionPlanItem.liveLifecycle.parameters : [])
                            delegate: Rectangle {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.preferredHeight: 64
                                radius: radiusSm
                                color: panelRaised
                                border.color: border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    spacing: 3
                                    Text { text: modelData.label; color: textSecondary; font.pixelSize: 10; font.bold: true }
                                    CopyableValue { Layout.fillWidth: true; value: modelData.value; font.pixelSize: 12 }
                                }
                            }
                        }
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: actionDetailNote.implicitHeight + 28
                    radius: radiusMd
                    color: warningSoft
                    border.color: warning
                    Text {
                        id: actionDetailNote
                        anchors.fill: parent
                        anchors.margins: 12
                        text: activeActionPlanItem.actionCode === "REVIEW_TRADE"
                            ? (activeActionPlanItem.liveLifecycle
                                ? appController.appText.action_note_trade_resync
                                : appController.appText.action_note_trade_locked)
                            : activeActionPlanItem.actionCode === "REVIEW_OCO"
                                ? appController.appText.action_note_oco
                                : activeActionPlanItem.actionCode === "REVIEW_EARN_REDEEM"
                                    ? appController.appText.action_note_earn_redeem
                                : activeActionPlanItem.actionCode === "OPEN_ACTIVE_STRATEGIES"
                                    ? appController.appText.action_note_lifecycle
                                : appController.appText.action_note_review_only
                        color: warning
                        font.pixelSize: 12
                        font.bold: true
                        wrapMode: Text.WordWrap
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: liveTradeGuardContent.implicitHeight + 28
                    visible: activeActionPlanItem.actionCode === "REVIEW_TRADE" || activeActionPlanItem.actionCode === "REVIEW_OCO" || activeActionPlanItem.actionCode === "REVIEW_EARN_REDEEM"
                    radius: radiusMd
                    color: panelRaised
                    border.color: activeActionPlanItem.submitEnabled === true ? accent : border
                    ColumnLayout {
                        id: liveTradeGuardContent
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 8
                        Text {
                            text: activeActionPlanItem.actionCode === "REVIEW_OCO" ? appController.appText.guard_title_oco
                                : activeActionPlanItem.actionCode === "REVIEW_EARN_REDEEM" ? appController.appText.guard_title_earn_redeem
                                : appController.appText.guard_title_trade
                            color: textPrimary
                            font.pixelSize: 15
                            font.bold: true
                        }
                        Text {
                            Layout.fillWidth: true
                            text: activeActionPlanItem.submitEnabled === true
                                ? activeActionPlanItem.actionCode === "REVIEW_OCO"
                                    ? appController.appText.guard_ready_oco
                                    : activeActionPlanItem.actionCode === "REVIEW_EARN_REDEEM"
                                        ? appController.appText.guard_ready_earn_redeem
                                        : appController.appText.guard_ready_trade
                                : (activeActionPlanItem.submitBlockedReason || appController.appText.live_submit_locked_fallback)
                            color: activeActionPlanItem.submitEnabled === true ? textSecondary : warning
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Item { Layout.fillWidth: true }
                            Button {
                                text: activeActionPlanItem.submitEnabled === true ? activeActionPlanItem.submitLabel : appController.appText.locked_button_fallback
                                enabled: activeActionPlanItem.submitEnabled === true && !appController.busy
                                onClicked: {
                                    if (activeActionPlanItem.actionCode === "REVIEW_OCO") {
                                        ocoConfirmInput.text = ""
                                        ocoConfirmDialog.open()
                                    } else if (activeActionPlanItem.actionCode === "REVIEW_EARN_REDEEM") {
                                        earnRedeemConfirmInput.text = ""
                                        earnRedeemConfirmDialog.open()
                                    } else {
                                        liveTradeConfirmInput.text = ""
                                        liveTradeConfirmDialog.open()
                                    }
                                }
                            }
                        }
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: challengeHoldContent.implicitHeight + 28
                    visible: activeActionPlanItem.actionCode === "REVIEW_TRADE" && activeActionPlanItem.status === "HOLD"
                    radius: radiusMd
                    color: panelRaised
                    border.color: border
                    ColumnLayout {
                        id: challengeHoldContent
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 8
                        Text { text: appController.appText.challenge_hold_title; color: textPrimary; font.pixelSize: 15; font.bold: true }
                        Text {
                            Layout.fillWidth: true
                            text: appController.appText.challenge_hold_description
                            color: textSecondary
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            ComboBox {
                                id: challengeHoldSymbol
                                Layout.preferredWidth: 200
                                model: appController.manualOverrideSymbols
                            }
                            Button {
                                text: appController.busy ? appController.appText.running_status : appController.appText.challenge_hold_button
                                enabled: !appController.busy && appController.manualOverrideSymbols.length > 0
                                // Deliberately does not close the dialog: closing it
                                // dropped the user on the Action Plan with no idea
                                // whether anything was happening. The dialog stays
                                // open, shows progress, and refreshes in place.
                                onClicked: appController.challengeHold(challengeHoldSymbol.currentText)
                            }
                            BusyDots {
                                Layout.alignment: Qt.AlignVCenter
                                visible: appController.busy
                            }
                            Text {
                                Layout.fillWidth: true
                                visible: appController.busy
                                text: appController.statusText
                                color: textSecondary
                                font.pixelSize: 11
                                elide: Text.ElideRight
                            }
                            Item { Layout.fillWidth: true; visible: !appController.busy }
                        }
                        // Persistent result: the toast that carried this
                        // disappeared before it could be read, leaving no record
                        // of what the challenge actually did.
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: challengeOutcomeText.implicitHeight + 20
                            // Keyed off the label's own text so visibility and
                            // content can never disagree and show an empty box.
                            visible: !appController.busy && challengeOutcomeText.text.length > 0
                            radius: radiusSm
                            color: accentSoft
                            border.color: accent
                            Text {
                                id: challengeOutcomeText
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.leftMargin: 12
                                anchors.rightMargin: 12
                                text: appController.challengeOutcome
                                color: textPrimary
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    visible: activeActionPlanItem.actionCode === "OPEN_ACTIVE_STRATEGIES"
                    Item { Layout.fillWidth: true }
                    Button {
                        text: appController.appText.open_active_strategies_button
                        onClicked: {
                            actionPlanDetailDialog.close()
                            appController.setCurrentPage(4)
                        }
                    }
                }
                Item { Layout.fillWidth: true; Layout.preferredHeight: 14 }
            }
        }
    }

    Dialog {
        id: liveTradeConfirmDialog
        title: appController.appText.confirm_live_trade_title
        modal: true
        anchors.centerIn: parent
        width: Math.min(680, window.width - 120)
        standardButtons: Dialog.NoButton

        ColumnLayout {
            width: liveTradeConfirmDialog.width - 48
            spacing: 14
            Text {
                Layout.fillWidth: true
                text: appController.appText.confirm_live_trade_description
                color: textSecondary
                font.pixelSize: 13
                wrapMode: Text.WordWrap
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: liveTradeConfirmWarning.implicitHeight + 24
                radius: radiusMd
                color: warningSoft
                border.color: warning
                Text {
                    id: liveTradeConfirmWarning
                    anchors.fill: parent
                    anchors.margins: 12
                    text: appController.appText.confirm_live_trade_warning
                    color: warning
                    font.pixelSize: 12
                    font.bold: true
                    wrapMode: Text.WordWrap
                }
            }
            TextField {
                id: liveTradeConfirmInput
                Layout.fillWidth: true
                placeholderText: "CONFIRM_MAINNET_ORDER"
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Button {
                    text: appController.appText.cancel_button
                    onClicked: liveTradeConfirmDialog.close()
                }
                Button {
                    text: appController.appText.run_guarded_submit_button
                    enabled: liveTradeConfirmInput.text === "CONFIRM_MAINNET_ORDER" && activeActionPlanItem.submitEnabled === true && !appController.busy
                    onClicked: {
                        appController.submitGuardedTrade(liveTradeConfirmInput.text)
                        liveTradeConfirmDialog.close()
                        actionPlanDetailDialog.close()
                    }
                }
            }
        }
    }

    PlatformDialogs.FileDialog {
        id: assistantImageDialog
        title: appController.appText.attach_screenshot_dialog_title
        fileMode: PlatformDialogs.FileDialog.OpenFile
        nameFilters: ["Images (*.png *.jpg *.jpeg *.webp)"]
        onAccepted: appController.attachAssistantImage(selectedFile.toString())
    }

    Dialog {
        id: assistantHistoryDialog
        title: appController.appText.ai_chat_history_title
        modal: true
        anchors.centerIn: parent
        width: Math.min(760, window.width - 96)
        height: Math.min(600, window.height - 96)
        standardButtons: Dialog.Close

        contentItem: ColumnLayout {
            spacing: 12
            Text {
                Layout.fillWidth: true
                text: appController.appText.ai_chat_history_storage_note
                color: textSecondary
                font.pixelSize: 12
                wrapMode: Text.WordWrap
            }
            Text {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: appController.assistantHistory.length === 0
                text: appController.appText.ai_chat_history_empty
                color: textSecondary
                font.pixelSize: 13
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                wrapMode: Text.WordWrap
            }
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: appController.assistantHistory.length > 0
                spacing: 10
                clip: true
                model: appController.assistantHistory
                delegate: Rectangle {
                    required property var modelData
                    width: ListView.view.width
                    height: 112
                    radius: radiusSm
                    color: panelRaised
                    border.color: border
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 12
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5
                            Text { Layout.fillWidth: true; text: modelData.title; color: textPrimary; font.pixelSize: 14; font.bold: true; elide: Text.ElideRight }
                            Text { Layout.fillWidth: true; text: modelData.preview; color: textSecondary; font.pixelSize: 11; elide: Text.ElideRight }
                            Text { text: modelData.contextPage + " | " + modelData.messageCount + " " + appController.appText.ai_chat_history_messages_label + " | " + modelData.updatedAt; color: textSecondary; font.pixelSize: 10 }
                        }
                        Button {
                            text: appController.appText.open_button
                            onClicked: {
                                appController.restoreAssistantChat(modelData.id)
                                assistantHistoryDialog.close()
                            }
                        }
                    }
                }
            }
        }
    }

    Dialog {
        id: ocoConfirmDialog
        title: appController.appText.confirm_oco_title
        modal: true
        anchors.centerIn: parent
        width: Math.min(680, window.width - 120)
        standardButtons: Dialog.NoButton

        ColumnLayout {
            width: ocoConfirmDialog.width - 48
            spacing: 14
            Text {
                Layout.fillWidth: true
                text: appController.appText.confirm_oco_description
                color: textSecondary
                font.pixelSize: 13
                wrapMode: Text.WordWrap
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: ocoConfirmWarning.implicitHeight + 24
                radius: radiusMd
                color: warningSoft
                border.color: warning
                Text {
                    id: ocoConfirmWarning
                    anchors.fill: parent
                    anchors.margins: 12
                    text: appController.appText.confirm_oco_warning
                    color: warning
                    font.pixelSize: 12
                    font.bold: true
                    wrapMode: Text.WordWrap
                }
            }
            TextField {
                id: ocoConfirmInput
                Layout.fillWidth: true
                placeholderText: "CONFIRM_MAINNET_OCO"
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Button {
                    text: appController.appText.cancel_button
                    onClicked: ocoConfirmDialog.close()
                }
                Button {
                    text: appController.appText.submit_oco_button
                    enabled: ocoConfirmInput.text === "CONFIRM_MAINNET_OCO" && activeActionPlanItem.submitEnabled === true && !appController.busy
                    onClicked: {
                        appController.submitGuardedOco(ocoConfirmInput.text)
                        ocoConfirmDialog.close()
                        actionPlanDetailDialog.close()
                    }
                }
            }
        }
    }
    Dialog {
        id: earnRedeemConfirmDialog
        title: appController.appText.confirm_earn_redeem_title
        modal: true
        anchors.centerIn: parent
        width: Math.min(680, window.width - 120)
        standardButtons: Dialog.NoButton

        ColumnLayout {
            width: earnRedeemConfirmDialog.width - 48
            spacing: 14
            Text {
                Layout.fillWidth: true
                text: appController.appText.confirm_earn_redeem_description
                color: textSecondary
                font.pixelSize: 13
                wrapMode: Text.WordWrap
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: earnRedeemConfirmWarning.implicitHeight + 24
                radius: radiusMd
                color: warningSoft
                border.color: warning
                Text {
                    id: earnRedeemConfirmWarning
                    anchors.fill: parent
                    anchors.margins: 12
                    text: appController.appText.confirm_earn_redeem_warning
                    color: warning
                    font.pixelSize: 12
                    font.bold: true
                    wrapMode: Text.WordWrap
                }
            }
            TextField {
                id: earnRedeemConfirmInput
                Layout.fillWidth: true
                placeholderText: "CONFIRM_EARN_REDEEM"
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Button {
                    text: appController.appText.cancel_button
                    onClicked: earnRedeemConfirmDialog.close()
                }
                Button {
                    text: appController.appText.submit_earn_redeem_button
                    enabled: earnRedeemConfirmInput.text === "CONFIRM_EARN_REDEEM" && activeActionPlanItem.submitEnabled === true && !appController.busy
                    onClicked: {
                        appController.submitGuardedEarnRedeem(earnRedeemConfirmInput.text)
                        earnRedeemConfirmDialog.close()
                        actionPlanDetailDialog.close()
                    }
                }
            }
        }
    }
    Dialog {
        id: firstPortfolioDeployDialog
        title: appController.appText.deploy_tranche_dialog_title_template.replace("{asset}", firstPortfolioDeployAsset)
        modal: true
        anchors.centerIn: parent
        width: Math.min(680, window.width - 120)
        standardButtons: Dialog.NoButton

        property string mode: "TESTNET"
        property string expectedConfirm: mode === "MAINNET" ? "CONFIRM_MAINNET_ORDER" : "CONFIRM_TESTNET_ORDER"

        onOpened: {
            mode = "TESTNET"
            firstPortfolioConfirmInput.text = ""
        }

        ColumnLayout {
            width: firstPortfolioDeployDialog.width - 48
            spacing: 14
            Text {
                Layout.fillWidth: true
                text: appController.appText.deploy_tranche_description_template.replace("{asset}", firstPortfolioDeployAsset).replace("{pct}", firstPortfolioDeployTargetPct)
                color: textSecondary
                font.pixelSize: 13
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Text { text: appController.appText.mode_label; color: textPrimary; font.pixelSize: 12 }
                ComboBox {
                    id: firstPortfolioModeCombo
                    Layout.preferredWidth: 160
                    model: ["TESTNET", "MAINNET"]
                    onCurrentTextChanged: firstPortfolioDeployDialog.mode = currentText
                }
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: firstPortfolioMainnetWarning.implicitHeight + 24
                visible: firstPortfolioDeployDialog.mode === "MAINNET"
                radius: radiusMd
                color: warningSoft
                border.color: warning
                Text {
                    id: firstPortfolioMainnetWarning
                    anchors.fill: parent
                    anchors.margins: 12
                    text: appController.appText.mainnet_submit_warning
                    color: warning
                    font.pixelSize: 12
                    font.bold: true
                    wrapMode: Text.WordWrap
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Button {
                    text: appController.appText.validate_only_button
                    enabled: parseFloat(firstPortfolioBudgetInput.text) > 0 && !appController.busy
                    onClicked: {
                        appController.runFirstPortfolioTranche(
                            firstPortfolioDeployAsset,
                            firstPortfolioDeployTargetPct,
                            parseFloat(firstPortfolioBudgetInput.text) || 0,
                            firstPortfolioTranchesInput.value,
                            firstPortfolioDeployDialog.mode,
                            false,
                            ""
                        )
                        firstPortfolioDeployDialog.close()
                    }
                }
            }
            Text {
                Layout.fillWidth: true
                text: appController.appText.submit_for_real_prefix
                color: textSecondary
                font.pixelSize: 12
                wrapMode: Text.WordWrap
            }
            // The phrase has to be reproduced exactly, so it is the last thing
            // that should have to be retyped from a label.
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                CopyableValue {
                    value: firstPortfolioDeployDialog.expectedConfirm
                    font.pixelSize: 13
                    font.bold: true
                    font.family: "Consolas"
                }
                Button {
                    text: appController.appText.copy_button
                    onClicked: appController.copyValue(firstPortfolioDeployDialog.expectedConfirm)
                }
                Item { Layout.fillWidth: true }
            }
            TextField {
                id: firstPortfolioConfirmInput
                Layout.fillWidth: true
                placeholderText: firstPortfolioDeployDialog.expectedConfirm
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Button {
                    text: appController.appText.cancel_button
                    onClicked: firstPortfolioDeployDialog.close()
                }
                Button {
                    text: appController.appText.submit_tranche_button
                    enabled: firstPortfolioConfirmInput.text === firstPortfolioDeployDialog.expectedConfirm
                        && parseFloat(firstPortfolioBudgetInput.text) > 0
                        && !appController.busy
                    onClicked: {
                        appController.runFirstPortfolioTranche(
                            firstPortfolioDeployAsset,
                            firstPortfolioDeployTargetPct,
                            parseFloat(firstPortfolioBudgetInput.text) || 0,
                            firstPortfolioTranchesInput.value,
                            firstPortfolioDeployDialog.mode,
                            true,
                            firstPortfolioConfirmInput.text
                        )
                        firstPortfolioDeployDialog.close()
                    }
                }
            }
        }
    }
    Dialog {
        id: guideDialog
        title: activeGuide.title || appController.appText.help_guides_title
        modal: true
        anchors.centerIn: parent
        width: Math.min(820, window.width - 80)
        height: Math.min(640, window.height - 80)
        standardButtons: Dialog.Close

        ScrollView {
            id: guideScroll
            anchors.fill: parent
            clip: true
            // The vertical scrollbar is drawn as an overlay, so availableWidth
            // still spans under it; reserve the space explicitly or it covers
            // the right edge of the text.
            rightPadding: 18
            contentWidth: availableWidth
            contentHeight: guideDialogContent.implicitHeight + 24
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                id: guideDialogContent
                width: guideScroll.availableWidth
                spacing: 14
                StatusPill {
                    label: activeGuide.section || appController.appText.guide_section_fallback
                    tone: "success"
                }
                Text {
                    Layout.fillWidth: true
                    text: activeGuide.summary || ""
                    color: textSecondary
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: guideWarningText.implicitHeight + 24
                    visible: Boolean(activeGuide.warning)
                    radius: radiusMd
                    color: warningSoft
                    border.color: warning
                    Text {
                        id: guideWarningText
                        anchors.fill: parent
                        anchors.margins: 12
                        text: activeGuide.warning || ""
                        color: warning
                        font.pixelSize: 13
                        font.bold: true
                        wrapMode: Text.WordWrap
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: border
                }
                Text {
                    Layout.fillWidth: true
                    text: activeGuide.body || ""
                    textFormat: Text.RichText
                    linkColor: accent
                    color: textPrimary
                    font.pixelSize: 13
                    lineHeight: 1.18
                    wrapMode: Text.WordWrap
                    onLinkActivated: (link) => window.handleGuideLink(link)
                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.NoButton
                        cursorShape: parent.hoveredLink ? Qt.PointingHandCursor : Qt.ArrowCursor
                    }
                }
                Repeater {
                    model: window.toModel(activeGuide.images)
                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 6
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 260
                            radius: radiusSm
                            color: panelRaised
                            border.color: border
                            clip: true
                            Image {
                                anchors.fill: parent
                                anchors.margins: 8
                                source: modelData.source
                                fillMode: Image.PreserveAspectFit
                                smooth: true
                                asynchronous: true
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.caption
                            color: textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                    }
                }
                Text {
                    Layout.fillWidth: true
                    text: appController.appText.guide_footer_note
                    color: textSecondary
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }
            }
        }
    }

    Popup {
        id: toastPopup
        x: window.width - width - 28
        y: 28
        // Measured unwrapped, so the box can size to short messages without
        // depending on the (wrapped) label width, which would be a loop.
        width: Math.min(Math.min(560, window.width - 56), Math.max(260, toastMetrics.width + 36))
        height: toastLabel.implicitHeight + 24
        modal: false
        focus: false
        closePolicy: Popup.NoAutoClose
        background: Rectangle {
            radius: radiusMd
            color: "#14352c"
            border.color: accent
        }
        TextMetrics {
            id: toastMetrics
            font: toastLabel.font
            text: window.toastText
        }
        Text {
            id: toastLabel
            anchors.centerIn: parent
            // Bounded width: without it the text ignored elide, overflowed the
            // popup and was cut off at the window edge.
            width: toastPopup.width - 36
            text: window.toastText
            color: textPrimary
            font.pixelSize: 13
            font.bold: true
            wrapMode: Text.WordWrap
        }
    }

    Timer {
        id: toastTimer
        // Long outcome messages were gone before they could be read.
        interval: Math.max(3000, Math.min(11000, window.toastText.length * 70))
        onTriggered: toastPopup.close()
    }

    Dialog {
        id: deleteProfileDialog
        title: appController.appText.reset_onboarding_profile_title
        modal: true
        anchors.centerIn: parent
        width: 460
        standardButtons: Dialog.Cancel

        ColumnLayout {
            width: parent.width
            spacing: 14
            Label {
                Layout.fillWidth: true
                text: appController.appText.reset_onboarding_profile_note1
                wrapMode: Text.WordWrap
            }
            Label {
                Layout.fillWidth: true
                text: appController.appText.reset_onboarding_profile_note2
                wrapMode: Text.WordWrap
            }
            Button {
                Layout.fillWidth: true
                text: appController.appText.reset_onboarding_profile_title
                onClicked: {
                    deleteProfileDialog.close()
                    appController.deleteUserProfile()
                }
            }
        }
    }

    ListModel { id: localDataResetModel }

    Dialog {
        id: localDataResetDialog
        title: appController.appText.delete_local_app_data_title
        modal: true
        anchors.centerIn: parent
        width: 640
        standardButtons: Dialog.Cancel
        onOpened: {
            localDataResetModel.clear()
            for (let i = 0; i < appController.localDataResetItems.length; i++) {
                let item = appController.localDataResetItems[i]
                localDataResetModel.append({
                    "code": item.code,
                    "name": item.name,
                    "detail": item.detail,
                    "paths": item.paths,
                    "status": item.status,
                    "selected": item.default === "true"
                })
            }
            deleteEverything.checked = false
            deleteConfirm.text = ""
        }

        ColumnLayout {
            width: parent.width
            spacing: 14
            Label {
                Layout.fillWidth: true
                text: appController.localDataResetSummary
                wrapMode: Text.WordWrap
            }
            CheckBox {
                id: deleteEverything
                text: appController.appText.delete_everything_checkbox
                onToggled: {
                    for (let i = 0; i < localDataResetModel.count; i++) {
                        localDataResetModel.setProperty(i, "selected", checked)
                    }
                }
            }
            ListView {
                Layout.fillWidth: true
                Layout.preferredHeight: 270
                clip: true
                spacing: 6
                model: localDataResetModel
                delegate: Rectangle {
                    required property int index
                    required property string name
                    required property string detail
                    required property string status
                    required property bool selected
                    width: ListView.view.width
                    height: 64
                    radius: radiusSm
                    color: panelRaised
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 10
                        CheckBox {
                            checked: selected
                            onToggled: localDataResetModel.setProperty(index, "selected", checked)
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 3
                            RowLayout {
                                Layout.fillWidth: true
                                Text { Layout.fillWidth: true; text: name; color: textPrimary; font.pixelSize: 12; font.bold: true; elide: Text.ElideRight }
                                Text { text: status; color: textSecondary; font.pixelSize: 10 }
                            }
                            Text { Layout.fillWidth: true; text: detail; color: textSecondary; font.pixelSize: 10; elide: Text.ElideRight }
                        }
                    }
                }
            }
            Label {
                Layout.fillWidth: true
                text: appController.appText.delete_local_data_warning
                color: warning
                wrapMode: Text.WordWrap
            }
            TextField {
                id: deleteConfirm
                Layout.fillWidth: true
                placeholderText: "DELETE"
            }
            Button {
                Layout.fillWidth: true
                text: deleteConfirm.text === "DELETE" ? appController.appText.delete_selected_local_data_button : appController.appText.type_delete_to_continue_button
                enabled: deleteConfirm.text === "DELETE" && !appController.busy
                onClicked: {
                    let codes = []
                    for (let i = 0; i < localDataResetModel.count; i++) {
                        let item = localDataResetModel.get(i)
                        if (item.selected)
                            codes.push(item.code)
                    }
                    if (appController.executeLocalDataReset(codes, deleteConfirm.text))
                        localDataResetDialog.close()
                }
            }
        }
    }

    Dialog {
        id: runDialog
        title: appController.appText.overview_run_analysis_button
        modal: true
        anchors.centerIn: parent
        width: 440
        standardButtons: Dialog.Cancel

        ColumnLayout {
            width: parent.width
            spacing: 14
            Label { text: appController.appText.data_source_label }
            ComboBox {
                id: dataMode
                Layout.fillWidth: true
                model: ["REAL", "MOCK"]
            }
            CheckBox {
                id: aiSummary
                text: appController.appText.generate_ai_summary_checkbox
                // Ticking these without a provider produced a run that asked
                // nothing and then explained itself in a panel afterwards.
                enabled: appController.activeAiProviderKind !== "NONE"
                checked: appController.activeAiProviderKind !== "NONE"
            }
            CheckBox {
                id: aiProposals
                text: appController.appText.allow_ai_market_ranking_checkbox
                enabled: appController.activeAiProviderKind !== "NONE"
                checked: false
            }
            Text {
                Layout.fillWidth: true
                visible: appController.activeAiProviderKind === "NONE"
                text: appController.appText.no_ai_provider_run_detail
                color: warning
                font.pixelSize: 11
                wrapMode: Text.WordWrap
            }
            CheckBox {
                id: livePreview
                text: appController.safetyAllowsLivePreview ? appController.appText.include_mainnet_preview_checkbox : appController.appText.mainnet_preview_locked_checkbox
                checked: appController.safetyAllowsLivePreview
                enabled: appController.safetyAllowsLivePreview
            }
            Label {
                Layout.fillWidth: true
                text: appController.appText.run_dialog_note
                wrapMode: Text.WordWrap
            }
            Button {
                Layout.fillWidth: true
                text: appController.appText.start_analysis_button
                onClicked: {
                    runDialog.close()
                    appController.runAnalysis(
                        dataMode.currentText,
                        aiSummary.checked,
                        aiProposals.checked,
                        livePreview.checked
                    )
                }
            }
        }
    }

    component MetricCard: Rectangle {
        id: metricCard
        required property string title
        required property string value
        required property color accentColor
        property string helpText: ""
        Layout.fillWidth: true
        // Most values are short ("829.06 USDC"), but the risk gate holds a
        // sentence. Grow instead of truncating it to one unreadable line;
        // cards in a row share the tallest height, so they stay aligned.
        Layout.preferredHeight: Math.max(104, metricCardContent.implicitHeight + spacingLg * 2)
        radius: radiusMd
        color: panel
        border.color: border
        Column {
            id: metricCardContent
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: spacingLg
            spacing: spacingSm
            Text { text: metricCard.title; color: textSecondary; font.pixelSize: textSizeCaption; font.bold: true }
            Text {
                width: parent.width
                text: metricCard.value
                color: textPrimary
                // Long prose drops a size so it stays readable when wrapped.
                font.pixelSize: metricCard.value.length > 28 ? 14 : 18
                font.bold: true
                wrapMode: Text.WordWrap
                maximumLineCount: 3
                elide: Text.ElideRight
            }
            Rectangle { width: 28; height: 3; radius: 2; color: metricCard.accentColor }
        }
        MouseArea {
            anchors.fill: parent
            hoverEnabled: parent.helpText.length > 0
            cursorShape: parent.helpText.length > 0 ? Qt.WhatsThisCursor : Qt.ArrowCursor
            ToolTip.visible: parent.helpText.length > 0 && containsMouse
            ToolTip.text: parent.helpText
            ToolTip.delay: 300
        }
    }

    component AppLogo: Item {
        id: appLogo
        property int size: 38
        implicitWidth: size
        implicitHeight: size
        readonly property real markCx: size * 0.5
        readonly property real markCy: size * 0.46
        readonly property real ringRadius: size * 0.23
        readonly property real ringStroke: size * 0.09

        Rectangle {
            width: appLogo.size
            height: appLogo.size * 0.62
            radius: appLogo.size * 0.26
            color: accent
            anchors.top: parent.top
        }
        Rectangle {
            width: appLogo.size * 0.72
            height: appLogo.size * 0.72
            radius: appLogo.size * 0.16
            color: accent
            rotation: 45
            anchors.horizontalCenter: parent.horizontalCenter
            y: appLogo.size * 0.32
        }
        Canvas {
            id: ringCanvas
            anchors.fill: parent
            renderStrategy: Canvas.Immediate
            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                ctx.lineWidth = appLogo.ringStroke
                ctx.strokeStyle = "#09110e"
                ctx.lineCap = "round"
                ctx.beginPath()
                ctx.arc(appLogo.markCx, appLogo.markCy, appLogo.ringRadius,
                         40 * Math.PI / 180, 320 * Math.PI / 180, false)
                ctx.stroke()
            }
            Component.onCompleted: requestPaint()
        }
        Rectangle {
            width: Math.max(1.1, appLogo.ringStroke * 0.55)
            height: appLogo.ringRadius * 2.5
            radius: width / 2
            color: "#09110e"
            x: appLogo.markCx - appLogo.ringRadius * 0.34 - width / 2
            y: appLogo.markCy - height / 2
        }
        Rectangle {
            width: Math.max(1.1, appLogo.ringStroke * 0.55)
            height: appLogo.ringRadius * 2.5
            radius: width / 2
            color: "#09110e"
            x: appLogo.markCx + appLogo.ringRadius * 0.34 - width / 2
            y: appLogo.markCy - height / 2
        }
    }

    // Animated "something is happening" marker. A static "Running..." label
    // left users unsure whether the app had actually started working.
    // A value the reader has to reproduce somewhere else - a price, a grid
    // count, a threshold. Elide rules these out as TextEdit (which has no
    // elide), so copying is a click rather than a drag-select.
    // A detail line in a fixed-height row. The row cannot grow, so a long
    // sentence can only be cut - and several of these are the only explanation
    // of what a checkbox is about to delete. Hovering shows the whole thing.
    component ElidedDetail: Text {
        id: elidedDetail
        color: textSecondary
        font.pixelSize: 10
        elide: Text.ElideRight
        MouseArea {
            anchors.fill: parent
            enabled: elidedDetail.truncated
            hoverEnabled: true
            acceptedButtons: Qt.NoButton
            cursorShape: Qt.ArrowCursor
            ToolTip.visible: containsMouse && elidedDetail.truncated
            ToolTip.text: elidedDetail.text
            ToolTip.delay: 300
            ToolTip.timeout: 12000
        }
    }

    component CopyableValue: Text {
        id: copyableValue
        property string value: ""
        text: value || "-"
        color: textPrimary
        elide: Text.ElideRight
        MouseArea {
            anchors.fill: parent
            enabled: copyableValue.value !== ""
            cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
            hoverEnabled: true
            onClicked: appController.copyValue(copyableValue.value)
            ToolTip.visible: containsMouse && enabled
            ToolTip.text: appController.appText.click_to_copy_tooltip
        }
    }

    component BusyDots: Row {
        id: busyDots
        property color dotColor: accent
        property int dotSize: 5
        spacing: 3
        visible: true
        Repeater {
            model: 3
            delegate: Rectangle {
                required property int index
                width: busyDots.dotSize
                height: busyDots.dotSize
                radius: width / 2
                color: busyDots.dotColor
                opacity: 0.25
                SequentialAnimation on opacity {
                    running: busyDots.visible
                    loops: Animation.Infinite
                    PauseAnimation { duration: index * 160 }
                    NumberAnimation { to: 1.0; duration: 240 }
                    NumberAnimation { to: 0.25; duration: 240 }
                    PauseAnimation { duration: (2 - index) * 160 }
                }
            }
        }
    }

    component StatusPill: Rectangle {
        id: statusPill
        required property string label
        property string tone: "neutral"
        implicitWidth: pillLabel.implicitWidth + spacingLg * 2
        implicitHeight: pillLabel.implicitHeight + spacingSm * 1.6
        radius: radiusPill
        color: tone === "success" ? accentSoft
            : tone === "warning" ? warningSoft
            : tone === "danger" ? dangerSoft
            : panelRaised
        border.color: tone === "success" ? accent
            : tone === "warning" ? warning
            : tone === "danger" ? danger
            : border
        Text {
            id: pillLabel
            anchors.centerIn: parent
            text: statusPill.label
            color: statusPill.tone === "success" ? accent
                : statusPill.tone === "warning" ? warning
                : statusPill.tone === "danger" ? danger
                : textSecondary
            font.pixelSize: textSizeCaption
            font.bold: true
            elide: Text.ElideRight
        }
    }

    component SectionCard: Rectangle {
        default property alias content: cardContent.children
        property alias contentSpacing: cardContent.spacing
        implicitHeight: cardContent.implicitHeight + spacingXl * 2
        Layout.fillWidth: true
        radius: radiusMd
        color: panel
        border.color: border
        ColumnLayout {
            id: cardContent
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: spacingXl
            spacing: spacingMd
        }
    }
}
