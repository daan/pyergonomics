import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import PyeHelpers 0.1

Rectangle {
    id: root
    height: 30
    
    color: isSelected ? Qt.darker("#336699", 1.2) : "#444444"
    border.color: "#555555"

    property int personId: -1
    property bool isVisible: true
    property bool isSelected: false
    property var events: []
    property int trackNameColumnWidth: 150
    property int visibilityColumnWidth: 50
    property font timelineFont: Qt.font({ pixelSize: 12 })

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        onClicked: (mouse) => {
            // Map the click position from the MouseArea's coordinates to the TimelineEditor's coordinates
            var posInTimeline = mapToItem(timelineEditor, mouse.x, mouse.y)

            // Update current frame based on click position
            if (timelineEditor.pixelsPerFrame > 0) {
                var frame = timelineEditor.viewPosition + (posInTimeline.x / timelineEditor.pixelsPerFrame);
                var newFrame = Math.round(Math.max(0, Math.min(appState.totalFrames - 1, frame)));
                appState.currentFrame = newFrame;
            }

            // Update selection
            if (mouse.modifiers & Qt.ShiftModifier) {
                appState.updateSelection(personId, "range");
            } else if (mouse.modifiers & Qt.ControlModifier) {
                appState.updateSelection(personId, "toggle");
            } else {
                appState.updateSelection(personId, "single");
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 10

        Label {
            text: "person " + personId
            Layout.preferredWidth: root.trackNameColumnWidth
            Layout.maximumWidth: root.trackNameColumnWidth
            elide: Text.ElideRight
            color: "white"
            font: root.timelineFont
        }

        CheckBox {
            id: visibilityCb
            checked: isVisible
            onCheckedChanged: peopleModel.sourceModel.setPersonVisible(personId, checked)
            Layout.preferredWidth: root.visibilityColumnWidth
            Layout.maximumWidth: root.visibilityColumnWidth
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            TimelineEditor {
                id: timelineEditor
                anchors.fill: parent

                intervals: root.events
                personId: root.personId
                totalFrames: appState.totalFrames
                currentFrame: appState.currentFrame
                viewPosition: appState.viewPosition
                pixelsPerFrame: appState.pixelsPerFrame
            }

            Rectangle {
                anchors.fill: parent
                color: "#444444"
                opacity: 0.7
                visible: !isVisible
            }
        }
    }
}
