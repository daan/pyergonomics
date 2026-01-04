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

        // Graph Painter
        GraphPainter {
            id: graphPainter
            Layout.fillWidth: true
            Layout.fillHeight: true
            
            viewPosition: root.viewPosition
            pixelsPerFrame: root.pixelsPerFrame
            currentFrame: root.currentFrame
            metrics: root.metrics
            
            // Background grid lines (optional)
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
    }
}
