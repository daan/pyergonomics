import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import PyeHelpers 0.1

ApplicationWindow {
    id: window
    width: 1024
    height: 768
    visible: true
    title: "Assessment View"
    color: "#333333"

    property font timelineFont: Qt.font({ pixelSize: 12 })
    property int sidebarWidth: 150

    Shortcut {
        sequence: "Escape"
        onActivated: Qt.quit()
    }
    Shortcut {
        sequence: "Space"
        onActivated: appState.togglePlayPause()
    }

    // Helper to get metrics for selected person
    property var selectedPersonMetrics: null
    property int selectedPersonId: -1

    Connections {
        target: appState
        function onSelectedPersonIdsChanged() {
            updateSelectedPerson()
        }
    }

    function updateSelectedPerson() {
        if (appState.selectedPersonIds.length > 0) {
            var pid = appState.selectedPersonIds[0]
            selectedPersonId = pid
            
            // Find index in model
            for (var i = 0; i < personModel.rowCount(); i++) {
                var id = personModel.getPersonId(i)
                if (id === pid) {
                    selectedPersonMetrics = personModel.getMetrics(i)
                    return
                }
            }
        } else {
            selectedPersonId = -1
            selectedPersonMetrics = null
        }
    }
    
    // Initial update
    Component.onCompleted: updateSelectedPerson()

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Header / Timeline
        Rectangle {
            Layout.fillWidth: true
            height: 40
            color: "#444444"
            border.color: "#555555"

            RowLayout {
                anchors.fill: parent
                spacing: 0

                // Sidebar
                Item {
                    Layout.preferredWidth: window.sidebarWidth
                    Layout.maximumWidth: window.sidebarWidth
                    Layout.fillHeight: true
                    
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 5
                        spacing: 10
                        
                        Button {
                            text: appState.isPlaying ? "Pause" : "Play"
                            enabled: appState.totalFrames > 0
                            onClicked: appState.togglePlayPause()
                        }
                        
                        Label {
                            text: selectedPersonId >= 0 ? "Person " + selectedPersonId : "No Selection"
                            color: "white"
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                        }
                    }
                }

                SharedTimeline {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    manager: appState
                    viewPosition: appState.viewPosition
                    pixelsPerFrame: appState.pixelsPerFrame
                    timelineFont: window.timelineFont

                    onPanRequested: (frameDelta) => appState.pan(frameDelta)
                    onZoomRequested: (newPixelsPerFrame, frameAtMouse) => appState.zoom(newPixelsPerFrame, frameAtMouse)
                }
            }
        }

        // Assessment View
        AssessmentView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            
            manager: appState
            personId: selectedPersonId
            metrics: selectedPersonMetrics
            sidebarWidth: window.sidebarWidth
            
            visible: selectedPersonId >= 0
        }
        
        Text {
            visible: selectedPersonId < 0
            text: "Select a person to view assessment"
            color: "gray"
            font.pixelSize: 20
            Layout.alignment: Qt.AlignCenter
        }
        
        // Person Selector (Simple list to allow selection)
        ListView {
            Layout.fillWidth: true
            Layout.preferredHeight: 100
            orientation: ListView.Horizontal
            model: personModel
            spacing: 5
            clip: true
            
            delegate: Rectangle {
                width: 80
                height: 80
                color: appState.selectedPersonIds.indexOf(personId) !== -1 ? "dodgerblue" : "#555555"
                border.color: "white"
                radius: 4
                
                Text {
                    anchors.centerIn: parent
                    text: "P " + personId
                    color: "white"
                }
                
                MouseArea {
                    anchors.fill: parent
                    onClicked: appState.updateSelection(personId, "single")
                }
            }
        }
    }
}
