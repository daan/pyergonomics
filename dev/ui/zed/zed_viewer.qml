import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick3D
import QtQuick3D.Helpers
import PyeHelpers
import CvHelpers

ApplicationWindow {
    id: window
    visible: true
    width: 1280
    height: 720
    title: "ZED Body Tracking Viewer"
    color: "#1a1a1a"

    // Camera mode: false = orbit camera, true = ZED camera with video
    property bool useZedCamera: false
    // Debug mode: show ZED SDK's 2D keypoints as reference
    property bool showDebugOverlay: false

    // Handle ESC key to quit
    Shortcut {
        sequence: "Escape"
        onActivated: Qt.quit()
    }

    // Camera switching shortcuts
    Shortcut {
        sequence: "1"
        onActivated: {
            if (useZedCamera) {
                cameraOrigin.position = zedCameraNode.position
                cameraOrigin.rotation = zedCameraNode.rotation
                cameraNode.position = Qt.vector3d(0, 0, 0)
            }
            useZedCamera = false
        }
    }
    Shortcut {
        sequence: "2"
        onActivated: useZedCamera = true
    }
    // Debug overlay toggle
    Shortcut {
        sequence: "D"
        onActivated: showDebugOverlay = !showDebugOverlay
    }
    // Pause/resume
    Shortcut {
        sequence: "Space"
        onActivated: skeletonProvider.togglePause()
    }

    // Build OpenGL projection matrix from ZED camera intrinsics
    function buildProjectionMatrix() {
        var fx = skeletonProvider.fx
        var fy = skeletonProvider.fy
        var cx = skeletonProvider.cx
        var cy = skeletonProvider.cy
        var w = skeletonProvider.imageWidth
        var h = skeletonProvider.imageHeight
        var near = 0.1
        var far = 100.0

        var A = -(far + near) / (far - near)
        var B = -2 * far * near / (far - near)

        // OpenGL projection matrix from camera intrinsics
        // Qt.matrix4x4 takes row-major order
        return Qt.matrix4x4(
            2*fx/w,       0,            (w - 2*cx)/w,   0,
            0,            2*fy/h,       (2*cy - h)/h,   0,
            0,            0,            A,              B,
            0,            0,            -1,             0
        )
    }

    Item {
        anchors.fill: parent

        // Video background - constrained to ZED aspect ratio
        Item {
            id: zedViewport
            visible: useZedCamera
            width: Math.min(parent.width, parent.height * skeletonProvider.cameraAspect)
            height: Math.min(parent.height, parent.width / skeletonProvider.cameraAspect)
            anchors.centerIn: parent

            Image {
                id: videoImage
                anchors.fill: parent
                source: useZedCamera ? "image://zed_frame/0?v=" + skeletonProvider.frameCount : ""
                cache: false
            }

            // Debug overlay: draw ZED SDK's 2D keypoints as cyan circles
            // This shows where ZED thinks the keypoints are in the image
            Repeater {
                model: showDebugOverlay && skeletonProvider.skeletons.length > 0 ? skeletonProvider.skeletons[0].keypoints_2d : []

                Rectangle {
                    required property var modelData
                    required property int index
                    // Scale from image coords to viewport coords
                    x: modelData[0] * zedViewport.width / skeletonProvider.imageWidth - 4
                    y: modelData[1] * zedViewport.height / skeletonProvider.imageHeight - 4
                    width: 8
                    height: 8
                    radius: 4
                    color: "cyan"
                    border.color: "black"
                    border.width: 1
                    visible: modelData[0] > 0 && modelData[1] > 0

                    // Show keypoint index
                    Text {
                        anchors.left: parent.right
                        anchors.leftMargin: 2
                        text: index
                        color: "cyan"
                        font.pixelSize: 10
                    }
                }
            }
        }

        View3D {
            id: view3d
            // In ZED mode: match zedViewport size; else: fill parent
            width: useZedCamera ? zedViewport.width : parent.width
            height: useZedCamera ? zedViewport.height : parent.height
            anchors.centerIn: parent
            camera: useZedCamera ? zedCamera : cameraNode

            environment: SceneEnvironment {
                clearColor: useZedCamera ? "transparent" : "#222222"
                backgroundMode: useZedCamera ? SceneEnvironment.Transparent : SceneEnvironment.Color
                antialiasingMode: SceneEnvironment.MSAA
                antialiasingQuality: SceneEnvironment.High
            }

            // Orbit camera setup
            Node {
                id: cameraOrigin
                eulerRotation.x: -30
                PerspectiveCamera {
                    id: cameraNode
                    position: Qt.vector3d(0, 0, 5)
                    clipFar: 100
                    clipNear: 0.1
                }
            }

            OrbitCameraController {
                id: orbitController
                anchors.fill: parent
                camera: cameraNode
                origin: cameraOrigin
                panEnabled: true
            }

            // Catch drag/wheel in ZED mode to switch to orbit
            MouseArea {
                anchors.fill: parent
                visible: useZedCamera
                acceptedButtons: Qt.AllButtons

                function switchToOrbit() {
                    cameraOrigin.position = zedCameraNode.position
                    cameraOrigin.rotation = zedCameraNode.rotation
                    cameraNode.position = Qt.vector3d(0, 0, 0)
                    useZedCamera = false
                }

                onPositionChanged: (mouse) => { switchToOrbit() }
                onWheel: (wheel) => { switchToOrbit(); wheel.accepted = false }
            }

            DirectionalLight {
                eulerRotation.x: -45
                eulerRotation.y: -30
            }

            Node {
                id: sceneRoot

                Grid {}

                // ZED camera (outside rotationNode, uses QtQuick3D Y-up coords directly)
                // Position and rotation are converted from ZED Z-up to QtQuick3D Y-up
                Node {
                    id: zedCameraNode
                    // Convert position from Z-up to Y-up: (x, y, z) -> (x, z, -y)
                    position: Qt.vector3d(
                        skeletonProvider.cameraPosition[0] || 0,
                        skeletonProvider.cameraPosition[2] || 1,
                        -(skeletonProvider.cameraPosition[1] || 0)
                    )
                    // Rotation: floor quaternion combined with coord system conversion
                    // Floor rotation is in Z-up, we need to convert to Y-up and look along -Z
                    rotation: {
                        var q = skeletonProvider.floorRotation
                        var floorQuat = Qt.quaternion(q[0] || 1, q[1] || 0, q[2] || 0, q[3] || 0)
                        // Rotation to convert Z-up to Y-up: -90° around X
                        var zupToYup = Qt.quaternion(0.7071068, -0.7071068, 0, 0)
                        // Rotation to look along -Z in QtQuick3D (camera default)
                        // Combined: zupToYup * floorQuat * (90° around X to look forward)
                        var lookForward = Qt.quaternion(0.7071068, 0.7071068, 0, 0)
                        return zupToYup.times(floorQuat).times(lookForward)
                    }

                    CustomCamera {
                        id: zedCamera
                        projection: buildProjectionMatrix()
                    }
                }

                // Coordinate system transform: Z-up (ZED) to Y-up (QtQuick3D)
                Node {
                    id: rotationNode
                    eulerRotation.x: -90

                    // Camera frustum visualization (only in orbit mode)
                    Node {
                        id: cameraFrustum
                        visible: !useZedCamera
                        position: Qt.vector3d(
                            skeletonProvider.cameraPosition[0] || 0,
                            skeletonProvider.cameraPosition[1] || 0,
                            skeletonProvider.cameraPosition[2] || 1
                        )
                        eulerRotation.x: 90

                        Frustum {
                            fov: skeletonProvider.cameraFov
                            aspectRatio: skeletonProvider.cameraAspect
                            scale: 0.3
                        }
                    }

                    // Skeletons
                    Repeater3D {
                        model: skeletonProvider.skeletons
                        delegate: Skeleton3D {
                            pose: modelData.keypoints_3d
                            boneConnections: skeletonProvider.boneConnections
                            personId: modelData.personId
                            isSelected: appState.selectedPersonIds.indexOf(modelData.personId) !== -1
                        }
                    }
                }
            }
        }
    }

    // Zoom to fit button (only in orbit mode)
    Button {
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.margins: 10
        text: "Zoom to Fit"
        visible: !useZedCamera
        onClicked: {
            cameraOrigin.position = Qt.vector3d(0, 1, 0)
            cameraNode.position = Qt.vector3d(0, 0, 5)
        }
    }

    // Info overlay
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 10
        color: "#80000000"
        radius: 4
        width: infoColumn.width + 16
        height: infoColumn.height + 12

        Column {
            id: infoColumn
            anchors.centerIn: parent
            spacing: 4

            Label {
                color: "white"
                text: "Frame: " + skeletonProvider.frameCount
                font.pixelSize: 14
                font.family: "monospace"
            }
            Label {
                color: "white"
                text: "Skeletons: " + skeletonProvider.skeletons.length
                font.pixelSize: 14
                font.family: "monospace"
            }
            Label {
                color: useZedCamera ? "#88ff88" : "#aaaaaa"
                text: "Camera: " + (useZedCamera ? "ZED (2)" : "Orbit (1)")
                font.pixelSize: 12
                font.family: "monospace"
            }
            Label {
                visible: showDebugOverlay
                color: "#88ffff"
                text: "Debug: 2D keypoints (cyan)"
                font.pixelSize: 12
                font.family: "monospace"
            }
            Label {
                color: "#aaaaaa"
                text: "FOV: " + skeletonProvider.cameraFov.toFixed(1) + "°"
                font.pixelSize: 12
                font.family: "monospace"
                visible: !useZedCamera
            }
        }
    }

    // Keyboard hint
    Label {
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.margins: 10
        color: "#80ffffff"
        text: "1: Orbit | 2: ZED | D: Debug | Space: Pause | ESC: Exit"
        font.pixelSize: 12
    }

    // Pause indicator
    Label {
        anchors.centerIn: parent
        visible: skeletonProvider.paused
        text: "PAUSED"
        color: "white"
        font.pixelSize: 48
        font.bold: true
        style: Text.Outline
        styleColor: "black"
    }
}
