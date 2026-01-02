import QtQuick
import QtQuick3D
import PyeHelpers 1.0

Node {
    id: root
    property var pose: []
    property var boneConnections: []
    property int personId: -1
    property bool isSelected: false

    readonly property color personColor: (dark2palette && personId >= 0) ? dark2palette[personId % dark2palette.length] : "#CCCCCC"
    readonly property color finalColor: isSelected ? "yellow" : personColor

    Model {
        geometry: SkeletonGeometry {
            pose: root.pose
            boneConnections: root.boneConnections
        }
        materials: PrincipledMaterial {
            baseColor: root.finalColor
            lighting: PrincipledMaterial.NoLighting
        }
    }
}
