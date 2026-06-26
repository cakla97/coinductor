import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 1240
    height: 780
    minimumWidth: 980
    minimumHeight: 680
    visible: true
    title: "Coinductor"
    color: "#0f1318"
    Material.theme: Material.Dark
    Material.primary: "#36c98f"
    Material.accent: "#36c98f"
    Material.background: "#171d24"
    Material.foreground: "#f2f5f7"

    property color panel: "#171d24"
    property color panelRaised: "#1d252e"
    property color border: "#2a3540"
    property color textPrimary: "#f2f5f7"
    property color textSecondary: "#9ba8b5"
    property color accent: "#36c98f"
    property color warning: "#f1b84b"

    RowLayout {
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
                    model: ["Overview", "Portfolio", "Strategies", "Run History", "AI Assistant", "Settings"]
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
            visible: appController.currentPage === 1

            ColumnLayout {
                x: 28
                y: 28
                width: Math.max(window.width - 288, 692)
                spacing: 18

                Text { text: "Portfolio"; color: textPrimary; font.pixelSize: 26; font.bold: true }
                Text { text: "Latest real-run valuation, asset roles, and liquidity location"; color: textSecondary; font.pixelSize: 13 }

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
                        Text { Layout.preferredWidth: 190; text: "POLICY"; color: textSecondary; font.pixelSize: 10; font.bold: true }
                        Text { Layout.preferredWidth: 120; text: "VALUE"; color: textSecondary; font.pixelSize: 10; font.bold: true }
                        Text { Layout.preferredWidth: 75; text: "SHARE"; color: textSecondary; font.pixelSize: 10; font.bold: true }
                        Text { Layout.fillWidth: true; text: "LIQUIDITY"; color: textSecondary; font.pixelSize: 10; font.bold: true }
                        Text { Layout.preferredWidth: 78; text: "SOURCE"; color: textSecondary; font.pixelSize: 10; font.bold: true }
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
                                Layout.preferredWidth: 190
                                spacing: 3
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.role
                                    color: modelData.policySource === "MANUAL" ? accent : textSecondary
                                    font.pixelSize: 10
                                    font.bold: modelData.policySource === "MANUAL"
                                    elide: Text.ElideRight
                                }
                                ComboBox {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 30
                                    model: appController.assetRoleOptions
                                    currentIndex: appController.assetRoleOptions.indexOf(modelData.roleOverride)
                                    font.pixelSize: 10
                                    onActivated: function(index) {
                                        appController.saveAssetRoleOverride(modelData.asset, appController.assetRoleOptions[index])
                                    }
                                }
                            }
                            Text { Layout.preferredWidth: 120; text: modelData.value; color: textPrimary; font.pixelSize: 12 }
                            Text { Layout.preferredWidth: 75; text: modelData.allocation; color: textPrimary; font.pixelSize: 12 }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Text { text: "Spot " + modelData.spot + "   Flexible " + modelData.flexible; color: textSecondary; font.pixelSize: 10 }
                                Text { text: "Locked " + modelData.locked; color: textSecondary; font.pixelSize: 10 }
                            }
                            ColumnLayout {
                                Layout.preferredWidth: 78
                                spacing: 3
                                Text {
                                    text: modelData.policySource
                                    color: modelData.policySource === "MANUAL" ? accent : textSecondary
                                    font.pixelSize: 10
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
            visible: appController.currentPage === 2

            ColumnLayout {
                x: 28
                y: 28
                width: Math.max(window.width - 288, 692)
                spacing: 18

                Text { text: "Strategies"; color: textPrimary; font.pixelSize: 26; font.bold: true }
                Text { text: "Guarded recommendations for Binance-native automation"; color: textSecondary; font.pixelSize: 13 }

                ListView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.max(460, contentHeight)
                    spacing: 10
                    model: appController.strategies
                    delegate: Rectangle {
                        required property var modelData
                        width: ListView.view.width
                        height: 142
                        radius: 7
                        color: panel
                        border.color: border
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 18
                            spacing: 8
                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: modelData.type; color: textPrimary; font.pixelSize: 17; font.bold: true }
                                Text { text: modelData.name; color: accent; font.pixelSize: 14; font.bold: true }
                                Item { Layout.fillWidth: true }
                                Text {
                                    text: modelData.status
                                    color: modelData.status === "READY" ? accent : warning
                                    font.pixelSize: 11
                                    font.bold: true
                                }
                            }
                            RowLayout {
                                spacing: 24
                                Text { text: "Capital  " + modelData.capital; color: textSecondary; font.pixelSize: 12 }
                                Text { text: modelData.allowed; color: textSecondary; font.pixelSize: 12 }
                            }
                            Text {
                                Layout.fillWidth: true
                                text: modelData.detail
                                color: textSecondary
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                                maximumLineCount: 3
                                elide: Text.ElideRight
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
            visible: appController.currentPage === 4

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 28
                spacing: 14

                Text { text: "AI Assistant"; color: textPrimary; font.pixelSize: 26; font.bold: true }
                Text { text: "Offline project help grounded in your latest real run"; color: textSecondary; font.pixelSize: 13 }

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
                        onAccepted: {
                            appController.askAssistant(text)
                            clear()
                        }
                    }
                    Button {
                        text: "Send"
                        enabled: assistantInput.text.trim().length > 0
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
            visible: appController.currentPage === 5

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
                        text: "Choose a starting path and verify this computer before connecting services."
                        color: textSecondary
                        font.pixelSize: 13
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

                Text { text: "How are you starting?"; color: textPrimary; font.pixelSize: 16; font.bold: true }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 150
                        radius: 7
                        color: appController.onboardingPath === "EXISTING" ? "#1d332d" : panel
                        border.color: appController.onboardingPath === "EXISTING" ? accent : border
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 18
                            spacing: 8
                            Text { text: "I already have a portfolio"; color: textPrimary; font.pixelSize: 16; font.bold: true }
                            Text {
                                Layout.fillWidth: true
                                text: "Connect Binance read-only access, classify current assets, then test guarded automation."
                                color: textSecondary
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                            }
                            Item { Layout.fillHeight: true }
                            Text { text: "Analyze existing allocation"; color: accent; font.pixelSize: 11; font.bold: true }
                        }
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: appController.selectOnboardingPath("EXISTING")
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 150
                        radius: 7
                        color: appController.onboardingPath === "FIRST_PORTFOLIO" ? "#1d332d" : panel
                        border.color: appController.onboardingPath === "FIRST_PORTFOLIO" ? accent : border
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 18
                            spacing: 8
                            Text { text: "Build my first portfolio"; color: textPrimary; font.pixelSize: 16; font.bold: true }
                            Text {
                                Layout.fillWidth: true
                                text: "Start from USDC, choose a risk profile, simulate a staged entry, and activate automation gradually."
                                color: textSecondary
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                            }
                            Item { Layout.fillHeight: true }
                            Text { text: "Create a controlled starting plan"; color: accent; font.pixelSize: 11; font.bold: true }
                        }
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: appController.selectOnboardingPath("FIRST_PORTFOLIO")
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: appController.onboardingPath === "" ? 0 : 96
                    visible: appController.onboardingPath !== ""
                    radius: 7
                    color: panelRaised
                    border.color: border
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        Text {
                            Layout.fillWidth: true
                            text: appController.onboardingPath === "EXISTING"
                                ? "Next: validate read-only Binance access and run an initial portfolio classification."
                                : "Next: define budget, risk profile, reserve, and a testnet-first staged USDC deployment plan."
                            color: textPrimary
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                        }
                        Button {
                            text: appController.onboardingPath === "EXISTING"
                                ? (appController.busy ? "Running..." : "Run classification")
                                : "Planned"
                            enabled: appController.onboardingPath === "EXISTING" && !appController.busy
                            onClicked: appController.runInitialClassification()
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: appController.onboardingPath === "EXISTING" ? 260 : 0
                    visible: appController.onboardingPath === "EXISTING"
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
                                Text { text: "Portfolio classification review"; color: textPrimary; font.pixelSize: 16; font.bold: true }
                                Text {
                                    Layout.fillWidth: true
                                    text: appController.onboardingReviewSummary
                                    color: textSecondary
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                            }
                            Button {
                                text: "Open report"
                                enabled: appController.hasReport
                                onClicked: appController.openReport()
                            }
                        }
                        ListView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            interactive: false
                            spacing: 6
                            model: appController.onboardingReview
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
                                    spacing: 12
                                    Text { Layout.preferredWidth: 150; text: modelData.label; color: textPrimary; font.pixelSize: 12; font.bold: true }
                                    Text { Layout.preferredWidth: 130; text: modelData.value; color: accent; font.pixelSize: 12; font.bold: true; elide: Text.ElideRight }
                                    Text { Layout.fillWidth: true; text: modelData.detail; color: textSecondary; font.pixelSize: 11; elide: Text.ElideRight }
                                }
                            }
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
            CheckBox { id: livePreview; text: "Include mainnet execution preview"; checked: true }
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
