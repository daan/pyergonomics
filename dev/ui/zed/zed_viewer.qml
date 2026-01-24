import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import PyeHelpers

ApplicationWindow {
    id: window
    visible: true
    width: 1280
    height: 720
    title: "ZED Body Tracking Viewer"
    color: "#1a1a1a"

    // Handle ESC key to quit
    Shortcut {
        sequence: "Escape"
        onActivated: Qt.quit()
    }

    PersonView {
        id: personView
        anchors.fill: parent
    }

    // Zoom to fit button
    Button {
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.margins: 10
        text: "Zoom to Fit"
        onClicked: personView.zoomToFit = true
    }

    // Info overlay
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 10
        color: "#80000000"
        radius: 4
        width: infoColumn.width + 16
        height: infoColumn.height + 12

        Column {
            id: infoColumn
            anchors.centerIn: parent
            spacing: 4

            Label {
                color: "white"
                text: "Frame: " + skeletonProvider.frameCount
                font.pixelSize: 14
                font.family: "monospace"
            }
            Label {
                color: "white"
                text: "Skeletons: " + skeletonProvider.skeletons.length
                font.pixelSize: 14
                font.family: "monospace"
            }
        }
    }

    // ESC hint
    Label {
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.margins: 10
        color: "#80ffffff"
        text: "Press ESC to exit"
        font.pixelSize: 12
    }
}
