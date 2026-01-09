import QtQuick
import QtQuick.Layouts
import PyeHelpers 0.1

Item {
    id: root

    property int personId: -1
    property var metrics: null

    property var manager // AppState

    // Sync properties
    property real viewPosition: manager ? manager.viewPosition : 0
    property real pixelsPerFrame: manager ? manager.pixelsPerFrame : 10
    property int totalFrames: manager ? manager.totalFrames : 100
    property int currentFrame: manager ? manager.currentFrame : 0

    property int sidebarWidth: 0

    // Zoom limits
    readonly property real minPixelsPerFrame: (graphPainter.width > 0 && totalFrames > 0) ? (graphPainter.width / 2) / totalFrames : 0.01
    readonly property real maxPixelsPerFrame: 100.0

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // Sidebar for Y-axis labels
        Item {
            Layout.preferredWidth: root.sidebarWidth
            Layout.maximumWidth: root.sidebarWidth
            Layout.fillHeight: true
            clip: true

            // Simple labels for 0, 90, 180 degrees
            Repeater {
                model: [180, 90, 0]
                delegate: Text {
                    text: modelData + "°"
                    color: "#AAAAAA"
                    font.pixelSize: 10
                    anchors.right: parent.right
                    anchors.rightMargin: 5
                    // y position: 180 is at 0, 0 is at height.
                    y: (1 - modelData/180.0) * parent.height - height/2
                }
            }
        }

        // Graph Painter with interaction
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            GraphPainter {
                id: graphPainter
                anchors.fill: parent

                viewPosition: root.viewPosition
                pixelsPerFrame: root.pixelsPerFrame
                currentFrame: root.currentFrame
                metrics: root.metrics

                // Background grid lines
                Rectangle {
                    anchors.fill: parent
                    color: "transparent"
                    z: -1

                    Column {
                        anchors.fill: parent
                        Repeater {
                            model: 2 // Lines at 90 and 0 (top is 180)
                            delegate: Rectangle {
                                width: parent.width
                                height: 1
                                color: "#444444"
                                y: (index + 1) * (parent.height / 2)
                            }
                        }
                    }
                }
            }

            // Pan, click, and zoom interaction
            MouseArea {
                id: panZoomArea
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton

                property point lastPos: Qt.point(0, 0)

                onPressed: (mouse) => {
                    if (mouse.source === Qt.MouseEventNotSynthesized) {
                        lastPos = Qt.point(mouse.x, mouse.y)
                    }
                }

                onPositionChanged: (mouse) => {
                    if (mouse.buttons & Qt.LeftButton && mouse.source === Qt.MouseEventNotSynthesized) {
                        var deltaX = mouse.x - lastPos.x;
                        if (root.pixelsPerFrame > 0 && manager) {
                            manager.pan(-deltaX / root.pixelsPerFrame);
                        }
                        lastPos = Qt.point(mouse.x, mouse.y)
                    }
                }

                onWheel: (wheel) => {
                    if (!manager) return;
                    var oldPixelsPerFrame = root.pixelsPerFrame;
                    var newPixelsPerFrame;

                    if (wheel.angleDelta.y > 0) {
                        newPixelsPerFrame = Math.min(root.maxPixelsPerFrame, root.pixelsPerFrame * 1.2);
                    } else {
                        newPixelsPerFrame = Math.max(root.minPixelsPerFrame, root.pixelsPerFrame / 1.2);
                    }

                    if (oldPixelsPerFrame !== newPixelsPerFrame) {
                        var frameAtMouse = root.viewPosition + wheel.x / oldPixelsPerFrame;
                        manager.zoom(newPixelsPerFrame, frameAtMouse);
                    }
                }

                onClicked: (mouse) => {
                    if (mouse.button === Qt.LeftButton) {
                        if (root.pixelsPerFrame > 0 && manager) {
                            var frame = root.viewPosition + (mouse.x / root.pixelsPerFrame);
                            var newFrame = Math.round(Math.max(0, Math.min(manager.totalFrames - 1, frame)));
                            manager.currentFrame = newFrame;
                        }
                    }
                }
            }

            // Playhead
            Rectangle {
                id: playhead
                x: (root.currentFrame - root.viewPosition) * root.pixelsPerFrame
                width: 2
                height: parent.height
                color: Qt.rgba(0.1, 0.5, 1.0, 0.9)
                visible: manager && x > -width && x < parent.width

                MouseArea {
                    anchors.fill: parent
                    anchors.margins: -4 // Easier to grab
                    acceptedButtons: Qt.LeftButton
                    cursorShape: Qt.SizeHorCursor

                    property real dragStartX: 0

                    onPressed: (mouse) => {
                        if (!manager) return;
                        dragStartX = mouse.x
                        manager.startScrubbing();
                    }

                    onPositionChanged: (mouse) => {
                        if (mouse.buttons & Qt.LeftButton) {
                            if (!manager || root.pixelsPerFrame <= 0) return;

                            var deltaX = mouse.x - dragStartX
                            var newPlayheadX = playhead.x + deltaX
                            var newFrame = root.viewPosition + newPlayheadX / root.pixelsPerFrame;

                            var clampedFrame = Math.round(Math.max(0, Math.min(manager.totalFrames - 1, newFrame)));
                            if (manager.currentFrame !== clampedFrame) {
                                manager.currentFrame = clampedFrame;
                            }
                        }
                    }

                    onReleased: (mouse) => {
                        if (!manager) return;
                        manager.stopScrubbing();
                    }
                }
            }
        }
    }
}
