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
                        Layout.fillWidth: true
                        Layout.preferredHeight: 42
                        radius: 6
                        color: modelData === "Overview" ? panelRaised : "transparent"
                        border.color: modelData === "Overview" ? border : "transparent"
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left
                            anchors.leftMargin: 14
                            text: modelData
                            color: modelData === "Overview" ? textPrimary : textSecondary
                            font.pixelSize: 14
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
                                color: accent
                                anchors.verticalCenter: parent.verticalCenter
                            }
                            Text { text: "Not checked"; color: textPrimary; font.pixelSize: 13 }
                        }
                    }
                }
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

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
