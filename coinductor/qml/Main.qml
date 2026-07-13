import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts

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
    property string pendingSafetyTarget: ""
    property string pendingSafetyPhrase: ""
    property var wizardSteps: ["Exchange", "Portfolio", "Profile", "AI", "Binance API", "Review"]
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

    function wizardPanelHeight() {
        if (wizardStep === 2)
            return 720
        if (wizardStep === 3)
            return 840
        if (wizardStep === 4)
            return 660
        if (wizardStep === 5)
            return 660
        return 560
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
                        Text { text: "Welcome to Coinductor"; color: textPrimary; font.pixelSize: 28; font.bold: true }
                        Text {
                            Layout.fillWidth: true
                            text: "A short setup wizard prepares your local profile before the main portfolio manager opens."
                            color: textSecondary
                            font.pixelSize: 14
                            wrapMode: Text.WordWrap
                        }
                    }
                    Button {
                        text: "Enter app"
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
                            text: "Nothing in this wizard places orders or changes exchange settings. It only creates a local preference profile and shows what still needs to be verified."
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
                                text: "Local-first"
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
                    Layout.preferredHeight: Math.max(window.wizardStep === 3 ? 760 : 640, window.height - 190)
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
                                text: "Setup steps"
                                color: textPrimary
                                font.pixelSize: 15
                                font.bold: true
                            }
                            Repeater {
                                model: window.wizardSteps
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
                                text: "The wizard changes only local Coinductor settings until you explicitly run checks or analysis."
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
                                    Text { text: "1. Choose exchange"; color: textPrimary; font.pixelSize: 22; font.bold: true }
                                    Text {
                                        Layout.fillWidth: true
                                        text: "Coinductor needs to know where the portfolio lives before it can explain API permissions, funding, and safety checks."
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
                                                text: wizardExchange.currentValue === "BINANCE" ? "Binance is supported in this build" : "Coinbase is planned, not available yet"
                                                color: wizardExchange.currentValue === "BINANCE" ? accent : warning
                                                font.pixelSize: 15
                                                font.bold: true
                                            }
                                            Text {
                                                Layout.fillWidth: true
                                                text: wizardExchange.currentValue === "BINANCE"
                                                    ? "The wizard will guide you through Binance read-only API setup, optional AI configuration, and a safe local profile. Trading permissions remain outside the desktop UI until explicit guarded workflows are ready."
                                                    : "The app is being designed so future exchanges can be added behind the same safety contract. Continue with Binance for now."
                                                color: textSecondary
                                                font.pixelSize: 12
                                                wrapMode: Text.WordWrap
                                            }
                                            Text {
                                                Layout.fillWidth: true
                                                text: "Manual setup covered later: account access, API key permissions, IP restrictions, read-only checks, and local privacy boundaries."
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
                                                text: appController.onboardingPath === "FIRST_PORTFOLIO" ? "First portfolio path selected" : "Existing portfolio path selected"
                                                color: accent
                                                font.pixelSize: 14
                                                font.bold: true
                                            }
                                            Text {
                                                Layout.fillWidth: true
                                                text: appController.onboardingPath === "FIRST_PORTFOLIO"
                                                    ? "The rest of the wizard will focus on a starting budget, reserve, initial basket, deposit guidance, and safe manual setup before any automation."
                                                    : "The rest of the wizard will focus on read-only Binance access, portfolio inventory, asset classification, and guarded recommendations for assets you already hold."
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
                                    Text { text: "2. Starting point"; color: textPrimary; font.pixelSize: 22; font.bold: true }
                                    Text {
                                        Layout.fillWidth: true
                                        text: "This choice changes what Coinductor explains next: existing portfolio classification, or a first funding and basket plan."
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
                                                Text { text: "I already have a portfolio"; color: textPrimary; font.pixelSize: 16; font.bold: true }
                                                Text {
                                                    Layout.fillWidth: true
                                                    text: "Best if you already hold assets on Binance. Coinductor will inventory balances, classify assets, and explain which ones can or cannot be used."
                                                    color: textSecondary
                                                    font.pixelSize: 12
                                                    wrapMode: Text.WordWrap
                                                }
                                                Item { Layout.fillHeight: true }
                                                Text { text: "Next: profile and read-only API"; color: accent; font.pixelSize: 12; font.bold: true }
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
                                                Text { text: "Build my first portfolio"; color: textPrimary; font.pixelSize: 16; font.bold: true }
                                                Text {
                                                    Layout.fillWidth: true
                                                    text: "Best if you start from fiat or USDC. Coinductor will suggest a reserve, initial deployment, and manual setup steps before automation."
                                                    color: textSecondary
                                                    font.pixelSize: 12
                                                    wrapMode: Text.WordWrap
                                                }
                                                Item { Layout.fillHeight: true }
                                                Text { text: "Next: profile and first plan"; color: accent; font.pixelSize: 12; font.bold: true }
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
                                    Text { text: "3. Decision profile"; color: textPrimary; font.pixelSize: 22; font.bold: true }
                                    Text {
                                        Layout.fillWidth: true
                                        text: "This short profile tells Coinductor how cautious, active, and hands-on recommendations should be. It does not place orders."
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
                                            Text { text: "Management style"; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                            ComboBox { id: wizardStyle; Layout.fillWidth: true; model: window.styleOptions; textRole: "label"; valueRole: "value"; currentIndex: 1; onActivated: window.markProfileEdited() }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Text { text: "Automation"; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                            ComboBox { id: wizardAutomation; Layout.fillWidth: true; model: window.automationOptions; textRole: "label"; valueRole: "value"; onActivated: window.markProfileEdited() }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Text { text: "Review rhythm"; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                            ComboBox { id: wizardCadence; Layout.fillWidth: true; model: window.cadenceOptions; textRole: "label"; valueRole: "value"; currentIndex: 1; onActivated: window.markProfileEdited() }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Text { text: "Language / region"; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                            ComboBox { id: wizardLocale; Layout.fillWidth: true; model: ["en-US", "es-ES", "cs-CZ", "pt-BR"]; onActivated: window.markProfileEdited() }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Text { text: "Operating currency"; color: textPrimary; font.pixelSize: 12; font.bold: true }
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
                                            Text { Layout.fillWidth: true; text: "Coinductor currently plans bot funding and trading budgets around USDC. Regional fiat funding comes later."; color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Text { text: "Starting budget"; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                            ComboBox { id: wizardBudget; Layout.fillWidth: true; model: window.budgetOptions; textRole: "label"; valueRole: "value"; onActivated: window.markProfileEdited() }
                                            Text { Layout.fillWidth: true; text: window.budgetHelp(wizardBudget.currentValue); color: textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                        }
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 12
                                        ColumnLayout {
                                            Layout.preferredWidth: 300
                                            Text { text: "Drawdown comfort"; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                            ComboBox { id: wizardDrawdown; Layout.fillWidth: true; model: window.drawdownOptions; textRole: "label"; valueRole: "value"; currentIndex: 1; onActivated: window.markProfileEdited() }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            CheckBox { id: wizardUseBots; text: "Use Binance bot recommendations"; checked: true; onClicked: window.markProfileEdited() }
                                            Text { Layout.fillWidth: true; text: window.botHelp(wizardUseBots.checked); color: textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            CheckBox {
                                                id: wizardAllowSpot
                                                text: "Allow guarded spot trades"
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
                                            Text { text: "Current selection"; color: textPrimary; font.pixelSize: 13; font.bold: true }
                                            Text {
                                                Layout.fillWidth: true
                                                visible: !window.profileChoicesEdited && !appController.userProfileConfigured
                                                text: "Choose a profile option above to see what it changes. Nothing is saved until you press Save profile or Apply safe defaults."
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
                                            text: "Apply safe defaults"
                                            ToolTip.visible: hovered
                                            ToolTip.text: "Immediately saves a conservative local profile: recommendations only, no guarded spot trades, and beginner-friendly risk settings."
                                            onClicked: {
                                                appController.useSafeDefaultProfile()
                                                window.profileChoicesEdited = true
                                                window.showToast("Safe default profile saved")
                                            }
                                        }
                                        Button {
                                            text: "Save profile"
                                            ToolTip.visible: hovered
                                            ToolTip.text: "Saves these profile choices locally. It does not connect to Binance or place orders."
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
                                        text: appController.userProfileConfigured ? "Profile is saved. Continue to AI setup." : "Save a profile or use safe defaults before continuing."
                                        color: appController.userProfileConfigured ? accent : warning
                                        font.pixelSize: 12
                                        font.bold: true
                                    }
                                    Item { Layout.fillHeight: true }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    Text { text: "4. AI assistant setup"; color: textPrimary; font.pixelSize: 22; font.bold: true }
                                    Text {
                                        Layout.fillWidth: true
                                        text: "AI is optional. After a provider is connected, Coinductor can offer step-by-step wizard help, report summaries, and app Q&A without giving AI direct execution control."
                                        color: textSecondary
                                        font.pixelSize: 13
                                        wrapMode: Text.WordWrap
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Button {
                                            text: "Open local AI guide"
                                            onClicked: window.openGuide("local-ai")
                                        }
                                        Button {
                                            text: "Open cloud AI guide"
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
                                                Text { text: "Current AI provider"; color: textPrimary; font.pixelSize: 15; font.bold: true }
                                                Text { Layout.fillWidth: true; text: appController.aiProviderSummary; color: textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap }
                                                Text { Layout.fillWidth: true; text: appController.aiProviderHealthDetail; color: textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                                Text { Layout.fillWidth: true; text: "You can skip AI setup and add it later. Inline wizard Q&A is planned next."; color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap }
                                            }
                                            Button {
                                                text: appController.checkingAiProvider ? "Checking..." : "Check AI provider"
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
                                            Layout.preferredHeight: appController.localAiModelRecommendations.length > 0 ? (aiProviderGrid.columns === 1 ? 680 : 640) : 390
                                            Layout.minimumHeight: appController.localAiModelRecommendations.length > 0 ? 610 : 360
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
                                                Text { Layout.fillWidth: true; text: "1. Install Ollama.  2. Pull a model, e.g. qwen3:8b or qwen3:14b.  3. Keep Ollama running.  4. Save these settings."; color: textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 8
                                                    TextField { id: localAiBaseUrl; Layout.fillWidth: true; placeholderText: "http://127.0.0.1:11434/v1"; text: "http://127.0.0.1:11434/v1" }
                                                    TextField { id: localAiModel; Layout.preferredWidth: 170; placeholderText: "qwen3:14b"; text: "qwen3:14b" }
                                                }
                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 8
                                                    Button {
                                                        text: "Save local AI"
                                                        onClicked: {
                                                            appController.saveLocalAiProvider(localAiBaseUrl.text, localAiModel.text)
                                                            window.showToast("Local AI settings saved")
                                                        }
                                                    }
                                                    Button {
                                                        text: "Scan hardware"
                                                        onClicked: appController.scanLocalAiHardware()
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
                                                                    Text { Layout.preferredWidth: 90; text: modelData.model; color: accent; font.pixelSize: 11; font.bold: true; elide: Text.ElideRight }
                                                                    Text { Layout.preferredWidth: 86; text: modelData.fit; color: textPrimary; font.pixelSize: 10; font.bold: true; elide: Text.ElideRight }
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
                                            Layout.preferredHeight: appController.localAiModelRecommendations.length > 0 ? (aiProviderGrid.columns === 1 ? 350 : 640) : 390
                                            Layout.minimumHeight: 340
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
                                                Text { Layout.fillWidth: true; text: "OpenAI example: create an API key in OpenAI Platform > API keys, then use https://api.openai.com/v1 and your chosen model. A ChatGPT subscription is separate from API usage."; color: textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 8
                                                    TextField { id: cloudAiBaseUrl; Layout.fillWidth: true; placeholderText: "https://api.openai.com/v1" }
                                                    TextField { id: cloudAiModel; Layout.preferredWidth: 170; placeholderText: "model name" }
                                                }
                                                TextField { id: cloudAiKey; Layout.fillWidth: true; placeholderText: "API key"; echoMode: TextInput.Password }
                                                Button {
                                                    text: "Save cloud AI"
                                                    enabled: cloudAiBaseUrl.text.trim().length > 0 && cloudAiModel.text.trim().length > 0 && cloudAiKey.text.trim().length > 0
                                                    onClicked: {
                                                        appController.saveCloudAiProvider(cloudAiBaseUrl.text, cloudAiModel.text, cloudAiKey.text)
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
                                    Text { text: "5. Binance API and safety checks"; color: textPrimary; font.pixelSize: 22; font.bold: true }
                                    Text {
                                        Layout.fillWidth: true
                                        text: "Coinductor needs read-only Binance API access for portfolio analysis. Trading permissions are separate and should only be added later when guarded workflows are ready."
                                        color: textSecondary
                                        font.pixelSize: 13
                                        wrapMode: Text.WordWrap
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Button {
                                            text: "Open Binance API guide"
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
                                            Text { text: "Connect read-only key to Coinductor"; color: textPrimary; font.pixelSize: 15; font.bold: true }
                                            RowLayout {
                                                Layout.fillWidth: true
                                                TextField { id: binanceReadKey; Layout.fillWidth: true; placeholderText: "API Key" }
                                                TextField { id: binanceReadSecret; Layout.fillWidth: true; placeholderText: "Secret Key"; echoMode: TextInput.Password }
                                                Button {
                                                    text: "Save key"
                                                    enabled: binanceReadKey.text.trim().length > 0 && binanceReadSecret.text.trim().length > 0
                                                    onClicked: {
                                                        appController.saveBinanceReadOnlyCredentials(binanceReadKey.text, binanceReadSecret.text)
                                                        binanceReadSecret.text = ""
                                                        window.showToast("Read-only Binance key saved")
                                                    }
                                                }
                                            }
                                            Text { Layout.fillWidth: true; Layout.topMargin: 2; text: "The key is stored in the local .env file in this project folder. It is not sent anywhere by the wizard."; color: textSecondary; font.pixelSize: 10; wrapMode: Text.WordWrap }
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Button {
                                            text: appController.checkingConnection ? "Checking..." : "Check read-only access"
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
                                    Item { Layout.fillHeight: true }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 14
                                    Text { text: "6. Review and enter Coinductor"; color: textPrimary; font.pixelSize: 22; font.bold: true }
                                    Text {
                                        Layout.fillWidth: true
                                        text: "The setup profile is saved locally. The main app will show your dashboard, portfolio roles, strategy recommendations, assistant, settings, and safety state."
                                        color: textSecondary
                                        font.pixelSize: 13
                                        wrapMode: Text.WordWrap
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Button {
                                            text: "Open safety guide"
                                            onClicked: window.openGuide("safety-model")
                                        }
                                        Button {
                                            text: "Open portfolio roles guide"
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

                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 58
                    Layout.bottomMargin: 18
                    Button {
                        text: "Back"
                        enabled: window.wizardStep > 0
                        onClicked: window.wizardStep = Math.max(0, window.wizardStep - 1)
                    }
                    Text {
                        Layout.fillWidth: true
                        text: !window.canContinueWizard()
                            ? (window.wizardStep === 0 ? "Choose Binance to continue." : window.wizardStep === 1 ? "Choose how you are starting." : "Save a profile before continuing.")
                            : ""
                        color: warning
                        font.pixelSize: 12
                    }
                    Button {
                        text: window.wizardStep === window.wizardSteps.length - 1 ? "Enter Coinductor" : "Next"
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
                    model: ["Overview", "Live Actions", "Portfolio", "Action Plan", "Run History", "AI Assistant", "Help & Guides", "Settings"]
                    delegate: Rectangle {
                        required property string modelData
                        required property int index
                        Layout.fillWidth: true
                        Layout.preferredHeight: 42
                        radius: 6
                        color: appController.currentPage === index ? panelRaised : "transparent"
                        border.color: appController.currentPage === index ? border : "transparent"
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left
                            anchors.leftMargin: 14
                            text: modelData
                            color: appController.currentPage === index ? textPrimary : textSecondary
                            font.pixelSize: 14
                        }
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: appController.setCurrentPage(index)
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
                            text: "No Safety stage change places an order. Live BUY and OCO protection always require a separate confirmation and fresh deterministic validation."
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
                    MetricCard { title: "Portfolio"; value: appController.portfolioValue; accentColor: accent }
                    MetricCard { title: "Liquid"; value: appController.liquidValue; accentColor: "#5aa9e6" }
                    MetricCard { title: "Locked"; value: appController.lockedValue; accentColor: warning }
                    MetricCard { title: "Risk gate"; value: appController.riskState; accentColor: "#d66b75" }
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
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: appController.currentPage === 2

            ColumnLayout {
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
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: appController.currentPage === 3

            ColumnLayout {
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

            ColumnLayout {
                x: 28
                y: 28
                width: Math.max(window.width - 288, 692)
                spacing: 18

                Text { text: "Run History"; color: textPrimary; font.pixelSize: 26; font.bold: true }
                Text { text: "The latest 30 analytical runs"; color: textSecondary; font.pixelSize: 13 }

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
            visible: appController.currentPage === 5

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 28
                spacing: 14

                Text { text: "AI Assistant"; color: textPrimary; font.pixelSize: 26; font.bold: true }
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: "Read-only help with offline fallback and optional configured AI provider"
                        color: textSecondary
                        font.pixelSize: 14
                    }
                    Rectangle {
                        Layout.preferredWidth: 360
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
                        required property var modelData
                        width: ListView.view.width
                        height: messageBubble.implicitHeight
                        Rectangle {
                            id: messageBubble
                            width: Math.min(parent.width * 0.72, Math.max(280, messageText.implicitWidth + 30))
                            implicitHeight: messageText.implicitHeight + 24
                            anchors.right: modelData.role === "user" ? parent.right : undefined
                            anchors.left: modelData.role === "user" ? undefined : parent.left
                            radius: 7
                            color: modelData.role === "user" ? "#234f43" : panel
                            border.color: modelData.role === "user" ? "#337660" : border
                            Text {
                                id: messageText
                                anchors.fill: parent
                                anchors.margins: 12
                                text: modelData.text
                                color: textPrimary
                                font.pixelSize: 13
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    TextField {
                        id: assistantInput
                        Layout.fillWidth: true
                        placeholderText: "Ask about the latest run, portfolio, risk, Grid..."
                        enabled: !appController.assistantBusy
                        onAccepted: {
                            appController.askAssistant(text)
                            clear()
                        }
                    }
                    Button {
                        text: appController.assistantBusy ? "Thinking..." : "Send"
                        enabled: assistantInput.text.trim().length > 0 && !appController.assistantBusy
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
            visible: appController.currentPage === 6

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
                    Layout.row: 4
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
                    Layout.row: 3
                    Layout.fillWidth: true
                    Layout.preferredHeight: 485
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
                                Text { text: "Credentials & Safety"; color: textPrimary; font.pixelSize: 16; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: "Add a separate Binance Spot trading key only after read-only reports and preview workflows are trusted. Saving this key does not unlock live submit."
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                            }
                            Rectangle {
                                Layout.preferredWidth: 112
                                Layout.preferredHeight: 30
                                radius: 5
                                color: appController.liveTradingKeyStatus === "PASS" ? "#17372d" : "#3a3020"
                                border.color: appController.liveTradingKeyStatus === "PASS" ? accent : warning
                                Text {
                                    anchors.centerIn: parent
                                    text: appController.liveTradingKeyStatus === "PASS" ? "CONFIGURED" : "LOCKED"
                                    color: appController.liveTradingKeyStatus === "PASS" ? accent : warning
                                    font.pixelSize: 10
                                    font.bold: true
                                }
                            }
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: liveWarningText.implicitHeight + 24
                            radius: 7
                            color: "#3a3020"
                            border.color: warning
                            Text {
                                id: liveWarningText
                                anchors.fill: parent
                                anchors.margins: 12
                                text: "Use a separate key with Reading + Spot trading only, trusted-IP restriction enabled, and withdrawals disabled. Dynamic-IP users should keep live execution locked unless they can maintain the whitelist."
                                color: warning
                                font.pixelSize: 12
                                font.bold: true
                                wrapMode: Text.WordWrap
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: appController.liveTradingKeyDetail
                            color: textSecondary
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            TextField { id: liveTradingApiKey; Layout.fillWidth: true; placeholderText: "Live trading API key" }
                            TextField { id: liveTradingApiSecret; Layout.fillWidth: true; placeholderText: "Live trading secret key"; echoMode: TextInput.Password }
                        }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: 3
                            columnSpacing: 12
                            rowSpacing: 6
                            CheckBox { id: liveSeparateKey; text: "Separate from read-only key"; checked: false }
                            CheckBox { id: liveIpRestricted; text: "Trusted-IP restriction understood"; checked: false }
                            CheckBox { id: liveNoWithdrawals; text: "Withdrawals remain disabled"; checked: false }
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
                            Text {
                                Layout.fillWidth: true
                                text: "Live submit still depends on the Safety stage and explicit guarded confirmations. This panel only stores local credentials."
                                color: textSecondary
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12
                            Button {
                                text: appController.checkingLiveTrading ? "Checking permissions..." : "Verify live API permissions"
                                enabled: appController.liveTradingKeyStatus === "PASS" && !appController.checkingLiveTrading
                                onClicked: appController.checkBinanceLiveTrading()
                            }
                            Rectangle {
                                Layout.preferredWidth: 96
                                Layout.preferredHeight: 28
                                radius: 5
                                color: appController.liveTradingCheckStatus === "Verified" ? "#17372d" : "#3a3020"
                                border.color: appController.liveTradingCheckStatus === "Verified" ? accent : warning
                                Text {
                                    anchors.centerIn: parent
                                    text: appController.liveTradingCheckStatus.toUpperCase()
                                    color: appController.liveTradingCheckStatus === "Verified" ? accent : warning
                                    font.pixelSize: 10
                                    font.bold: true
                                }
                            }
                            Text {
                                Layout.fillWidth: true
                                text: appController.liveTradingCheckDetail
                                color: textSecondary
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.row: 2
                    Layout.fillWidth: true
                    Layout.preferredHeight: 410
                    radius: 7
                    color: panel
                    border.color: appController.safetyAllowsLiveSubmit ? accent : border
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 12
                        RowLayout {
                            Layout.fillWidth: true
                            Text { Layout.fillWidth: true; text: "Safety stage"; color: textPrimary; font.pixelSize: 16; font.bold: true }
                            Text { text: appController.safetyStage; color: appController.safetyAllowsLiveSubmit ? accent : warning; font.pixelSize: 12; font.bold: true }
                        }
                        Text { Layout.fillWidth: true; text: appController.safetyDetail; color: textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap }
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
                Item { Layout.row: 5; Layout.fillWidth: true; Layout.preferredHeight: 44 }
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
                            text: "Reset onboarding only changes preferences. Delete local data is a separate preview for a full local reset and is not executed yet."
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
                            ? "Live trade submission is separate from review. It stays locked unless the latest BUY preview, live key, safety stage, and confirmation text all pass."
                            : activeActionPlanItem.actionCode === "REVIEW_OCO"
                                ? "OCO protection is a separate SELL order pair. Submission requires a READY preview and its own explicit confirmation."
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
                    visible: activeActionPlanItem.actionCode === "REVIEW_TRADE" || activeActionPlanItem.actionCode === "REVIEW_OCO"
                    radius: 7
                    color: panelRaised
                    border.color: activeActionPlanItem.submitEnabled === true ? accent : border
                    ColumnLayout {
                        id: liveTradeGuardContent
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 8
                        Text {
                            text: activeActionPlanItem.actionCode === "REVIEW_OCO" ? "Guarded position protection" : "Guarded live trade"
                            color: textPrimary
                            font.pixelSize: 15
                            font.bold: true
                        }
                        Text {
                            Layout.fillWidth: true
                            text: activeActionPlanItem.submitEnabled === true
                                ? activeActionPlanItem.actionCode === "REVIEW_OCO"
                                    ? "This will run a fresh validation pass and submit the OCO pair only if the position protection preview is still ready."
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
                                    } else {
                                        liveTradeConfirmInput.text = ""
                                        liveTradeConfirmDialog.open()
                                    }
                                }
                            }
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
                    color: textPrimary
                    font.pixelSize: 13
                    lineHeight: 1.18
                    wrapMode: Text.WordWrap
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
                text: "Type DELETE to confirm. This dialog is preview-only in this build; actual deletion will be enabled in a separate guarded implementation step."
                wrapMode: Text.WordWrap
            }
            TextField {
                id: deleteConfirm
                Layout.fillWidth: true
                placeholderText: "DELETE"
            }
            Button {
                Layout.fillWidth: true
                text: deleteConfirm.text === "DELETE" ? "Preview only - deletion not enabled yet" : "Type DELETE to continue"
                enabled: false
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
    }
}
