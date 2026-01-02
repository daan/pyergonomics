import QtQuick

Item {
    id: root
    clip: true

    property real viewPosition: 0.0
    property real pixelsPerFrame: 2.0
    property int totalFrames: 0
    property int currentFrame: 0
    property var intervals: []
    property int personId: -1

    Rectangle {
        anchors.fill: parent
        color: "black"
    }

    Item {
        id: content
        x: -root.viewPosition * root.pixelsPerFrame
        width: root.totalFrames * root.pixelsPerFrame
        height: parent.height

        Rectangle {
            anchors.fill: parent
            color: "#444444"
        }

        Repeater {
            model: root.intervals
            delegate: Rectangle {
                // modelData is [start_frame, end_frame]
                x: modelData[0] * root.pixelsPerFrame
                y: 4
                width: (modelData[1] - modelData[0] + 1) * root.pixelsPerFrame
                height: parent.height - 8
                color: (root.personId >= 0 && dark2palette) ? dark2palette[root.personId % dark2palette.length] : "gray"
            }
        }

        Rectangle { // Playhead line
            id: playheadLine
            x: root.currentFrame * root.pixelsPerFrame
            width: 1
            height: parent.height
            color: "dodgerblue"
            visible: root.currentFrame >= 0
        }
    }
}
