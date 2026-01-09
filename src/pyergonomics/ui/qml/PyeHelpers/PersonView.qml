import QtQuick
import QtQuick.Layouts
import QtQuick3D
import QtQuick3D.Helpers
import PyeHelpers
import CvHelpers

View3D {
    id: root
    property bool zoomToFit: false
    
    onZoomToFitChanged: {
        if(zoomToFit) {
            const sphere = calculateBoundingSphereForAllSkeletons();
            if (sphere.radius > 0) {
                zoomToBoundingSphere(sphere.center, sphere.radius);
            }
            zoomToFit = false; // reset
        }
    }

    Layout.fillWidth: true
    Layout.fillHeight: true

    function distanceBetweenPoints(p1, p2) {
        const dx = p2.x - p1.x;
        const dy = p2.y - p1.y;
        const dz = p2.z - p1.z;
        return Math.sqrt(dx*dx + dy*dy + dz*dz);
    }

    function calculateBoundingSphereForAllSkeletons() {
        let min = null;
        let max = null;

        const skeletons = skeletonProvider.skeletons;
        console.log("Calculating bounding sphere for", skeletons.length, "skeletons");
        for (let i = 0; i < skeletons.length; ++i) {
            const skeleton = skeletons[i];
            const keypoints = skeleton.keypoints_3d;
            for (let j = 0; j < keypoints.length; ++j) {
                const p_array = keypoints[j];
                // Ignore non-visible or invalid points
                if (isNaN(p_array[0]) || isNaN(p_array[1]) || isNaN(p_array[2])) {
                    continue;
                }

                if (min === null) {
                    min = Qt.vector3d(p_array[0], p_array[1], p_array[2]);
                    max = Qt.vector3d(p_array[0], p_array[1], p_array[2]);
                } else {
                    min.x = Math.min(min.x, p_array[0]);
                    min.y = Math.min(min.y, p_array[1]);
                    min.z = Math.min(min.z, p_array[2]);
                    max.x = Math.max(max.x, p_array[0]);
                    max.y = Math.max(max.y, p_array[1]);
                    max.z = Math.max(max.z, p_array[2]);
                }
                print("Point:", p_array[0], p_array[1], p_array[2]);
            }
        }

        if (min === null) {
            return { center: Qt.vector3d(0, 0, 0), radius: 0 };
        }

        const center = min.plus(max).times(0.5);
        console.log("Sphere center:", center);
        const radius = distanceBetweenPoints(center, max);

        return { center: center, radius: radius };
    }

    function zoomToBoundingSphere(sphereCenter, sphereRadius) {
        const padding = 1.2;
        const radius = sphereRadius * padding;

        let fov = cameraNode.fieldOfView; // Vertical FOV in degrees
        let aspect = width / height;

        let halfAngleRad;
        if (aspect >= 1) { // Landscape or square, vertical FOV is limiting
            halfAngleRad = (fov / 2) * Math.PI / 180;
        } else { // Portrait, horizontal FOV is limiting
            let halfAngleVRad = (fov / 2) * Math.PI / 180;
            halfAngleRad = Math.atan(Math.tan(halfAngleVRad) * aspect);
        }

        const distance = radius / Math.tan(halfAngleRad);

        // Transform sphereCenter from z-up (pyergonomics) to y-up (QtQuick3D)
        // The rotationNode applies eulerRotation.x: -90, which transforms (x, y, z) -> (x, z, -y)
        const transformedCenter = Qt.vector3d(sphereCenter.x, sphereCenter.z, -sphereCenter.y);

        // Set the orbit controller's origin to the transformed center
        cameraOrigin.position = transformedCenter;

        // Preserve the camera's orientation by maintaining its direction
        // relative to the origin, but update its distance.
        let currentDir = cameraNode.position.normalized();
        // If the camera is at the origin, its direction is undefined.
        // This can happen at startup. Provide a default direction in that case.
        if (cameraNode.position.length() < 0.001) {
            currentDir = Qt.vector3d(0, 0, 5).normalized();
        }
        cameraNode.position = currentDir.times(distance);
    }


    environment: SceneEnvironment {
        clearColor: "#222222"
        backgroundMode: SceneEnvironment.Color
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: SceneEnvironment.High
    }

    camera: cameraNode

    Node {
		    id: cameraOrigin
        eulerRotation.x: -40
        PerspectiveCamera {
            id: cameraNode
            position: Qt.vector3d(0, 0, 5)
            clipFar: 100
            clipNear: 0.1
	        }
	    }
    OrbitCameraController {
        anchors.fill: parent
        camera: cameraNode
        origin: cameraOrigin
        panEnabled: true
    }

    DirectionalLight {
        eulerRotation.x: -45
        eulerRotation.y: -30
    }
	Node {
        id: sceneRoot

	    Grid {}

            Node {
                id: rotationNode
                // move from z-up (pyergonomics) to a y-up (qtquick3d) coordinate system
                eulerRotation.x: -90

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
