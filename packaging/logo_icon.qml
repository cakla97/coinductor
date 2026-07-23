import QtQuick

// Standalone render of the in-app AppLogo mark (coinductor/qml/Main.qml)
// used only to generate the app/installer icon. Keep the geometry in sync
// with the AppLogo component if the logo changes.
Item {
    width: 256
    height: 256

    Item {
        id: logo
        readonly property real size: 236
        width: size
        height: size
        anchors.centerIn: parent

        readonly property real markCx: size * 0.5
        readonly property real markCy: size * 0.46
        readonly property real ringRadius: size * 0.23
        readonly property real ringStroke: size * 0.09
        readonly property color accent: "#36c98f"
        readonly property color glyph: "#09110e"

        Rectangle {
            width: logo.size
            height: logo.size * 0.62
            radius: logo.size * 0.26
            color: logo.accent
            anchors.top: parent.top
        }
        Rectangle {
            width: logo.size * 0.72
            height: logo.size * 0.72
            radius: logo.size * 0.16
            color: logo.accent
            rotation: 45
            anchors.horizontalCenter: parent.horizontalCenter
            y: logo.size * 0.32
        }
        Canvas {
            anchors.fill: parent
            renderStrategy: Canvas.Immediate
            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                ctx.lineWidth = logo.ringStroke
                ctx.strokeStyle = "#09110e"
                ctx.lineCap = "round"
                ctx.beginPath()
                ctx.arc(logo.markCx, logo.markCy, logo.ringRadius,
                         40 * Math.PI / 180, 320 * Math.PI / 180, false)
                ctx.stroke()
            }
            Component.onCompleted: requestPaint()
        }
        Rectangle {
            width: Math.max(1.1, logo.ringStroke * 0.55)
            height: logo.ringRadius * 2.5
            radius: width / 2
            color: logo.glyph
            x: logo.markCx - logo.ringRadius * 0.34 - width / 2
            y: logo.markCy - height / 2
        }
        Rectangle {
            width: Math.max(1.1, logo.ringStroke * 0.55)
            height: logo.ringRadius * 2.5
            radius: width / 2
            color: logo.glyph
            x: logo.markCx + logo.ringRadius * 0.34 - width / 2
            y: logo.markCy - height / 2
        }
    }
}
