import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import PyeHelpers

ApplicationWindow {
    id: root
    width: 800
    height: 600
    visible: true
    title: "Video Viewer"
    color: "#333333"

    Shortcut {
        sequence: "Escape"
        onActivated: Qt.quit()
    }
    Shortcut {
        sequence: "Space"
        onActivated: appState.togglePlayPause()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 5

        focus: true
        Keys.onPressed: (event) => {
            if (event.key === Qt.Key_Left) {
                if (appState.currentFrame > 0) {
                    appState.currentFrame--
                } else {
                    appState.currentFrame = appState.totalFrames - 1 // Wrap around
                }
            }
            if (event.key === Qt.Key_Right) {
                if (appState.currentFrame < appState.totalFrames - 1) {
                    appState.currentFrame++
                } else {
                    appState.currentFrame = 0 // Wrap around
                }
            }
        }

        FrameView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            // No model provided, so just video
        }

        Slider {
            id: frameSlider
            Layout.fillWidth: true
            from: 0
            to: appState.totalFrames > 0 ? appState.totalFrames - 1 : 0
            value: appState.currentFrame
            stepSize: 1.0

            onMoved: {
                appState.currentFrame = Math.round(value)
            }
        }
    }
}
