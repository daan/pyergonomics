import QtQuick
import QtQuick.Layouts
import PyeHelpers 0.1

Item {
    id: root
    Layout.fillWidth: true
    Layout.fillHeight: true
    clip: true

    signal panRequested(real frameDelta)
    signal zoomRequested(real newPixelsPerFrame, real frameAtMouse)

    property var manager
    property real viewPosition: 0.0
    property real pixelsPerFrame: 2.0

    property font timelineFont: Qt.font({ pixelSize: 12 })

    readonly property int totalFrames: manager ? manager.totalFrames : 0
    readonly property real minPixelsPerFrame: (root.width > 0 && totalFrames > 0) ? (root.width / 2) / totalFrames : 0.01
    readonly property real maxPixelsPerFrame: 100.0
    
    AxisPainter {
        id: axisPainter
        anchors.fill: parent
        viewPosition: root.viewPosition
        visibleWidth: root.width
        totalFrames: root.totalFrames
        pixelsPerFrame: root.pixelsPerFrame
        font: root.timelineFont
    }

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
                if (root.pixelsPerFrame > 0) {
                    root.panRequested(-deltaX / root.pixelsPerFrame);
                }
                lastPos = Qt.point(mouse.x, mouse.y)
            }
        }

        onWheel: (wheel) => {
            var oldPixelsPerFrame = root.pixelsPerFrame;
            var newPixelsPerFrame;

            if (wheel.angleDelta.y > 0) {
                newPixelsPerFrame = Math.min(root.maxPixelsPerFrame, root.pixelsPerFrame * 1.2);
            } else {
                newPixelsPerFrame = Math.max(root.minPixelsPerFrame, root.pixelsPerFrame / 1.2);
            }

            if (oldPixelsPerFrame !== newPixelsPerFrame) {
                var frameAtMouse = root.viewPosition + wheel.x / oldPixelsPerFrame;
                root.zoomRequested(newPixelsPerFrame, frameAtMouse);
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

    Rectangle {
        id: playhead
        
        x: (manager.currentFrame - root.viewPosition) * root.pixelsPerFrame - width / 2
        y: 0
        width: frameNumberText.implicitWidth + 16
        height: parent.height
        color: Qt.rgba(0.1, 0.5, 1.0, 0.7)
        radius: 4
        border.color: "lightblue"
        visible: manager && x > -width && x < root.width

        Text {
            id: frameNumberText
            anchors.centerIn: parent
            text: manager ? manager.currentFrame : 0
            color: "white"
            font: root.timelineFont
        }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton

            property real dragOffset: 0

            onPressed: (mouse) => {
                if (!manager) return;
                dragOffset = mouse.x - (playhead.width / 2)
                manager.startScrubbing();
                console.log("Playhead drag started.");
            }

            onPositionChanged: (mouse) => {
                if (mouse.buttons & Qt.LeftButton) {
                    if (!manager || root.pixelsPerFrame <= 0) return;
                    
                    var mouseInRoot = mapToItem(root, mouse.x, mouse.y)
                    var newPlayheadCenterX = mouseInRoot.x - dragOffset
                    var newFrame = root.viewPosition + newPlayheadCenterX / root.pixelsPerFrame;

                    var clampedFrame = Math.round(Math.max(0, Math.min(manager.totalFrames - 1, newFrame)));
                    if (manager.currentFrame !== clampedFrame) {
                        manager.currentFrame = clampedFrame;
                    }
                }
            }

            onReleased: (mouse) => {
                if (!manager) return;
                manager.stopScrubbing();
                console.log("Playhead drag released at frame:", manager.currentFrame);
            }
        }
    }
}
