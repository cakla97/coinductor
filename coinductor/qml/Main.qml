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
    Material.theme: Material.Dark
    Material.primary: "#36c98f"
    Material.accent: "#36c98f"
    Material.background: "#171d24"
    Material.foreground: "#f2f5f7"
    font.pixelSize: 14

    property color panel: "#171d24"
    property color panelRaised: "#1d252e"
    property color border: "#2a3540"
    property color textPrimary: "#f2f5f7"
    property color textSecondary: "#9ba8b5"
    property color accent: "#36c98f"
    property color warning: "#f1b84b"
    property string toastText: ""
    property int wizardStep: 0
    property bool profileChoicesEdited: false
    property string fundingCurrency: "USDC"
    property var activeGuide: ({})
    property var activeActionPlanItem: ({})
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
    property var styleOptions: [
        { label: "Conservative", value: "CONSERVATIVE" },
        { label: "Balanced", value: "BALANCED" },
        { label: "Active", value: "ACTIVE" }
    ]
    property var automationOptions: [
        { label: "Recommendations only", value: "RECOMMEND_ONLY" },
        { label: "Guarded automation", value: "GUARDED_AUTOMATION" }
    ]
    property var cadenceOptions: [
        { label: "Weekly", value: "WEEKLY" },
        { label: "Twice weekly", value: "TWICE_WEEKLY" },
        { label: "Daily", value: "DAILY" },
        { label: "Manual / irregular", value: "MANUAL" }
    ]
    property var drawdownOptions: [
        { label: "Low - 10%", value: 10 },
        { label: "Medium - 15%", value: 15 },
        { label: "High - 20%", value: 20 }
    ]
    property var budgetOptions: [
        { label: "Auto", value: 0 },
        { label: "250", value: 250 },
        { label: "500", value: 500 },
        { label: "1,000", value: 1000 },
        { label: "2,000", value: 2000 },
        { label: "10,000", value: 10000 },
        { label: "25,000", value: 25000 }
    ]

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
            return appController.hasCompletedRealAnalysis ? "Enable preview" : "Run read-only analysis"
        if (appController.safetyStageCode === "PREVIEW_ONLY" && !appController.hasReadyLivePreview)
            return "Prepare trade preview"
        if ((appController.safetyStageCode === "PREVIEW_ONLY" || appController.safetyStageCode === "ARMED")
                && appController.liveTradingCheckStatus !== "Verified")
            return "Verify live API permissions"
        if (appController.safetyStageCode === "PREVIEW_ONLY")
            return "Arm guarded actions"
        if (appController.safetyStageCode === "ARMED")
            return "Enable live submit"
        return "Open Action Plan"
    }

    function runSafetyNextAction() {
        if (appController.safetyStageCode === "SETUP" && !appController.hasCompletedRealAnalysis) {
            runDialog.open()
        } else if (appController.safetyStageCode === "SETUP") {
            openSafetyStageConfirmation("PREVIEW_ONLY", "Enable mainnet preview")
        } else if (appController.safetyStageCode === "PREVIEW_ONLY" && !appController.hasReadyLivePreview) {
            appController.prepareTradePreview()
        } else if ((appController.safetyStageCode === "PREVIEW_ONLY" || appController.safetyStageCode === "ARMED")
                   && appController.liveTradingCheckStatus !== "Verified") {
            appController.checkBinanceLiveTrading()
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
    }

    function styleHelp(value) {
        if (value === "CONSERVATIVE")
            return "Coinductor protects more capital, prefers smaller suggestions, keeps more reserve, and is less likely to recommend active trades."
        if (value === "ACTIVE")
            return "Coinductor can surface more frequent opportunities, but deterministic risk limits, protected assets, and confirmations still apply."
        return "Balanced keeps the default middle ground: useful recommendations without pushing the portfolio into aggressive automation."
    }

    function automationHelp(value) {
        if (value === "GUARDED_AUTOMATION")
            return "Coinductor may prepare guarded workflows after checks pass. It still cannot bypass limits, confirmations, stop-loss rules, or safety stages."
        return "Coinductor will explain and recommend actions, but you decide what to do. This is the safest starting mode."
    }

    function cadenceHelp(value) {
        if (value === "DAILY")
            return "Best when you want closer monitoring and are willing to open Coinductor often."
        if (value === "WEEKLY")
            return "Best for passive portfolio management with fewer interventions."
        if (value === "MANUAL")
            return "Coinductor assumes irregular runs and will avoid workflows that require frequent check-ins."
        return "A practical middle ground for active but not daily portfolio review."
    }

    function drawdownHelp(value) {
        if (value <= 10)
            return "Low comfort means Coinductor should keep suggestions conservative and preserve more dry powder."
        if (value >= 20)
            return "High comfort allows more growth-oriented recommendations, but this is not a guarantee or a hard stop-loss."
        return "Medium comfort is the default: risk-aware without making the portfolio completely passive."
    }

    function budgetHelp(value) {
        if (appController.onboardingPath !== "FIRST_PORTFOLIO")
            return "Optional context only: your existing Binance holdings define what Coinductor manages, not this number. Leave it on Auto unless you plan to add fresh capital."
        if (value === 0)
            return "Auto means Coinductor will not assume fresh capital. It will use discovered balances and conservative defaults until real funding is known."
        return "Starting budget is the approximate operating capital Coinductor uses for first-portfolio planning and funding recommendations."
    }

    function botHelp(enabled) {
        return enabled
            ? "Binance bot recommendations lets Coinductor prepare Grid/Rebalancing parameters for manual setup where Binance has no public creation API."
            : "Bot recommendations stay hidden unless you later enable them in your profile."
    }

    function spotTradeHelp(enabled) {
        return enabled
            ? "Guarded spot trades means Coinductor may prepare live trade workflows only after deterministic checks and confirmations."
            : "Spot trades remain recommendations only. This is safer for the first setup pass."
    }

    function markProfileEdited() {
        profileChoicesEdited = true
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

    function wizardStepContentHeight() {
        if (wizardStep === 2)
            return 720
        if (wizardStep === 3)
            return 840
        if (wizardStep === 4)
            return 900
        if (wizardStep === 5) {
            var exchangeSteps = 64 + appController.exchangeOnboardingSteps.length * 34
            var basket = appController.onboardingPath === "FIRST_PORTFOLIO"
                ? 140 + appController.firstPortfolioAllocation.length * 28 + appController.firstPortfolioSteps.length * 34
                : 0
            return 700 + exchangeSteps + basket
        }
        return 640
    }

    function openWizardAtStep(stepIndex) {
        wizardStep = stepIndex
        appController.openOnboardingWizard()
    }

    Item {
        anchors.fill: parent
        visible: appController.onboardingWizardVisible

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
                    Rectangle {
                        Layout.preferredWidth: 46
                        Layout.preferredHeight: 46
                        radius: 9
                        color: accent
                        Text {
                            anchors.centerIn: parent
                            text: "C"
                            color: "#09110e"
                            font.pixelSize: 26
                            font.bold: true
                        }
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
                    radius: 7
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
                        Rectangle {
                            Layout.preferredWidth: 150
                            Layout.preferredHeight: 30
                            radius: 5
                            color: "#17372d"
                            border.color: accent
                            Text {
                                anchors.centerIn: parent
                                text: appController.wizardText.local_first_badge
                                color: accent
                                font.pixelSize: 11
                                font.bold: true
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredHeight: Math.max(window.wizardStepContentHeight(), window.height - 190)
                    Layout.minimumHeight: 420
                    spacing: 16

                    Rectangle {
                        Layout.preferredWidth: 210
                        Layout.fillHeight: true
                        radius: 7
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
                                    radius: 6
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
                                            radius: 10
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
                        radius: 7
                        color: panel
                        border.color: border
                        ColumnLayout {
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
                                        radius: 7
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
                                        radius: 7
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
                                            radius: 7
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
                                            radius: 7
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
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Text { text: appController.wizardText.field_automation; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                            ComboBox { id: wizardAutomation; Layout.fillWidth: true; model: window.automationOptions; textRole: "label"; valueRole: "value"; onActivated: window.markProfileEdited() }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Text { text: appController.wizardText.field_review_rhythm; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                            ComboBox { id: wizardCadence; Layout.fillWidth: true; model: window.cadenceOptions; textRole: "label"; valueRole: "value"; currentIndex: 1; onActivated: window.markProfileEdited() }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Text { text: appController.wizardText.field_language_region; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                            ComboBox { id: wizardLocale; Layout.fillWidth: true; model: ["en-US", "es-ES", "cs-CZ", "pt-BR"]; onActivated: window.markProfileEdited() }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Text { text: appController.wizardText.field_operating_currency; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                            Rectangle {
                                                Layout.fillWidth: true
                                                Layout.preferredHeight: 56
                                                radius: 5
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
                                            ComboBox { id: wizardDrawdown; Layout.fillWidth: true; model: window.drawdownOptions; textRole: "label"; valueRole: "value"; currentIndex: 1; onActivated: window.markProfileEdited() }
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
                                        Layout.fillWidth: true
                                        radius: 6
                                        color: panelRaised
                                        Layout.preferredHeight: 128
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 12
                                            spacing: 5
                                            Text { text: appController.wizardText.current_selection_title; color: textPrimary; font.pixelSize: 13; font.bold: true }
                                            Text {
                                                Layout.fillWidth: true
                                                visible: !window.profileChoicesEdited && !appController.userProfileConfigured
                                                text: appController.wizardText.current_selection_placeholder
                                                color: textSecondary
                                                font.pixelSize: 12
                                                wrapMode: Text.WordWrap
                                            }
                                            Text { Layout.fillWidth: true; visible: window.profileChoicesEdited || appController.userProfileConfigured; text: wizardStyle.currentText + " management style - " + window.styleHelp(wizardStyle.currentValue); color: textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                            Text { Layout.fillWidth: true; visible: window.profileChoicesEdited || appController.userProfileConfigured; text: wizardAutomation.currentText + " - " + window.automationHelp(wizardAutomation.currentValue); color: textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                            Text { Layout.fillWidth: true; visible: window.profileChoicesEdited || appController.userProfileConfigured; text: wizardCadence.currentText + " review rhythm - " + window.cadenceHelp(wizardCadence.currentValue); color: textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap }
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
                                        Layout.preferredHeight: 104
                                        radius: 7
                                        color: panelRaised
                                        border.color: border
                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 16
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
                                    GridLayout {
                                        id: aiProviderGrid
                                        Layout.fillWidth: true
                                        columns: width < 760 ? 1 : 2
                                        columnSpacing: 12
                                        rowSpacing: 12
                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: (appController.localAiModelRecommendations.length > 0 ? (aiProviderGrid.columns === 1 ? 760 : 690) : 460) + (appController.localAiDiscoveredModels.length > 0 ? 50 + Math.min(appController.localAiDiscoveredModels.length, 4) * 40 : (appController.discoveringAiModels || appController.localAiDiscoveryStatus === "BLOCK" ? 90 : 0))
                                            Layout.minimumHeight: (appController.localAiModelRecommendations.length > 0 ? 660 : 430) + (appController.localAiDiscoveredModels.length > 0 || appController.discoveringAiModels || appController.localAiDiscoveryStatus === "BLOCK" ? 90 : 0)
                                            radius: 7
                                            color: panelRaised
                                            border.color: border
                                            clip: true
                                            ColumnLayout {
                                                anchors.fill: parent
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
                                                        text: appController.aiProviderBaseUrl.length > 0 ? appController.aiProviderBaseUrl : "http://127.0.0.1:11434/v1"
                                                    }
                                                }
                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 8
                                                    TextField {
                                                        id: localAiModel
                                                        Layout.fillWidth: true
                                                        placeholderText: "Text model, e.g. qwen3:14b"
                                                        text: appController.aiTextModel.length > 0 ? appController.aiTextModel : "qwen3:14b"
                                                    }
                                                    TextField {
                                                        id: localAiVisionModel
                                                        Layout.fillWidth: true
                                                        placeholderText: "Vision model (optional), e.g. qwen3-vl:8b"
                                                        text: appController.aiVisionModel
                                                    }
                                                }
                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 8
                                                    Button {
                                                        text: "Save local AI"
                                                        onClicked: {
                                                            appController.saveLocalAiProvider(localAiBaseUrl.text, localAiModel.text, localAiVisionModel.text)
                                                            window.showToast("Local AI settings saved")
                                                        }
                                                    }
                                                    Button {
                                                        text: "Scan hardware"
                                                        onClicked: appController.scanLocalAiHardware()
                                                    }
                                                    Button {
                                                        text: appController.discoveringAiModels ? "Detecting..." : "Detect installed models"
                                                        enabled: !appController.discoveringAiModels
                                                        onClicked: appController.discoverLocalAiModels(localAiBaseUrl.text)
                                                    }
                                                    Item { Layout.fillWidth: true }
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
                                                    visible: appController.localAiDiscoveredModels.length > 0 || appController.discoveringAiModels || appController.localAiDiscoveryStatus === "BLOCK"
                                                    Layout.fillWidth: true
                                                    Layout.bottomMargin: 10
                                                    Layout.minimumHeight: 90
                                                    Layout.preferredHeight: appController.localAiDiscoveredModels.length > 0 ? 60 + Math.min(appController.localAiDiscoveredModels.length, 4) * 40 : 90
                                                    radius: 6
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
                                                            color: appController.localAiDiscoveryStatus === "BLOCK" ? warning : textSecondary
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
                                                                height: 34
                                                                radius: 5
                                                                color: "#141a21"
                                                                border.color: border
                                                                RowLayout {
                                                                    anchors.fill: parent
                                                                    anchors.leftMargin: 10
                                                                    anchors.rightMargin: 6
                                                                    spacing: 6
                                                                    Text { Layout.fillWidth: true; text: modelData; color: accent; font.pixelSize: 11; elide: Text.ElideRight }
                                                                    Button {
                                                                        text: "Use as text"
                                                                        font.pixelSize: 9
                                                                        implicitHeight: 24
                                                                        onClicked: localAiModel.text = modelData
                                                                    }
                                                                    Button {
                                                                        text: "Use as vision"
                                                                        font.pixelSize: 9
                                                                        implicitHeight: 24
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
                                                    radius: 6
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
                                                                radius: 5
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
                                            radius: 7
                                            color: panelRaised
                                            border.color: border
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
                                                    TextField { id: cloudAiBaseUrl; Layout.fillWidth: true; placeholderText: "https://api.openai.com/v1" }
                                                }
                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 8
                                                    TextField { id: cloudAiModel; Layout.fillWidth: true; placeholderText: "Text model" }
                                                    TextField { id: cloudAiVisionModel; Layout.fillWidth: true; placeholderText: "Vision model (optional)" }
                                                }
                                                TextField { id: cloudAiKey; Layout.fillWidth: true; placeholderText: "API key"; echoMode: TextInput.Password }
                                                Button {
                                                    text: "Save cloud AI"
                                                    enabled: cloudAiBaseUrl.text.trim().length > 0 && cloudAiModel.text.trim().length > 0 && cloudAiKey.text.trim().length > 0
                                                    onClicked: {
                                                        appController.saveCloudAiProvider(cloudAiBaseUrl.text, cloudAiModel.text, cloudAiVisionModel.text, cloudAiKey.text)
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
                                        radius: 7
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
                                        radius: 7
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
                                        Rectangle {
                                            Layout.preferredWidth: 120
                                            Layout.preferredHeight: 32
                                            radius: 5
                                            color: appController.binanceConnectionStatus === "Connected" ? "#17372d"
                                                : appController.binanceConnectionStatus === "Blocked" ? "#3a2226" : panelRaised
                                            border.color: appController.binanceConnectionStatus === "Connected" ? accent
                                                : appController.binanceConnectionStatus === "Blocked" ? "#ee6b6e" : border
                                            Text {
                                                anchors.centerIn: parent
                                                text: appController.binanceConnectionStatus
                                                color: appController.binanceConnectionStatus === "Connected" ? accent
                                                    : appController.binanceConnectionStatus === "Blocked" ? "#ee6b6e" : textSecondary
                                                font.pixelSize: 11
                                                font.bold: true
                                            }
                                        }
                                    }
                                    Text { Layout.fillWidth: true; text: appController.binanceConnectionDetail; color: textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 232
                                        radius: 7
                                        color: panelRaised
                                        border.color: border
                                        ColumnLayout {
                                            anchors.fill: parent
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
                                                Rectangle {
                                                    Layout.preferredWidth: 120
                                                    Layout.preferredHeight: 32
                                                    radius: 5
                                                    color: appController.testnetCheckStatus === "Verified" ? "#17372d"
                                                        : appController.testnetCheckStatus === "Blocked" ? "#3a2226" : panel
                                                    border.color: appController.testnetCheckStatus === "Verified" ? accent
                                                        : appController.testnetCheckStatus === "Blocked" ? "#ee6b6e" : border
                                                    Text {
                                                        anchors.centerIn: parent
                                                        text: appController.testnetCheckStatus
                                                        color: appController.testnetCheckStatus === "Verified" ? accent
                                                            : appController.testnetCheckStatus === "Blocked" ? "#ee6b6e" : textSecondary
                                                        font.pixelSize: 11
                                                        font.bold: true
                                                    }
                                                }
                                            }
                                            Text { Layout.fillWidth: true; text: appController.testnetCheckDetail; color: textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                        }
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 72
                                        radius: 7
                                        color: panelRaised
                                        border.color: border
                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 14
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
                                        Layout.preferredHeight: appController.onboardingPath === "FIRST_PORTFOLIO" ? 300 : 190
                                        radius: 7
                                        color: panelRaised
                                        border.color: border
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 16
                                            spacing: 8
                                            Text { text: appController.onboardingPath === "FIRST_PORTFOLIO" ? "First portfolio plan" : "Existing portfolio next step"; color: textPrimary; font.pixelSize: 15; font.bold: true }
                                            Text {
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
                                                    Text { Layout.fillWidth: true; text: modelData.detail; color: textSecondary; font.pixelSize: 10; elide: Text.ElideRight }
                                                }
                                            }
                                        }
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 64 + appController.exchangeOnboardingSteps.length * 34
                                        radius: 7
                                        color: panelRaised
                                        border.color: border
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 16
                                            spacing: 6
                                            Text { text: "Next steps outside Coinductor"; color: textPrimary; font.pixelSize: 15; font.bold: true }
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
                                                    Text { Layout.fillWidth: true; text: modelData.detail; color: textSecondary; font.pixelSize: 10; elide: Text.ElideRight }
                                                }
                                            }
                                        }
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 140 + appController.firstPortfolioAllocation.length * 28 + appController.firstPortfolioSteps.length * 34
                                        radius: 7
                                        color: panelRaised
                                        border.color: border
                                        visible: appController.onboardingPath === "FIRST_PORTFOLIO"
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 16
                                            spacing: 8
                                            Text { text: "Suggested first basket (manual purchase)"; color: textPrimary; font.pixelSize: 15; font.bold: true }
                                            Text {
                                                Layout.fillWidth: true
                                                text: "Weights match your chosen management style. Buying is always manual on Binance; Coinductor never places this order for you."
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
                                                    Text { Layout.fillWidth: true; text: modelData.detail; color: textSecondary; font.pixelSize: 10; elide: Text.ElideRight }
                                                }
                                            }
                                        }
                                    }
                                    ListView {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 160
                                        interactive: false
                                        spacing: 6
                                        model: appController.readinessSteps
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
                                                spacing: 10
                                                Text { Layout.preferredWidth: 140; text: modelData.name; color: textPrimary; font.pixelSize: 11; font.bold: true }
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
                    radius: 7
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
            Layout.preferredWidth: 232
            Layout.fillHeight: true
            color: "#12171d"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 8

                RowLayout {
                    Layout.bottomMargin: 26
                    spacing: 12
                    Rectangle {
                        width: 38
                        height: 38
                        radius: 8
                        color: accent
                        Text {
                            anchors.centerIn: parent
                            text: "C"
                            color: "#09110e"
                            font.pixelSize: 22
                            font.bold: true
                        }
                    }
                    Column {
                        Text { text: "Coinductor"; color: textPrimary; font.pixelSize: 19; font.bold: true }
                        Text { text: "Portfolio automation"; color: textSecondary; font.pixelSize: 11 }
                    }
                }

                Repeater {
                    id: navigationRepeater
                    model: window.navigationItems
                    delegate: Rectangle {
                        required property var modelData
                        required property int index
                        Layout.fillWidth: true
                        Layout.preferredHeight: 42
                        radius: 6
                        color: appController.currentPage === modelData.page ? panelRaised : "transparent"
                        border.color: appController.currentPage === modelData.page ? border : "transparent"
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left
                            anchors.leftMargin: 14
                            text: modelData.label
                            color: appController.currentPage === modelData.page ? textPrimary : textSecondary
                            font.pixelSize: 14
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
                    radius: 6
                    color: panel
                    border.color: appController.safetyAllowsLiveSubmit ? accent
                        : appController.safetyAllowsLivePreview ? warning : border
                    Column {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 6
                        Text { text: "SAFETY"; color: textSecondary; font.pixelSize: 10; font.bold: true }
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
                            text: appController.safetyAllowsLiveSubmit ? "Live guarded" : appController.safetyAllowsLivePreview ? "Preview only" : "No exchange changes"
                            color: textSecondary
                            font.pixelSize: 10
                            elide: Text.ElideRight
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 72
                    radius: 6
                    color: panel
                    border.color: border
                    Column {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 6
                        Text { text: "BINANCE"; color: textSecondary; font.pixelSize: 10; font.bold: true }
                        Row {
                            spacing: 8
                            Rectangle {
                                width: 8
                                height: 8
                                radius: 4
                                color: appController.binanceConnectionStatus === "Connected" ? accent
                                    : appController.binanceConnectionStatus === "Checking" ? warning
                                    : appController.binanceConnectionStatus === "Blocked" ? "#ee6b6e" : textSecondary
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

            ColumnLayout {
                x: 28
                y: 28
                width: Math.max(window.width - 288, 692)
                spacing: 18

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: finishSetupBannerColumn.implicitHeight + 28
                    visible: appController.userProfileConfigured
                        && (appController.binanceConnectionStatus !== "Connected" || appController.aiProviderBaseUrl.length === 0)
                    radius: 8
                    color: "#3a3020"
                    border.color: warning
                    ColumnLayout {
                        id: finishSetupBannerColumn
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 14
                        spacing: 8
                        Text { text: "Finish setup"; color: warning; font.pixelSize: 14; font.bold: true }
                        RowLayout {
                            Layout.fillWidth: true
                            visible: appController.binanceConnectionStatus !== "Connected"
                            spacing: 12
                            Text {
                                Layout.fillWidth: true
                                text: "Binance read-only access is not connected yet. Portfolio analysis needs it to show real data instead of examples."
                                color: textPrimary
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                            }
                            Button { text: "Complete Binance setup"; onClicked: window.openWizardAtStep(4) }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            visible: appController.aiProviderBaseUrl.length === 0
                            spacing: 12
                            Text {
                                Layout.fillWidth: true
                                text: "AI assistant is not configured yet. This step is optional; Coinductor works without it."
                                color: textSecondary
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                            }
                            Button { text: "Set up AI (optional)"; onClicked: window.openWizardAtStep(3) }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text { text: "Portfolio Overview"; color: textPrimary; font.pixelSize: 26; font.bold: true }
                        Text {
                            text: "Deterministic analysis with guarded execution"
                            color: textSecondary
                            font.pixelSize: 13
                        }
                    }
                    Button {
                        text: appController.busy ? "Running..." : "Run analysis"
                        enabled: !appController.busy
                        onClicked: runDialog.open()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: overviewSafetyContent.implicitHeight + 32
                    radius: 7
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
                                Text { text: "Safety & readiness"; color: textPrimary; font.pixelSize: 15; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: appController.safetyStageCode === "SETUP"
                                        ? appController.hasCompletedRealAnalysis
                                            ? "Real analysis is available. Continue in Live Actions when you want to enable mainnet preview."
                                            : "Setup is complete and exchange-changing actions are locked. Start with a real read-only analysis."
                                        : appController.safetyStageCode === "PREVIEW_ONLY" && !appController.hasReadyLivePreview
                                            ? "Mainnet preview is enabled. Wait for a valid BUY setup and review its preview before arming guarded actions."
                                            : appController.safetyDetail
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                            }
                            Rectangle {
                                Layout.preferredWidth: 126
                                Layout.preferredHeight: 30
                                radius: 5
                                color: appController.safetyAllowsLiveSubmit ? "#17372d" : appController.safetyAllowsLivePreview ? "#3a3020" : panelRaised
                                border.color: appController.safetyAllowsLiveSubmit ? accent : appController.safetyAllowsLivePreview ? warning : border
                                Text {
                                    anchors.centerIn: parent
                                    text: appController.safetyStage
                                    color: appController.safetyAllowsLiveSubmit ? accent : appController.safetyAllowsLivePreview ? warning : textSecondary
                                    font.pixelSize: 10
                                    font.bold: true
                                }
                            }
                            Button {
                                text: appController.safetyStageCode === "SETUP" && !appController.hasCompletedRealAnalysis
                                    ? "Run analysis"
                                    : "Open Live Actions"
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
                            text: "This stage never places an order by itself. See Live Actions for the full safety-stage controls and confirmation gates."
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
                    MetricCard { title: "Portfolio"; value: appController.portfolioValue; accentColor: accent; helpText: "Total value of everything Coinductor tracks, including Spot, Flexible Earn, and Locked balances." }
                    MetricCard { title: "Liquid"; value: appController.liquidValue; accentColor: "#5aa9e6"; helpText: "Value in Spot or Flexible Earn that could be used without waiting." }
                    MetricCard { title: "Locked"; value: appController.lockedValue; accentColor: warning; helpText: "Value in Locked Earn or otherwise not immediately available." }
                    MetricCard { title: "Risk gate"; value: appController.riskState; accentColor: "#d66b75"; helpText: "Whether the deterministic risk engine currently approves a new trade. When it does not, the reason is shown here instead of \"Approved\"." }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 148
                    radius: 7
                    color: panel
                    border.color: border
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 8
                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: "Latest decision"; color: textSecondary; font.pixelSize: 12; font.bold: true }
                            Item { Layout.fillWidth: true }
                            Rectangle {
                                width: decisionText.implicitWidth + 22
                                height: 28
                                radius: 5
                                color: appController.decision === "HOLD" ? "#3a3020" : "#17372d"
                                Text {
                                    id: decisionText
                                    anchors.centerIn: parent
                                    text: appController.decision
                                    color: appController.decision === "HOLD" ? warning : accent
                                    font.pixelSize: 12
                                    font.bold: true
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.WhatsThisCursor
                                    ToolTip.visible: containsMouse
                                    ToolTip.text: "HOLD means no trade is currently recommended. Any other decision type is explained below and detailed further in Action Plan."
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
                            text: "Open detailed report"
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
                        radius: 7
                        color: panel
                        border.color: border
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 18
                            Text { text: "Recommended actions"; color: textPrimary; font.pixelSize: 16; font.bold: true }
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
                                    radius: 5
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
                        radius: 7
                        color: panel
                        border.color: border
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 18
                            Text { text: "AI summary"; color: textPrimary; font.pixelSize: 16; font.bold: true }
                            Text {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                text: appController.aiSummary
                                color: textSecondary
                                font.pixelSize: 13
                                wrapMode: Text.WordWrap
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
                width: Math.max(window.width - 288, 692)
                spacing: 18

                Text { text: "Portfolio"; color: textPrimary; font.pixelSize: 26; font.bold: true }
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: "Latest real-run valuation, asset roles, and liquidity location"
                        color: textSecondary
                        font.pixelSize: 14
                    }
                    ComboBox {
                        Layout.preferredWidth: 190
                        Layout.preferredHeight: 34
                        model: [
                            { label: "Value high to low", value: "VALUE_DESC" },
                            { label: "Value low to high", value: "VALUE_ASC" },
                            { label: "Asset A-Z", value: "ASSET_ASC" },
                            { label: "Policy A-Z", value: "ROLE_ASC" }
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
                    radius: 6
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 14
                        anchors.rightMargin: 14
                        spacing: 12
                        Text { Layout.preferredWidth: 70; text: "ASSET"; color: textSecondary; font.pixelSize: 10; font.bold: true }
                        Text { Layout.preferredWidth: 210; text: "POLICY"; color: textSecondary; font.pixelSize: 11; font.bold: true }
                        Text { Layout.preferredWidth: 120; text: "VALUE"; color: textSecondary; font.pixelSize: 10; font.bold: true }
                        Text { Layout.preferredWidth: 75; text: "SHARE"; color: textSecondary; font.pixelSize: 10; font.bold: true }
                        Text { Layout.fillWidth: true; text: "LIQUIDITY"; color: textSecondary; font.pixelSize: 10; font.bold: true }
                        Text { Layout.preferredWidth: 120; text: "SOURCE"; color: textSecondary; font.pixelSize: 10; font.bold: true }
                    }
                }

                ListView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.max(420, contentHeight)
                    spacing: 6
                    model: appController.portfolioAssets
                    delegate: Rectangle {
                        required property var modelData
                        width: ListView.view.width
                        height: 76
                        radius: 6
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
                                        window.showToast("Policy for " + modelData.asset + " changed to " + currentText)
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
                                Text { text: "Spot " + modelData.spot + "   Flexible " + modelData.flexible; color: textSecondary; font.pixelSize: 11 }
                                Text { text: "Locked " + modelData.locked; color: textSecondary; font.pixelSize: 11 }
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
                width: Math.max(window.width - 288, 692)
                spacing: 18

                RowLayout {
                    width: parent.width
                    Layout.fillWidth: true
                    spacing: 16
                    ColumnLayout {
                        spacing: 4
                        Text { text: "Action Plan"; color: textPrimary; font.pixelSize: 26; font.bold: true }
                        Text { text: "Latest trade, Grid, and Rebalancing decisions in one review list."; color: textSecondary; font.pixelSize: 13 }
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        text: "Open detailed report"
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
                    radius: 7
                    color: panel
                    border.color: border
                    ColumnLayout {
                        id: firstPortfolioDeploymentContent
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        Text { text: "First portfolio deployment"; color: textPrimary; font.pixelSize: 16; font.bold: true }
                        Text {
                            Layout.fillWidth: true
                            text: "Staged, guarded purchase of your starting basket. Each tranche still passes bankroll, stop-loss, and confirmation checks; only market-timing (consensus/RSI) is intentionally skipped, since this executes a plan you already chose."
                            color: textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Repeater {
                            model: appController.firstPortfolioAllocation
                            delegate: Rectangle {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.preferredHeight: 40
                                radius: 5
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
                                        text: "Testnet " + window.firstPortfolioProgressCount(modelData.asset, "TESTNET") + "/" + firstPortfolioTranchesInput.value
                                            + "  ·  Mainnet " + window.firstPortfolioProgressCount(modelData.asset, "MAINNET") + "/" + firstPortfolioTranchesInput.value
                                        color: textSecondary
                                        font.pixelSize: 11
                                    }
                                    Button {
                                        text: "Deploy"
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
                            Text { text: "Total USDC budget for the whole basket:"; color: textSecondary; font.pixelSize: 11 }
                            TextField { id: firstPortfolioBudgetInput; Layout.preferredWidth: 120; placeholderText: "e.g. 400" }
                            Text { text: "Tranches:"; color: textSecondary; font.pixelSize: 11 }
                            SpinBox { id: firstPortfolioTranchesInput; from: 1; to: 10; value: 3 }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "Enter the real USDC amount you intend to deploy here — the wizard's planned budget may be in a different currency and is not auto-converted."
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
                        Text { text: "Ready - can be confirmed now"; color: textSecondary; font.pixelSize: 11 }
                    }
                    Row {
                        spacing: 6
                        Rectangle { width: 10; height: 10; radius: 5; color: warning; anchors.verticalCenter: parent.verticalCenter }
                        Text { text: "Watch - conditions not met yet"; color: textSecondary; font.pixelSize: 11 }
                    }
                    Row {
                        spacing: 6
                        Rectangle { width: 10; height: 10; radius: 5; color: textSecondary; anchors.verticalCenter: parent.verticalCenter }
                        Text { text: "Other - review-only, e.g. HOLD or blocked"; color: textSecondary; font.pixelSize: 11 }
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
                        radius: 7
                        color: panel
                        border.color: modelData.tone === "ready" ? accent : warning
                        ColumnLayout {
                            id: actionPlanCardContent
                            anchors.fill: parent
                            anchors.margins: 18
                            spacing: 10
                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: modelData.title; color: textPrimary; font.pixelSize: 17; font.bold: true }
                                Item { Layout.fillWidth: true }
                                Rectangle {
                                    Layout.preferredWidth: Math.max(92, actionStatus.implicitWidth + 20)
                                    Layout.preferredHeight: 28
                                    radius: 5
                                    color: modelData.tone === "ready" ? "#17372d" : modelData.tone === "watch" ? "#3a3020" : "#26313b"
                                    border.color: modelData.tone === "ready" ? accent : warning
                                    Text {
                                        id: actionStatus
                                        anchors.centerIn: parent
                                        text: modelData.status
                                        color: modelData.tone === "ready" ? accent : modelData.tone === "watch" ? warning : textSecondary
                                        font.pixelSize: 11
                                        font.bold: true
                                    }
                                }
                            }
                            GridLayout {
                                Layout.fillWidth: true
                                columns: 4
                                columnSpacing: 20
                                rowSpacing: 8
                                Repeater {
                                    model: modelData.parameters || []
                                    delegate: ColumnLayout {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        spacing: 2
                                        Text { text: modelData.label; color: textSecondary; font.pixelSize: 10; font.bold: true }
                                        Text {
                                            Layout.fillWidth: true
                                            text: modelData.value || "-"
                                            color: textPrimary
                                            font.pixelSize: 12
                                            elide: Text.ElideRight
                                        }
                                    }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: tradeLifecycleSummary.implicitHeight + 22
                                visible: modelData.liveLifecycle !== undefined && modelData.liveLifecycle !== null
                                radius: 6
                                color: panelRaised
                                border.color: modelData.liveLifecycle && modelData.liveLifecycle.tone === "ready" ? accent : border
                                RowLayout {
                                    id: tradeLifecycleSummary
                                    anchors.fill: parent
                                    anchors.margins: 11
                                    spacing: 12
                                    Text {
                                        text: "Last live trade"
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
                                    Layout.preferredWidth: 170
                                    text: modelData.primaryLabel || "Review"
                                    enabled: modelData.actionCode !== "NONE"
                                    onClicked: {
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
                width: Math.max(window.width - 288, 692)
                spacing: 18

                RowLayout {
                    Layout.fillWidth: true
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text { text: "Active Strategies"; color: textPrimary; font.pixelSize: 26; font.bold: true }
                        Text { Layout.fillWidth: true; text: appController.activeStrategiesSummary; color: textSecondary; font.pixelSize: 13; wrapMode: Text.WordWrap }
                    }
                    Button {
                        text: appController.busy ? "Refreshing..." : "Refresh monitoring"
                        enabled: !appController.busy
                        onClicked: appController.refreshActiveStrategies()
                    }
                    Button {
                        text: "Register active bot"
                        enabled: !appController.busy
                        onClicked: strategyRegistrationDialog.open()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 190
                    visible: appController.activeStrategies.length === 0
                    radius: 7
                    color: panel
                    border.color: border
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 10
                        Text {
                            text: appController.registeredStrategyCount > 0 ? "Monitoring evaluation pending" : "No active bots registered"
                            color: textPrimary
                            font.pixelSize: 17
                            font.bold: true
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.registeredStrategyCount > 0
                                  ? "The bot is stored locally, but no fresh evaluation is available yet. Refresh monitoring after checking your Binance connection."
                                  : "Create a Grid or Rebalancing Bot in Binance from a READY Action Plan recommendation, then register its real parameters in Coinductor for periodic monitoring."
                            color: textSecondary
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                        }
                        Item { Layout.fillHeight: true }
                        RowLayout {
                            Layout.fillWidth: true
                            Item { Layout.fillWidth: true }
                            Button { text: "Register active bot"; onClicked: strategyRegistrationDialog.open() }
                            Button { text: "Open Action Plan"; onClicked: appController.setCurrentPage(3) }
                        }
                    }
                }

                Component {
                    id: nextReviewPanelComponent
                    Rectangle {
                    implicitHeight: nextReviewContent.implicitHeight + 36
                    visible: Object.keys(appController.nextReview).length > 0
                    radius: 7
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
                                Text { text: "Next review"; color: textPrimary; font.pixelSize: 17; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: appController.nextReview.headline || ""
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                            }
                            Rectangle {
                                Layout.preferredWidth: Math.max(140, nextReviewStatus.implicitWidth + 24)
                                Layout.preferredHeight: 30
                                radius: 5
                                color: appController.nextReview.tone === "blocked" ? "#3a3020" : panelRaised
                                border.color: appController.nextReview.tone === "blocked" ? warning : border
                                Text {
                                    id: nextReviewStatus
                                    anchors.centerIn: parent
                                    text: appController.nextReview.status || "Not scheduled"
                                    color: appController.nextReview.tone === "blocked" ? warning : textPrimary
                                    font.pixelSize: 11
                                    font.bold: true
                                }
                            }
                        }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: width < 760 ? 1 : 3
                            columnSpacing: 24
                            rowSpacing: 8
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Suggested timing"; color: textSecondary; font.pixelSize: 10; font.bold: true }
                                Text { Layout.fillWidth: true; text: appController.nextReview.timing || "Not available"; color: textPrimary; font.pixelSize: 12; wrapMode: Text.WordWrap }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Scheduled from latest run"; color: textSecondary; font.pixelSize: 10; font.bold: true }
                                Text { Layout.fillWidth: true; text: appController.nextReview.scheduledAt || "Not available"; color: textPrimary; font.pixelSize: 12; wrapMode: Text.WordWrap }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Profile review rhythm"; color: textSecondary; font.pixelSize: 10; font.bold: true }
                                Text { Layout.fillWidth: true; text: appController.nextReview.profileCadence || "Not configured"; color: textPrimary; font.pixelSize: 12; wrapMode: Text.WordWrap }
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
                                Text { text: "Run earlier if"; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: "These are optional triggers for refreshing the analysis before the scheduled review. You do not need to make them happen."
                                    color: textSecondary
                                    font.pixelSize: 10
                                    wrapMode: Text.WordWrap
                                }
                                Repeater {
                                    model: appController.nextReview.triggers || []
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
                                Text { text: "Resolve before rerunning"; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: "These blockers need a manual or funding change. Repeating the same analysis alone will not remove them."
                                    color: textSecondary
                                    font.pixelSize: 10
                                    wrapMode: Text.WordWrap
                                }
                                Text {
                                    Layout.fillWidth: true
                                    visible: (appController.nextReview.manualSteps || []).length === 0
                                    text: "No manual prerequisite. A fresh run can reassess current market conditions."
                                    color: textSecondary
                                    font.pixelSize: 11
                                    wrapMode: Text.WordWrap
                                }
                                Repeater {
                                    model: appController.nextReview.manualSteps || []
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
                                text: "Based on deterministic output from run " + (appController.nextReview.sourceRun || "-") + ". AI commentary does not control this timing."
                                color: textSecondary
                                font.pixelSize: 10
                                wrapMode: Text.WordWrap
                            }
                            Button {
                                text: "Run analysis now"
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
                        radius: 7
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
                                    Text { text: modelData.type + "  |  Binance ID " + modelData.botId; color: textSecondary; font.pixelSize: 11 }
                                }
                                Rectangle {
                                    Layout.preferredWidth: Math.max(110, strategyHealth.implicitWidth + 22)
                                    Layout.preferredHeight: 30
                                    radius: 5
                                    color: modelData.tone === "ready" ? "#17372d" : modelData.tone === "watch" ? "#3a3020" : "#3a2226"
                                    border.color: modelData.tone === "ready" ? accent : warning
                                    Text {
                                        id: strategyHealth
                                        anchors.centerIn: parent
                                        text: modelData.health
                                        color: modelData.tone === "ready" ? accent : warning
                                        font.pixelSize: 11
                                        font.bold: true
                                    }
                                }
                            }
                            Text { text: modelData.state; color: modelData.tone === "ready" ? accent : warning; font.pixelSize: 11; font.bold: true }
                            GridLayout {
                                Layout.fillWidth: true
                                columns: 4
                                columnSpacing: 18
                                rowSpacing: 8
                                Repeater {
                                    model: modelData.parameters || []
                                    delegate: ColumnLayout {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        spacing: 2
                                        Text { text: modelData.label; color: textSecondary; font.pixelSize: 10; font.bold: true }
                                        Text { Layout.fillWidth: true; text: modelData.value || "-"; color: textPrimary; font.pixelSize: 11; elide: Text.ElideRight }
                                    }
                                }
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 12
                                Text { Layout.fillWidth: true; text: modelData.recommendation; color: textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap; maximumLineCount: 3; elide: Text.ElideRight }
                                Button {
                                    Layout.preferredWidth: 150
                                    text: "View details"
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
                width: Math.max(window.width - 288, 692)
                spacing: 18

                Text { text: "Run History"; color: textPrimary; font.pixelSize: 26; font.bold: true }
                Text { text: "The latest 30 analytical runs"; color: textSecondary; font.pixelSize: 13 }
                Text {
                    Layout.fillWidth: true
                    text: "REAL runs read your live Binance account and are the ones behind Action Plan and Active Strategies. MOCK runs use example data for trying the app and never touch your real portfolio. This is a read-only log; to act on a decision, use Action Plan."
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
                        radius: 6
                        color: panel
                        border.color: border
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 14
                            spacing: 14
                            ColumnLayout {
                                Layout.preferredWidth: 85
                                Text { text: "RUN " + modelData.runId; color: textPrimary; font.pixelSize: 13; font.bold: true }
                                Text { text: modelData.dataMode; color: modelData.dataMode === "REAL" ? accent : warning; font.pixelSize: 10; font.bold: true }
                            }
                            ColumnLayout {
                                Layout.preferredWidth: 145
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

                Text { text: "AI Assistant"; color: textPrimary; font.pixelSize: 26; font.bold: true }
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: "Read-only help | Context: " + appController.assistantContextPage
                        color: textSecondary
                        font.pixelSize: 14
                    }
                    Rectangle {
                        Layout.preferredWidth: 280
                        Layout.minimumWidth: 180
                        Layout.preferredHeight: 34
                        radius: 6
                        color: panel
                        border.color: border
                        Text {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            verticalAlignment: Text.AlignVCenter
                            text: "Active AI: " + appController.aiProviderSummary
                            color: textSecondary
                            font.pixelSize: 12
                            elide: Text.ElideRight
                        }
                    }
                    Button {
                        text: "History"
                        onClicked: assistantHistoryDialog.open()
                    }
                    Button {
                        text: "New chat"
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
                            radius: 7
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
                    radius: 7
                    color: panelRaised
                    border.color: accent

                    ColumnLayout {
                        id: assistantActionContent
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 14
                        spacing: 8
                        Text { Layout.fillWidth: true; text: appController.assistantPendingAction.title || "Proposed app action"; color: textPrimary; font.pixelSize: 15; font.bold: true; wrapMode: Text.WordWrap }
                        Text { Layout.fillWidth: true; text: appController.assistantPendingAction.description || ""; color: textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap }
                        RowLayout {
                            Layout.alignment: Qt.AlignRight
                            spacing: 8
                            Button { text: "Dismiss"; onClicked: appController.dismissAssistantAction() }
                            Button { text: appController.assistantPendingAction.confirmLabel || "Confirm"; highlighted: true; onClicked: appController.confirmAssistantAction() }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 92
                    visible: Object.keys(appController.assistantAttachment).length > 0
                    radius: 7
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
                                text: appController.assistantAttachment.name || "Attached image"
                                color: textPrimary
                                font.pixelSize: 13
                                font.bold: true
                                elide: Text.ElideMiddle
                            }
                            Text {
                                Layout.fillWidth: true
                                text: appController.assistantVisionAvailable
                                      ? "The active AI supports image input. The screenshot will be sent with this message. You can paste another screenshot with Ctrl+V."
                                      : appController.assistantVisionDetail
                                color: appController.assistantVisionAvailable ? textSecondary : warning
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                        }
                        Button {
                            text: "Remove"
                            enabled: !appController.assistantBusy
                            onClicked: appController.clearAssistantAttachment()
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    Button {
                        text: "Attach image"
                        enabled: !appController.assistantBusy
                        onClicked: assistantImageDialog.open()
                    }
                    TextField {
                        id: assistantInput
                        Layout.fillWidth: true
                        placeholderText: "Ask about the latest run, portfolio, risk, Grid..."
                        enabled: !appController.assistantBusy
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
                    Button {
                        text: "Send"
                        enabled: !appController.assistantBusy
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

            ColumnLayout {
                x: 28
                y: 28
                width: Math.max(window.width - 288, 692)
                spacing: 18

                Text { text: "Help & Guides"; color: textPrimary; font.pixelSize: 26; font.bold: true }
                Text {
                    Layout.fillWidth: true
                    text: "Step-by-step local guides for setup, safety, AI providers, Binance API access, and portfolio roles."
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
                            radius: 7
                            color: panel
                            border.color: border
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 16
                                spacing: 8
                                RowLayout {
                                    Layout.fillWidth: true
                                    Text { Layout.fillWidth: true; text: modelData.title; color: textPrimary; font.pixelSize: 16; font.bold: true; elide: Text.ElideRight }
                                    Rectangle {
                                        Layout.preferredWidth: 92
                                        Layout.preferredHeight: 24
                                        radius: 5
                                        color: panelRaised
                                        border.color: border
                                        Text { anchors.centerIn: parent; text: modelData.section; color: textSecondary; font.pixelSize: 10; font.bold: true }
                                    }
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
                                    text: "Open guide"
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

            GridLayout {
                x: 28
                y: 28
                width: Math.max(window.width - 288, 692)
                columns: 1
                rowSpacing: 18
                Text { Layout.row: 0; text: "Live Actions"; color: textPrimary; font.pixelSize: 26; font.bold: true }
                RowLayout {
                    Layout.row: 1
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: "Prepare guarded previews and manage live trading safety gates. Results open in Action Plan after each run."
                        color: textSecondary
                        font.pixelSize: 13
                        wrapMode: Text.WordWrap
                    }
                    Button {
                        text: "Open live API guide"
                        onClicked: window.openGuide("binance-live-api")
                    }
                    Button {
                        text: "Refresh checks"
                        onClicked: appController.refreshSetup()
                    }
                }

                Rectangle {
                    Layout.row: 3
                    Layout.fillWidth: true
                    Layout.preferredHeight: 330
                    radius: 7
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
                                Text { text: "Guarded Action Center"; color: textPrimary; font.pixelSize: 16; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: "Choose what kind of output you want. Coinductor runs the required analysis, then opens Action Plan with an updated summary."
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                            }
                            Rectangle {
                                Layout.preferredWidth: 118
                                Layout.preferredHeight: 30
                                radius: 5
                                color: "#3a3020"
                                border.color: warning
                                Text {
                                    anchors.centerIn: parent
                                    text: appController.safetyStage
                                    color: appController.safetyAllowsLiveSubmit ? accent : warning
                                    font.pixelSize: 10
                                    font.bold: true
                                }
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
                                Text { text: "Trade preview"; color: textPrimary; font.pixelSize: 14; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 54
                                    text: "Prepare a guarded trade recommendation and open Action Plan with the latest decision."
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                                Button {
                                    text: appController.busy ? "Running..." : "Prepare trade preview"
                                    enabled: !appController.busy
                                    onClicked: appController.prepareTradePreview()
                                }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                Text { text: "Bot plan"; color: textPrimary; font.pixelSize: 14; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 54
                                    text: "Refresh Grid and Rebalancing recommendations and open Action Plan with setup details."
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                                Button {
                                    text: appController.busy ? "Running..." : "Prepare bot plan"
                                    enabled: !appController.busy
                                    onClicked: appController.prepareBotPlan()
                                }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                Text { text: "Custom analysis"; color: textPrimary; font.pixelSize: 14; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 54
                                    text: "Open the same configurable run dialog used by Overview when you want custom parameters."
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                                Button {
                                    text: "Open run dialog"
                                    enabled: !appController.busy
                                    onClicked: runDialog.open()
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.safetyAllowsLiveSubmit
                                ? "Guarded submission is available only inside a READY Action Plan item and still requires a fresh validation plus per-action confirmation."
                                : "Analysis and recommendations do not submit orders. Live actions remain locked by the current Safety stage."
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
                    radius: 7
                    color: panel
                    border.color: appController.safetyAllowsLiveSubmit ? accent : border
                    ColumnLayout {
                        id: safetyStageContent
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 12
                        RowLayout {
                            Layout.fillWidth: true
                            Text { Layout.fillWidth: true; text: "Safety stage"; color: textPrimary; font.pixelSize: 16; font.bold: true }
                            Text { text: appController.safetyStage; color: appController.safetyAllowsLiveSubmit ? accent : warning; font.pixelSize: 12; font.bold: true }
                        }
                        Text { Layout.fillWidth: true; text: appController.safetyDetail; color: textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: liveApiSummaryContent.implicitHeight + 24
                            radius: 6
                            color: panelRaised
                            border.color: appController.liveTradingCheckStatus === "Verified" ? accent : border
                            RowLayout {
                                id: liveApiSummaryContent
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 12
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Text { text: "Live API"; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                    Text {
                                        Layout.fillWidth: true
                                        text: (appController.liveTradingKeyStatus === "PASS" ? "Credentials configured" : "Credentials not configured")
                                            + "  |  " + (appController.liveTradingCheckStatus === "Verified" ? "Permissions verified this session" : "Permissions not verified this session")
                                        color: textSecondary
                                        font.pixelSize: 11
                                        wrapMode: Text.WordWrap
                                    }
                                }
                                Rectangle {
                                    Layout.preferredWidth: 92
                                    Layout.preferredHeight: 28
                                    radius: 5
                                    color: appController.liveTradingCheckStatus === "Verified" ? "#17372d" : "#3a3020"
                                    border.color: appController.liveTradingCheckStatus === "Verified" ? accent : warning
                                    Text {
                                        anchors.centerIn: parent
                                        text: appController.liveTradingCheckStatus === "Verified" ? "VERIFIED" : appController.liveTradingKeyStatus === "PASS" ? "CONFIGURED" : "LOCKED"
                                        color: appController.liveTradingCheckStatus === "Verified" ? accent : warning
                                        font.pixelSize: 10
                                        font.bold: true
                                    }
                                }
                                Button {
                                    text: "Manage live API"
                                    onClicked: liveApiManagerDialog.open()
                                }
                                Button {
                                    text: appController.checkingLiveTrading ? "Verifying..." : "Verify permissions"
                                    enabled: appController.liveTradingKeyStatus === "PASS" && !appController.checkingLiveTrading
                                    onClicked: appController.checkBinanceLiveTrading()
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.safetyStageCode === "SETUP" && !appController.hasCompletedRealAnalysis
                                ? "Next prerequisite: complete a real read-only analysis."
                                : appController.safetyStageCode === "PREVIEW_ONLY" && !appController.hasReadyLivePreview
                                    ? "Next prerequisite: prepare and review a ready trade preview. Hold and blocked results do not unlock arming."
                                    : (appController.safetyStageCode === "PREVIEW_ONLY" || appController.safetyStageCode === "ARMED") && appController.liveTradingCheckStatus !== "Verified"
                                        ? "Next prerequisite: verify the live API permissions for this app session."
                                        : "All prerequisites for the next Safety stage are available."
                            color: warning
                            font.pixelSize: 11
                            font.bold: true
                            wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                Layout.fillWidth: true
                                text: "Recommended next step"
                                color: textSecondary
                                font.pixelSize: 11
                                font.bold: true
                            }
                            Button {
                                text: window.safetyNextActionLabel()
                                highlighted: true
                                enabled: !appController.busy && !appController.checkingLiveTrading
                                onClicked: window.runSafetyNextAction()
                            }
                        }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: 3
                            columnSpacing: 12
                            Rectangle {
                                Layout.fillWidth: true; Layout.preferredHeight: 72; radius: 6; color: panelRaised; border.color: appController.safetyAllowsLivePreview ? accent : border
                                Column {
                                    anchors.fill: parent; anchors.margins: 10; spacing: 4
                                    Text { text: "1. Preview"; color: textPrimary; font.bold: true }
                                    Text { width: parent.width; text: "Mainnet validation without submit"; color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true; Layout.preferredHeight: 72; radius: 6; color: panelRaised; border.color: appController.safetyStageCode === "ARMED" || appController.safetyAllowsLiveSubmit ? accent : border
                                Column {
                                    anchors.fill: parent; anchors.margins: 10; spacing: 4
                                    Text { text: "2. Armed"; color: textPrimary; font.bold: true }
                                    Text { width: parent.width; text: "Verified key, submit still locked"; color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true; Layout.preferredHeight: 72; radius: 6; color: panelRaised; border.color: appController.safetyAllowsLiveSubmit ? accent : border
                                Column {
                                    anchors.fill: parent; anchors.margins: 10; spacing: 4
                                    Text { text: "3. Live enabled"; color: textPrimary; font.bold: true }
                                    Text { width: parent.width; text: "Guarded submit can be confirmed"; color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap }
                                }
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10
                            Button {
                                text: "Enable preview"
                                enabled: appController.safetyStageCode === "SETUP" && appController.hasCompletedRealAnalysis
                                onClicked: window.openSafetyStageConfirmation("PREVIEW_ONLY", "Enable mainnet preview")
                            }
                            Button {
                                text: "Arm guarded actions"
                                enabled: appController.safetyStageCode === "PREVIEW_ONLY"
                                    && appController.hasReadyLivePreview
                                    && appController.liveTradingCheckStatus === "Verified"
                                onClicked: window.openSafetyStageConfirmation("ARMED", "Arm guarded actions")
                            }
                            Button {
                                text: "Enable live submit"
                                enabled: appController.safetyStageCode === "ARMED" && appController.liveTradingCheckStatus === "Verified"
                                onClicked: window.openSafetyStageConfirmation("LIVE_ENABLED", "Enable guarded live submit")
                            }
                            Item { Layout.fillWidth: true }
                            Button {
                                text: "Lock live submit"
                                enabled: appController.safetyStageCode === "ARMED" || appController.safetyAllowsLiveSubmit
                                onClicked: appController.lockLiveSubmit()
                            }
                        }
                        Text { Layout.fillWidth: true; text: "Stage changes are local safety controls and never place an order. Every live trade or OCO protection still needs its own confirmation. If your public IP is dynamic, keep live execution locked unless the Binance whitelist is current."; color: warning; font.pixelSize: 11; font.bold: true; wrapMode: Text.WordWrap }
                    }
                }
                Item { Layout.row: 4; Layout.fillWidth: true; Layout.preferredHeight: 44 }
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: appController.currentPage === 8

            ColumnLayout {
                x: 28
                y: 28
                width: Math.max(window.width - 288, 692)
                spacing: 18
                Text { text: "Settings"; color: textPrimary; font.pixelSize: 26; font.bold: true }
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: "Manage local configuration, privacy controls, and readiness checks."
                        color: textSecondary
                        font.pixelSize: 13
                    }
                    Button {
                        text: "Setup wizard"
                        onClicked: appController.openOnboardingWizard()
                    }
                    Button {
                        text: "Replay app tour"
                        onClicked: appController.startAppTour()
                    }
                    Button {
                        text: "Refresh checks"
                        onClicked: appController.refreshSetup()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 104
                    radius: 7
                    color: panel
                    border.color: border
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 16
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            Text { text: "Binance read-only connection"; color: textPrimary; font.pixelSize: 16; font.bold: true }
                            Text {
                                Layout.fillWidth: true
                                text: appController.binanceConnectionDetail
                                color: textSecondary
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                            }
                        }
                        Rectangle {
                            Layout.preferredWidth: 96
                            Layout.preferredHeight: 30
                            radius: 5
                            color: appController.binanceConnectionStatus === "Connected" ? "#17372d"
                                : appController.binanceConnectionStatus === "Checking" ? "#3a3020"
                                : appController.binanceConnectionStatus === "Blocked" ? "#3a2226" : panelRaised
                            border.color: appController.binanceConnectionStatus === "Connected" ? accent
                                : appController.binanceConnectionStatus === "Checking" ? warning
                                : appController.binanceConnectionStatus === "Blocked" ? "#ee6b6e" : border
                            Text {
                                anchors.centerIn: parent
                                text: appController.binanceConnectionStatus
                                color: appController.binanceConnectionStatus === "Connected" ? accent
                                    : appController.binanceConnectionStatus === "Checking" ? warning
                                    : appController.binanceConnectionStatus === "Blocked" ? "#ee6b6e" : textSecondary
                                font.pixelSize: 10
                                font.bold: true
                            }
                        }
                        Button {
                            text: appController.checkingConnection ? "Checking..." : "Check read-only access"
                            enabled: !appController.checkingConnection
                            onClicked: appController.checkBinanceReadOnly()
                        }
                    }
                }


                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 330
                    radius: 7
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
                                Text { text: "AI provider"; color: textPrimary; font.pixelSize: 16; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: appController.aiProviderSummary
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                            }
                            Rectangle {
                                Layout.preferredWidth: 96
                                Layout.preferredHeight: 30
                                radius: 5
                                color: appController.aiProviderHealthStatus === "Connected" ? "#17372d"
                                    : appController.aiProviderHealthStatus === "Checking" ? "#3a3020"
                                    : appController.aiProviderHealthStatus === "Blocked" ? "#3a2226" : panelRaised
                                border.color: appController.aiProviderHealthStatus === "Connected" ? accent
                                    : appController.aiProviderHealthStatus === "Checking" ? warning
                                    : appController.aiProviderHealthStatus === "Blocked" ? "#ee6b6e" : border
                                Text {
                                    anchors.centerIn: parent
                                    text: appController.aiProviderHealthStatus
                                    color: appController.aiProviderHealthStatus === "Connected" ? accent
                                        : appController.aiProviderHealthStatus === "Checking" ? warning
                                        : appController.aiProviderHealthStatus === "Blocked" ? "#ee6b6e" : textSecondary
                                    font.pixelSize: 10
                                    font.bold: true
                                }
                            }
                            Button {
                                text: appController.checkingAiProvider ? "Checking..." : "Check AI provider"
                                enabled: !appController.checkingAiProvider
                                onClicked: appController.checkAiProvider()
                            }
                            Button {
                                text: "Configure AI models"
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
                                        Text { Layout.fillWidth: true; text: modelData.detail; color: textSecondary; font.pixelSize: 10; elide: Text.ElideRight }
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
                                        Text { width: parent.width; text: modelData.detail; color: textSecondary; font.pixelSize: 10; elide: Text.ElideRight }
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 285
                    radius: 7
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
                                Text { text: "Onboarding profile"; color: textPrimary; font.pixelSize: 16; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: appController.userProfileSummary
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                            }
                            Button {
                                text: "Open wizard"
                                onClicked: appController.openOnboardingWizard()
                            }
                            Button {
                                text: "Use safe defaults"
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
                                    Text { Layout.fillWidth: true; text: modelData.detail; color: textSecondary; font.pixelSize: 10; elide: Text.ElideRight }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 335
                    radius: 7
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
                                Text { text: "Privacy & Data"; color: textPrimary; font.pixelSize: 16; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: "Coinductor is local-first: it reads only what is needed for portfolio management and keeps project data on this computer unless you opt into an external AI provider."
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                            }
                            Button {
                                text: "Reset onboarding"
                                enabled: appController.userProfileConfigured
                                onClicked: deleteProfileDialog.open()
                            }
                            Button {
                                text: "Delete local data"
                                onClicked: localDataResetDialog.open()
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
                                    Text { Layout.fillWidth: true; text: modelData.detail; color: textSecondary; font.pixelSize: 10; elide: Text.ElideRight }
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "Reset onboarding only changes preferences. Delete local data permanently removes the local files you select; it never touches anything outside this project folder."
                            color: textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "System readiness"; color: textPrimary; font.pixelSize: 16; font.bold: true }
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
                            Text { Layout.fillWidth: true; text: modelData.detail; color: textSecondary; font.pixelSize: 11; elide: Text.ElideRight }
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
                    radius: 7
                    color: panel
                    border.color: border
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 9
                        Text { text: "Safety baseline"; color: textPrimary; font.pixelSize: 16; font.bold: true }
                        Text { text: "Checks only report whether secrets exist; they never display or transmit them."; color: textSecondary; font.pixelSize: 12 }
                        Text { text: "Selecting an onboarding path does not place orders or change configuration."; color: textSecondary; font.pixelSize: 12 }
                        Text { text: "Live execution retains separate preview, limits, and explicit confirmation gates."; color: textSecondary; font.pixelSize: 12 }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 190
                    radius: 7
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
                                Text { text: "Safety stage"; color: textPrimary; font.pixelSize: 16; font.bold: true }
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
                                    text: "Stage: " + appController.safetyStage
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
                                    Text { Layout.fillWidth: true; text: modelData.detail; color: textSecondary; font.pixelSize: 10; elide: Text.ElideRight }
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
        title: "Register an active Binance bot"
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
                    text: "This records a bot that you already created in Binance. Coinductor does not create, stop, or modify the Binance bot from this form."
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
                    TabButton { text: "Spot Grid" }
                    TabButton { text: "Rebalancing" }
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
                                text: "Copy the exact active Grid parameters from Binance. Price range, entry, TP/SL, and creation time are used to identify review conditions."
                                color: textSecondary
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                            }
                            Button {
                                text: "Import latest recommendation"
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
                                    strategyRegistrationDialog.importNotice = "Imported proposed values from run " + suggestion.sourceRun + ". Compare every field with the bot you actually created in Binance; missing values remain blank."
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
                                Text { text: "Local name *"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridName; Layout.fillWidth: true; placeholderText: "Example: BTC range bot" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Binance bot ID"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridBotId; Layout.fillWidth: true; placeholderText: "Optional, but recommended" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Symbol *"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                ComboBox { id: gridSymbol; Layout.fillWidth: true; model: appController.gridRegistrationSymbols }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Grid spacing *"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                ComboBox { id: gridType; Layout.fillWidth: true; model: ["ARITHMETIC", "GEOMETRIC"] }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Lower price *"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridRangeLow; Layout.fillWidth: true; placeholderText: "Lower range shown in Binance" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Upper price *"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridRangeHigh; Layout.fillWidth: true; placeholderText: "Upper range shown in Binance" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Number of grids *"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridCount; Layout.fillWidth: true; placeholderText: "Example: 10" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Investment in USDC *"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridInvestment; Layout.fillWidth: true; placeholderText: "Exact allocated amount" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Entry price *"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridEntryPrice; Layout.fillWidth: true; placeholderText: "Price when the bot was created" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Created at"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridCreatedAt; Layout.fillWidth: true; placeholderText: "Optional ISO date, e.g. 2026-07-13T12:00:00+02:00" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Stop loss *"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridStopLoss; Layout.fillWidth: true; placeholderText: "Must be below the lower range" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Take profit *"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: gridTakeProfit; Layout.fillWidth: true; placeholderText: "Must be above the upper range" }
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: "Local notes"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                            TextField { id: gridNotes; Layout.fillWidth: true; placeholderText: "Optional context for future reviews" }
                        }
                        CheckBox {
                            id: gridVerified
                            Layout.fillWidth: true
                            text: "I verified that these values match the currently active bot in Binance."
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Item { Layout.fillWidth: true }
                            Button {
                                text: appController.busy ? "Working..." : "Register and refresh monitoring"
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
                                text: "Use comma-separated values in the same order for assets, target weights, and entry prices. Target weights must total exactly 100%."
                                color: textSecondary
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                            }
                            Button {
                                text: "Import latest recommendation"
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
                                    strategyRegistrationDialog.importNotice = "Imported proposed values from run " + suggestion.sourceRun + ". Compare every field with Binance; entry prices stay blank if the latest run did not contain all required markets."
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "Allowed assets: " + appController.rebalancingRegistrationAssets.join(", ")
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
                                Text { text: "Local name *"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: rebalancingName; Layout.fillWidth: true; placeholderText: "Example: Core portfolio basket" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Binance bot ID"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: rebalancingBotId; Layout.fillWidth: true; placeholderText: "Optional, but recommended" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Assets *"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: rebalancingAssets; Layout.fillWidth: true; placeholderText: "BTC, ETH, SOL" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Target weights (%) *"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: rebalancingWeights; Layout.fillWidth: true; placeholderText: "50, 25, 25" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Entry prices in USDC *"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: rebalancingEntryPrices; Layout.fillWidth: true; placeholderText: "One price for each asset" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Investment in USDC *"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: rebalancingInvestment; Layout.fillWidth: true; placeholderText: "Exact allocated amount" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Rebalance threshold (%) *"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: rebalancingThreshold; Layout.fillWidth: true; placeholderText: "Example: 10" }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                Text { text: "Created at"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                                TextField { id: rebalancingCreatedAt; Layout.fillWidth: true; placeholderText: "Optional ISO date; empty means now" }
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: "Local notes"; color: textPrimary; font.pixelSize: 11; font.bold: true }
                            TextField { id: rebalancingNotes; Layout.fillWidth: true; placeholderText: "Optional context for future reviews" }
                        }
                        CheckBox {
                            id: rebalancingVerified
                            Layout.fillWidth: true
                            text: "I verified that these values match the currently active bot in Binance."
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Item { Layout.fillWidth: true }
                            Button {
                                text: appController.busy ? "Working..." : "Register and refresh monitoring"
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
                text: "Close"
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
                        text: "QUICK TOUR  " + (appController.appTourStep + 1) + " / " + appController.appTourStepCount
                        color: accent
                        font.pixelSize: 10
                        font.bold: true
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        text: "Skip tour"
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
                        text: "Back"
                        enabled: appController.appTourStep > 0
                        onClicked: appController.previousAppTourStep()
                    }
                    Button {
                        text: appController.appTourStep === appController.appTourStepCount - 1 ? "Finish" : "Next"
                        highlighted: true
                        onClicked: appController.nextAppTourStep()
                    }
                }
            }
        }
    }

    Dialog {
        id: activeStrategyDetailDialog
        title: activeStrategyItem.name || "Active strategy"
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
                        Text { text: (activeStrategyItem.type || "") + "  |  Binance ID " + (activeStrategyItem.botId || "-"); color: textSecondary; font.pixelSize: 12 }
                    }
                    Text { text: activeStrategyItem.health || "Unknown"; color: activeStrategyItem.tone === "ready" ? accent : warning; font.pixelSize: 12; font.bold: true }
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
                        model: activeStrategyItem.parameters || []
                        delegate: Rectangle {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 68
                            radius: 6
                            color: panelRaised
                            border.color: border
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 3
                                Text { text: modelData.label; color: textSecondary; font.pixelSize: 10; font.bold: true }
                                Text { Layout.fillWidth: true; text: modelData.value || "-"; color: textPrimary; font.pixelSize: 12; elide: Text.ElideRight }
                            }
                        }
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: strategyMonitorNote.implicitHeight + 24
                    radius: 7
                    color: "#3a3020"
                    border.color: warning
                    Text {
                        id: strategyMonitorNote
                        anchors.fill: parent
                        anchors.margins: 12
                        text: "Monitoring compares registered parameters with locally collected market data. Verify profit, fills, and final bot status directly in Binance before changing or stopping a bot."
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
                    Text { text: "Update local monitoring status"; color: textPrimary; font.pixelSize: 16; font.bold: true }
                    Text {
                        Layout.fillWidth: true
                        text: "First pause, stop, or close the bot in Binance. This control only updates Coinductor's local monitoring record and never sends a command to Binance."
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
                            Text { text: "New local status"; color: textSecondary; font.pixelSize: 10; font.bold: true }
                            ComboBox {
                                id: strategyStatusChoice
                                Layout.fillWidth: true
                                model: ["Paused", "Stopped", "Closed"]
                            }
                        }
                        Button {
                            text: appController.busy ? "Working..." : "Update local record"
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
                        text: "I already applied this status change to the bot in Binance."
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "Paused, Stopped, and Closed records leave active monitoring but remain in the local registry and historical run data."
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
        title: "Manage live trading API"
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
                    text: "Store and verify the separate Binance key used by guarded live actions. Managing credentials never changes the Safety stage or submits an order."
                    color: textSecondary
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: liveApiWarningText.implicitHeight + 24
                    radius: 7
                    color: "#3a3020"
                    border.color: warning
                    Text {
                        id: liveApiWarningText
                        anchors.fill: parent
                        anchors.margins: 12
                        text: "Use a separate key with Reading + Spot trading only, trusted-IP restriction enabled, and withdrawals disabled. Dynamic-IP users should keep live execution locked unless they can maintain the whitelist."
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
                        text: "Open setup guide"
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
                    CheckBox { id: liveSeparateKey; text: "This key is separate from the read-only key"; checked: false }
                    CheckBox { id: liveIpRestricted; text: "Trusted-IP restriction is enabled in Binance"; checked: false }
                    CheckBox { id: liveNoWithdrawals; text: "Withdrawals and transfer permissions remain disabled"; checked: false }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Button {
                        text: "Save live trading key"
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
                            window.showToast("Live trading key saved locally; submit remains locked")
                        }
                    }
                    Button {
                        text: appController.checkingLiveTrading ? "Checking permissions..." : "Verify permissions"
                        enabled: appController.liveTradingKeyStatus === "PASS" && !appController.checkingLiveTrading
                        onClicked: appController.checkBinanceLiveTrading()
                    }
                    Item { Layout.fillWidth: true }
                    Rectangle {
                        Layout.preferredWidth: 104
                        Layout.preferredHeight: 30
                        radius: 5
                        color: appController.liveTradingCheckStatus === "Verified" ? "#17372d" : "#3a3020"
                        border.color: appController.liveTradingCheckStatus === "Verified" ? accent : warning
                        Text {
                            anchors.centerIn: parent
                            text: appController.liveTradingCheckStatus === "Verified" ? "VERIFIED" : appController.liveTradingKeyStatus === "PASS" ? "CONFIGURED" : "LOCKED"
                            color: appController.liveTradingCheckStatus === "Verified" ? accent : warning
                            font.pixelSize: 10
                            font.bold: true
                        }
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
                    text: "Live submit remains controlled by Safety stage, fresh validation, and a separate confirmation for every trade or OCO action."
                    color: warning
                    font.pixelSize: 11
                    font.bold: true
                    wrapMode: Text.WordWrap
                }
                RowLayout {
                    Layout.fillWidth: true
                    Item { Layout.fillWidth: true }
                    Button { text: "Close"; onClicked: liveApiManagerDialog.close() }
                }
            }
        }
    }

    Dialog {
        id: safetyStageConfirmDialog
        title: "Confirm Safety stage change"
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
                    ? "This enables guarded live submit controls. It does not place an order, but future READY actions can be submitted after their own confirmation."
                    : pendingSafetyTarget === "ARMED"
                        ? "This records that the live API permissions were verified and arms guarded workflows. Live submit remains locked."
                        : "This enables mainnet previews only. No order or exchange-changing action can be submitted."
                color: textSecondary
                font.pixelSize: 13
                wrapMode: Text.WordWrap
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: safetyPhraseRow.implicitHeight + 24
                radius: 7
                color: "#3a3020"
                border.color: warning
                RowLayout {
                    id: safetyPhraseRow
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 12
                    Text {
                        Layout.fillWidth: true
                        text: "Confirmation phrase: " + pendingSafetyPhrase
                        color: warning
                        font.pixelSize: 12
                        font.bold: true
                        wrapMode: Text.WordWrap
                    }
                    Button {
                        text: "Copy phrase"
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
                Button { text: "Cancel"; onClicked: safetyStageConfirmDialog.close() }
                Button {
                    text: "Change Safety stage"
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
        title: activeActionPlanItem.title || "Action detail"
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
                    Rectangle {
                        Layout.preferredWidth: Math.max(96, actionDetailStatus.implicitWidth + 22)
                        Layout.preferredHeight: 30
                        radius: 5
                        color: activeActionPlanItem.tone === "ready" ? "#17372d" : activeActionPlanItem.tone === "watch" ? "#3a3020" : "#26313b"
                        border.color: activeActionPlanItem.tone === "ready" ? accent : warning
                        Text {
                            id: actionDetailStatus
                            anchors.centerIn: parent
                            text: activeActionPlanItem.status || "UNKNOWN"
                            color: activeActionPlanItem.tone === "ready" ? accent : activeActionPlanItem.tone === "watch" ? warning : textSecondary
                            font.pixelSize: 11
                            font.bold: true
                        }
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
                        model: activeActionPlanItem.parameters || []
                        delegate: Rectangle {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 68
                            radius: 6
                            color: panelRaised
                            border.color: border
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 3
                                Text { text: modelData.label; color: textSecondary; font.pixelSize: 10; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.value || "-"
                                    color: textPrimary
                                    font.pixelSize: 13
                                    elide: Text.ElideRight
                                }
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
                        Text { Layout.fillWidth: true; text: "Last live trade"; color: textPrimary; font.pixelSize: 16; font.bold: true }
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
                            model: activeActionPlanItem.liveLifecycle ? activeActionPlanItem.liveLifecycle.lifecycleSteps : []
                            delegate: Rectangle {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.preferredHeight: 76
                                radius: 6
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
                            model: activeActionPlanItem.liveLifecycle ? activeActionPlanItem.liveLifecycle.parameters : []
                            delegate: Rectangle {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.preferredHeight: 64
                                radius: 6
                                color: panelRaised
                                border.color: border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    spacing: 3
                                    Text { text: modelData.label; color: textSecondary; font.pixelSize: 10; font.bold: true }
                                    Text { Layout.fillWidth: true; text: modelData.value || "-"; color: textPrimary; font.pixelSize: 12; elide: Text.ElideRight }
                                }
                            }
                        }
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: actionDetailNote.implicitHeight + 28
                    radius: 7
                    color: "#3a3020"
                    border.color: warning
                    Text {
                        id: actionDetailNote
                        anchors.fill: parent
                        anchors.margins: 12
                        text: activeActionPlanItem.actionCode === "REVIEW_TRADE"
                            ? (activeActionPlanItem.liveLifecycle
                                ? "The current recommendation and the last live trade are separate. Run a fresh analysis to synchronize Binance order and OCO status again."
                                : "Live trade submission is separate from review. It stays locked unless the latest BUY preview, live key, safety stage, and confirmation text all pass.")
                            : activeActionPlanItem.actionCode === "REVIEW_OCO"
                                ? "OCO protection is a separate SELL order pair. Submission requires a READY preview and its own explicit confirmation."
                                : activeActionPlanItem.actionCode === "REVIEW_EARN_REDEEM"
                                    ? "Earn redeem moves funds from Flexible Earn back to Spot so a trade can be funded. Submission requires a READY preview and its own explicit confirmation."
                                : activeActionPlanItem.actionCode === "OPEN_ACTIVE_STRATEGIES"
                                    ? "Coinductor detected a lifecycle condition from locally registered parameters. Verify the real bot state in Binance before updating the local record."
                                : "This dialog is review-only. Manual bot setup remains outside automatic desktop submission."
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
                    radius: 7
                    color: panelRaised
                    border.color: activeActionPlanItem.submitEnabled === true ? accent : border
                    ColumnLayout {
                        id: liveTradeGuardContent
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 8
                        Text {
                            text: activeActionPlanItem.actionCode === "REVIEW_OCO" ? "Guarded position protection"
                                : activeActionPlanItem.actionCode === "REVIEW_EARN_REDEEM" ? "Guarded Earn redeem"
                                : "Guarded live trade"
                            color: textPrimary
                            font.pixelSize: 15
                            font.bold: true
                        }
                        Text {
                            Layout.fillWidth: true
                            text: activeActionPlanItem.submitEnabled === true
                                ? activeActionPlanItem.actionCode === "REVIEW_OCO"
                                    ? "This will run a fresh validation pass and submit the OCO pair only if the position protection preview is still ready."
                                    : activeActionPlanItem.actionCode === "REVIEW_EARN_REDEEM"
                                        ? "This will run a fresh validation pass and redeem from Flexible Earn only if the preview is still ready."
                                        : "This will run a fresh validation pass and submit only if the new mainnet preview is still ready."
                                : (activeActionPlanItem.submitBlockedReason || "Live submit is locked.")
                            color: activeActionPlanItem.submitEnabled === true ? textSecondary : warning
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Item { Layout.fillWidth: true }
                            Button {
                                text: activeActionPlanItem.submitEnabled === true ? activeActionPlanItem.submitLabel : "Locked"
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
                    radius: 7
                    color: panelRaised
                    border.color: border
                    ColumnLayout {
                        id: challengeHoldContent
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 8
                        Text { text: "Challenge this HOLD"; color: textPrimary; font.pixelSize: 15; font.bold: true }
                        Text {
                            Layout.fillWidth: true
                            text: "Request a BUY evaluation for a specific allowed symbol instead of accepting HOLD. This does not bypass any check: bankroll, exposure, consensus/RSI/trend, stop-loss, and live-submit confirmation all still apply and can still reject it."
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
                                text: appController.busy ? "Running..." : "Challenge HOLD"
                                enabled: !appController.busy && appController.manualOverrideSymbols.length > 0
                                onClicked: {
                                    appController.challengeHold(challengeHoldSymbol.currentText)
                                    actionPlanDetailDialog.close()
                                }
                            }
                            Item { Layout.fillWidth: true }
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    visible: activeActionPlanItem.actionCode === "OPEN_ACTIVE_STRATEGIES"
                    Item { Layout.fillWidth: true }
                    Button {
                        text: "Open Active Strategies"
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
        title: "Confirm guarded live trade"
        modal: true
        anchors.centerIn: parent
        width: Math.min(680, window.width - 120)
        standardButtons: Dialog.NoButton

        ColumnLayout {
            width: liveTradeConfirmDialog.width - 48
            spacing: 14
            Text {
                Layout.fillWidth: true
                text: "Coinductor will run a fresh guarded analysis and may submit a mainnet MARKET BUY only if the preview remains ready. This is not a 24/7 process and it will not bypass deterministic limits."
                color: textSecondary
                font.pixelSize: 13
                wrapMode: Text.WordWrap
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: liveTradeConfirmWarning.implicitHeight + 24
                radius: 7
                color: "#3a3020"
                border.color: warning
                Text {
                    id: liveTradeConfirmWarning
                    anchors.fill: parent
                    anchors.margins: 12
                    text: "Type CONFIRM_MAINNET_ORDER exactly. Never use this if Binance trusted-IP restrictions, live key permissions, or funding look wrong."
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
                    text: "Cancel"
                    onClicked: liveTradeConfirmDialog.close()
                }
                Button {
                    text: "Run guarded submit"
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
        title: "Attach a screenshot or image"
        fileMode: PlatformDialogs.FileDialog.OpenFile
        nameFilters: ["Images (*.png *.jpg *.jpeg *.webp)"]
        onAccepted: appController.attachAssistantImage(selectedFile.toString())
    }

    Dialog {
        id: assistantHistoryDialog
        title: "AI chat history"
        modal: true
        anchors.centerIn: parent
        width: Math.min(760, window.width - 96)
        height: Math.min(600, window.height - 96)
        standardButtons: Dialog.Close

        contentItem: ColumnLayout {
            spacing: 12
            Text {
                Layout.fillWidth: true
                text: "Stored locally. The newest 20 conversations are kept."
                color: textSecondary
                font.pixelSize: 12
                wrapMode: Text.WordWrap
            }
            Text {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: appController.assistantHistory.length === 0
                text: "No saved conversations yet. A chat appears here after its first completed answer."
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
                    radius: 7
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
                            Text { text: modelData.contextPage + " | " + modelData.messageCount + " messages | " + modelData.updatedAt; color: textSecondary; font.pixelSize: 10 }
                        }
                        Button {
                            text: "Open"
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
        title: "Confirm OCO position protection"
        modal: true
        anchors.centerIn: parent
        width: Math.min(680, window.width - 120)
        standardButtons: Dialog.NoButton

        ColumnLayout {
            width: ocoConfirmDialog.width - 48
            spacing: 14
            Text {
                Layout.fillWidth: true
                text: "Coinductor will run a fresh mainnet validation and may submit a linked take-profit and stop-loss SELL pair for the open position. Binance keeps this protection active while Coinductor is closed."
                color: textSecondary
                font.pixelSize: 13
                wrapMode: Text.WordWrap
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: ocoConfirmWarning.implicitHeight + 24
                radius: 7
                color: "#3a3020"
                border.color: warning
                Text {
                    id: ocoConfirmWarning
                    anchors.fill: parent
                    anchors.margins: 12
                    text: "Type CONFIRM_MAINNET_OCO exactly. Recheck the quantity, take-profit, stop-loss, trusted IP, and live-key permissions before continuing."
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
                    text: "Cancel"
                    onClicked: ocoConfirmDialog.close()
                }
                Button {
                    text: "Submit OCO protection"
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
        title: "Confirm Earn redeem"
        modal: true
        anchors.centerIn: parent
        width: Math.min(680, window.width - 120)
        standardButtons: Dialog.NoButton

        ColumnLayout {
            width: earnRedeemConfirmDialog.width - 48
            spacing: 14
            Text {
                Layout.fillWidth: true
                text: "Coinductor will run a fresh guarded analysis and may redeem the previewed amount from Flexible Earn back to Spot, only if the preview remains ready. This does not place a trade by itself."
                color: textSecondary
                font.pixelSize: 13
                wrapMode: Text.WordWrap
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: earnRedeemConfirmWarning.implicitHeight + 24
                radius: 7
                color: "#3a3020"
                border.color: warning
                Text {
                    id: earnRedeemConfirmWarning
                    anchors.fill: parent
                    anchors.margins: 12
                    text: "Type CONFIRM_EARN_REDEEM exactly. Recheck the asset and amount before continuing."
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
                    text: "Cancel"
                    onClicked: earnRedeemConfirmDialog.close()
                }
                Button {
                    text: "Submit Earn redeem"
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
        title: "Deploy " + firstPortfolioDeployAsset + " tranche"
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
                text: "This runs the next tranche for " + firstPortfolioDeployAsset + " (target " + firstPortfolioDeployTargetPct + "% of the basket) using the total USDC budget and tranche count set on the Action Plan page. Every existing safety gate applies except market-timing consensus, which is intentionally skipped for this initial deployment."
                color: textSecondary
                font.pixelSize: 13
                wrapMode: Text.WordWrap
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Text { text: "Mode:"; color: textPrimary; font.pixelSize: 12 }
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
                radius: 7
                color: "#3a3020"
                border.color: warning
                Text {
                    id: firstPortfolioMainnetWarning
                    anchors.fill: parent
                    anchors.margins: 12
                    text: "Mainnet submit also requires the Safety stage to be LIVE_ENABLED and will place a real order."
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
                    text: "Validate only"
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
                text: "To submit for real, type " + firstPortfolioDeployDialog.expectedConfirm + " exactly."
                color: textSecondary
                font.pixelSize: 12
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
                    text: "Cancel"
                    onClicked: firstPortfolioDeployDialog.close()
                }
                Button {
                    text: "Submit tranche"
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
        title: activeGuide.title || "Help & Guides"
        modal: true
        anchors.centerIn: parent
        width: Math.min(820, window.width - 80)
        height: Math.min(640, window.height - 80)
        standardButtons: Dialog.Close

        ScrollView {
            anchors.fill: parent
            clip: true
            ColumnLayout {
                width: guideDialog.width - 48
                spacing: 14
                Rectangle {
                    Layout.preferredWidth: Math.max(90, guideSectionText.implicitWidth + 26)
                    Layout.preferredHeight: 28
                    radius: 5
                    color: "#17372d"
                    border.color: accent
                    Text {
                        id: guideSectionText
                        anchors.centerIn: parent
                        text: activeGuide.section || "Guide"
                        color: accent
                        font.pixelSize: 11
                        font.bold: true
                    }
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
                    radius: 7
                    color: "#3a3020"
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
                    onLinkActivated: (link) => Qt.openUrlExternally(link)
                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.NoButton
                        cursorShape: parent.hoveredLink ? Qt.PointingHandCursor : Qt.ArrowCursor
                    }
                }
                Repeater {
                    model: activeGuide.images || []
                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 6
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 260
                            radius: 7
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
                    text: "Screenshots and more detailed provider-specific steps can be added to this guide later."
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
        width: Math.min(420, Math.max(260, toastLabel.implicitWidth + 36))
        height: toastLabel.implicitHeight + 24
        modal: false
        focus: false
        closePolicy: Popup.NoAutoClose
        background: Rectangle {
            radius: 7
            color: "#14352c"
            border.color: accent
        }
        Text {
            id: toastLabel
            anchors.centerIn: parent
            text: window.toastText
            color: textPrimary
            font.pixelSize: 13
            font.bold: true
            elide: Text.ElideRight
        }
    }

    Timer {
        id: toastTimer
        interval: 2400
        onTriggered: toastPopup.close()
    }

    Dialog {
        id: deleteProfileDialog
        title: "Reset onboarding profile"
        modal: true
        anchors.centerIn: parent
        width: 460
        standardButtons: Dialog.Cancel

        ColumnLayout {
            width: parent.width
            spacing: 14
            Label {
                Layout.fillWidth: true
                text: "This resets only your onboarding profile: region, risk preference, automation preference, budget, and planner settings."
                wrapMode: Text.WordWrap
            }
            Label {
                Layout.fillWidth: true
                text: "API keys, reports, database history, role overrides, and safety state are not deleted."
                wrapMode: Text.WordWrap
            }
            Button {
                Layout.fillWidth: true
                text: "Reset onboarding profile"
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
        title: "Delete local app data"
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
                text: "Delete everything"
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
                    radius: 5
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
                text: "This permanently deletes the selected local files. It cannot be undone. Type DELETE to confirm."
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
                text: deleteConfirm.text === "DELETE" ? "Delete selected local data" : "Type DELETE to continue"
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
        title: "Run analysis"
        modal: true
        anchors.centerIn: parent
        width: 440
        standardButtons: Dialog.Cancel

        ColumnLayout {
            width: parent.width
            spacing: 14
            Label { text: "Data source" }
            ComboBox {
                id: dataMode
                Layout.fillWidth: true
                model: ["REAL", "MOCK"]
            }
            CheckBox { id: aiSummary; text: "Generate AI summary"; checked: true }
            CheckBox { id: aiProposals; text: "Allow AI market ranking"; checked: false }
            CheckBox {
                id: livePreview
                text: appController.safetyAllowsLivePreview ? "Include mainnet execution preview" : "Mainnet preview locked by safety stage"
                checked: appController.safetyAllowsLivePreview
                enabled: appController.safetyAllowsLivePreview
            }
            Label {
                Layout.fillWidth: true
                text: "This screen never submits orders. Confirmed execution remains a separate guarded workflow."
                wrapMode: Text.WordWrap
            }
            Button {
                Layout.fillWidth: true
                text: "Start analysis"
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
        required property string title
        required property string value
        required property color accentColor
        property string helpText: ""
        Layout.fillWidth: true
        Layout.preferredHeight: 98
        radius: 7
        color: panel
        border.color: border
        Column {
            anchors.fill: parent
            anchors.margins: 14
            spacing: 9
            Text { text: title; color: textSecondary; font.pixelSize: 11; font.bold: true }
            Text {
                width: parent.width
                text: value
                color: textPrimary
                font.pixelSize: 17
                font.bold: true
                elide: Text.ElideRight
            }
            Rectangle { width: 28; height: 3; radius: 1; color: accentColor }
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
}
