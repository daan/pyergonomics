import QtQuick 2.15

Item {
    id: root

    property var model
    property bool hasProject: appState.sourceWidth > 1 && appState.sourceHeight > 1

    Rectangle {
        id: placeholder
        anchors.fill: parent
        color: "#333333"
        visible: !hasProject || videoImage.status !== Image.Ready

        Text {
            anchors.centerIn: parent
            text: "No project loaded"
            color: "#888888"
            font.pixelSize: 16
        }
    }

    Image {
        id: videoImage
        anchors.fill: parent
        source: hasProject ? "image://frame_source/" + appState.currentFrame + "?v=" + appState.projectVersion : ""
        fillMode: Image.PreserveAspectFit
        cache: false
    }

    Item {
        id: overlay
        readonly property real scaleX: (videoImage && appState.sourceWidth > 1) ? videoImage.paintedWidth / appState.sourceWidth : 1.0
        readonly property real scaleY: (videoImage && appState.sourceHeight > 1) ? videoImage.paintedHeight / appState.sourceHeight : 1.0

        x: (videoImage.width - videoImage.paintedWidth) / 2
        y: (videoImage.height - videoImage.paintedHeight) / 2
        width: videoImage.paintedWidth
        height: videoImage.paintedHeight
        clip: true

        Repeater {
        id: repeater
        model: root.model

        delegate: Rectangle {
            id: delegateRoot

            // The Repeater provides model data through the 'model' property in the delegate.
            // We create aliases here for clarity and to ensure they are correctly typed.
            readonly property int personId: model.personId !== undefined ? model.personId : -1
            readonly property var currentBoundingBox: model.currentBoundingBox

            x: currentBoundingBox ? currentBoundingBox.x * overlay.scaleX : -1000
            y: currentBoundingBox ? currentBoundingBox.y * overlay.scaleY : -1000
            width: currentBoundingBox ? currentBoundingBox.w * overlay.scaleX : 0
            height: currentBoundingBox ? currentBoundingBox.h * overlay.scaleY : 0
            
            visible: currentBoundingBox !== null

            readonly property bool isSelected: appState.selectedPersonIds.indexOf(personId) !== -1
            readonly property color personColor: (dark2palette && personId >= 0) ? dark2palette[personId % dark2palette.length] : "#CCCCCC"
            
            color: "transparent"
            border.width: isSelected ? 4 : 2
            border.color: isSelected ? "yellow" : personColor

            Rectangle {
                width: label.implicitWidth
                height: label.implicitHeight
                color: isSelected ? "yellow" : personColor

                // Position label above the box, but move it inside if it would go off-screen
                y: (delegateRoot.y < height) ? 0 : -height

                Text {
                    id: label
                    text: "person " + personId
                    font.bold: true
                    font.pixelSize: 14
                    color: isSelected ? "black" : "white"
                    padding: 2
                }
            }
        }
    }
    }
    
    MouseArea {
        anchors.fill: overlay
        onClicked: (mouse) => {
            var clickedPerson = -1
            // iterate children in reverse to find topmost
            for (var i = repeater.count - 1; i >= 0; i--) {
                var item = repeater.itemAt(i)
                if (item.visible && item.x <= mouse.x && mouse.x <= item.x + item.width && item.y <= mouse.y && mouse.y <= item.y + item.height) {
                    clickedPerson = item.personId
                    break
                }
            }
            
            var isModifier = (mouse.modifiers & Qt.ControlModifier) || (mouse.modifiers & Qt.MetaModifier) || (mouse.modifiers & Qt.AltModifier)

            if (clickedPerson !== -1) {
                if (isModifier) {
                    appState.updateSelection(clickedPerson, "toggle")
                } else {
                    appState.updateSelection(clickedPerson, "single")
                }
            } else {
                if (!isModifier) {
                    appState.clearSelection()
                }
            }
        }
    }
}
