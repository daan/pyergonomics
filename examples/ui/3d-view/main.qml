import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick3D
import QtQuick3D.Helpers

import PyeHelpers
import CvHelpers

ApplicationWindow {
    width: 1280
    height: 720
    visible: true
    title: "Pose 3D Viewer"

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
            if (event.key === Qt.Key_F) {
                personView.zoomToFit = true
            }
        }

        PersonView {
            id: personView
            Layout.fillWidth: true
            Layout.fillHeight: true
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
