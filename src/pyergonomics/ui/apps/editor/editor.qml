import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import QtQuick3D
import QtQuick3D.Helpers
import PyeHelpers 0.1
import CvHelpers

ApplicationWindow {
    id: window
    width: 1024
    height: 768
    visible: true
    title: "Editor"
    color: "#333333"

    property int trackNameColumnWidth: 150
    property int visibilityColumnWidth: 50
    property font timelineFont: Qt.font({ pixelSize: 12 })

    // Assessment view state
    property bool showAssessmentView: appState.hasAssessment
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

    Component.onCompleted: updateSelectedPerson()

    Action {
        id: openAction
        text: "Open..."
        shortcut: "Ctrl+O"
        onTriggered: openDialog.open()
    }

    Action {
        id: saveAction
        text: "Save"
        shortcut: "Ctrl+S"
        onTriggered: appState.save_project()
    }

    Action {
        id: saveAsAction
        text: "Save As..."
        shortcut: "Ctrl+Shift+S"
        onTriggered: saveAsDialog.open()
    }

    Action {
        id: quitAction
        text: "Quit"
        shortcut: "Ctrl+Q"
        onTriggered: Qt.quit()
    }

    Action {
        id: toggleAssessmentAction
        text: "Assessment View"
        checkable: true
        checked: window.showAssessmentView
        enabled: appState.hasAssessment
        onTriggered: window.showAssessmentView = checked
    }

    menuBar: MenuBar {
        Menu {
            title: "File"
            MenuItem { action: openAction }
            MenuItem { action: saveAction }
            MenuItem { action: saveAsAction }
            MenuSeparator {}
            MenuItem { action: quitAction }
        }
        Menu {
            title: "View"
            MenuItem { action: toggleAssessmentAction }
        }
    }

    FileDialog {
        id: openDialog
        title: "Open Project"
        nameFilters: ["Project files (*.toml)"]
        onAccepted: {
            appState.load_project(selectedFile)
        }
    }

    FileDialog {
        id: saveAsDialog
        title: "Save Project As"
        fileMode: FileDialog.SaveFile
        nameFilters: ["Project files (*.toml)"]
        onAccepted: {
            appState.save_project_as(selectedFile)
        }
    }

    Shortcut {
        sequence: "Escape"
        onActivated: Qt.quit()
    }
    Shortcut {
        sequence: "Space"
        onActivated: appState.togglePlayPause()
    }

    Action {
        id: mergeAction
        text: "Merge Selected"
        shortcut: "m"
        onTriggered: appState.merge_selected_persons()
    }

    Action {
        id: deleteAction
        text: "Delete Selected"
        shortcut: "d"
        onTriggered: appState.delete_selected_persons()
    }

    Action {
        id: zoomToFitAction
        text: "Zoom to Fit"
        shortcut: "f"
        onTriggered: {
            if (personViewOnly.visible) personViewOnly.zoomToFit = true
            if (personViewCombined.visible) personViewCombined.zoomToFit = true
        }
    }

    SplitView {
        anchors.fill: parent
        orientation: Qt.Vertical

        Item {
            SplitView.fillHeight: true
            SplitView.preferredHeight: 400

            // Case a: Only video, no 3D data
            FrameView {
                anchors.fill: parent
                model: peopleFrameModel
                visible: appState.hasVideo && !appState.has3DData
            }

            // Case b: Only 3D data, no video
            PersonView {
                id: personViewOnly
                anchors.fill: parent
                visible: !appState.hasVideo && appState.has3DData

                Keys.onPressed: (event) => {
                    if (event.key === Qt.Key_F) {
                        personViewOnly.zoomToFit = true
                    }
                }
            }

            // Case c: Both video and 3D data
            SplitView {
                anchors.fill: parent
                orientation: Qt.Horizontal
                visible: appState.hasVideo && appState.has3DData

                FrameView {
                    SplitView.fillWidth: true
                    SplitView.preferredWidth: parent.width / 2
                    model: peopleFrameModel
                }

                PersonView {
                    id: personViewCombined
                    SplitView.fillWidth: true
                    SplitView.preferredWidth: parent.width / 2

                    Keys.onPressed: (event) => {
                        if (event.key === Qt.Key_F) {
                            personViewCombined.zoomToFit = true
                        }
                    }
                }
            }

            // Placeholder when no project is loaded
            Rectangle {
                anchors.fill: parent
                color: "#333333"
                visible: !appState.hasVideo && !appState.has3DData

                Text {
                    anchors.centerIn: parent
                    text: "No project loaded"
                    color: "#888888"
                    font.pixelSize: 16
                }
            }
        }

        // Assessment View (optional, shown when data available and enabled)
        AssessmentView {
            id: assessmentView
            SplitView.minimumHeight: 100
            SplitView.preferredHeight: 150
            visible: appState.hasAssessment && window.showAssessmentView

            manager: appState
            personId: window.selectedPersonId
            metrics: window.selectedPersonMetrics
            sidebarWidth: window.trackNameColumnWidth + window.visibilityColumnWidth + 20
        }

        ColumnLayout {
            id: timelineLayout
            spacing: 0
            SplitView.minimumHeight: 150
            SplitView.preferredHeight: 250

            Rectangle { // Header
                Layout.fillWidth: true
                height: 40
                color: "#444444"
                border.color: "#555555"

                RowLayout {
                    anchors.fill: parent
                    spacing: 10

                    Item {
                        Layout.preferredWidth: window.trackNameColumnWidth + window.visibilityColumnWidth + 10 
                        Layout.maximumWidth: Layout.preferredWidth
                        Layout.fillHeight: true
                        
                        Button {
                            anchors.centerIn: parent
                            text: appState.isPlaying ? "Pause" : "Play"
                            enabled: appState.totalFrames > 0
                            onClicked: appState.togglePlayPause()
                        }
                    }

                    SharedTimeline {
                        id: headerTimeline
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

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                
                ListView {
                    model: peopleModel
                    spacing: 1
                    
                    delegate: TrackView {
                        width: ListView.view.width
                        personId: model.personId
                        isVisible: model.isVisible
                        events: model.events
                        isSelected: appState.selectedPersonIds.indexOf(personId) !== -1
                        
                        trackNameColumnWidth: window.trackNameColumnWidth
                        visibilityColumnWidth: window.visibilityColumnWidth
                        timelineFont: window.timelineFont
                    }
                }
            }
        }
    }
}
