import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import PyeHelpers 0.1

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

    menuBar: MenuBar {
        Menu {
            title: "File"
            MenuItem { action: openAction }
            MenuItem { action: saveAction }
            MenuItem { action: saveAsAction }
            MenuSeparator {}
            MenuItem { action: quitAction }
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

    SplitView {
        anchors.fill: parent
        orientation: Qt.Vertical

        FrameView {
            SplitView.fillHeight: true
            SplitView.preferredHeight: 400
            model: peopleFrameModel
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
