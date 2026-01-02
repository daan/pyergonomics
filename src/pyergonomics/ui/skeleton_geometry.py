import numpy as np
from PySide6.QtCore import QByteArray, Property, Signal
from PySide6.QtGui import QVector3D
from PySide6.QtQuick3D import QQuick3DGeometry


class SkeletonGeometry(QQuick3DGeometry):
    poseChanged = Signal()
    boneConnectionsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pose = []
        self._bone_connections = []
        self.updateData()

    @Property('QVariantList', notify=poseChanged)
    def pose(self):
        return self._pose

    @pose.setter
    def pose(self, value):
        if self._pose != value:
            self._pose = value
            self.poseChanged.emit()
            self.updateData()

    @Property('QVariantList', notify=boneConnectionsChanged)
    def boneConnections(self):
        return self._bone_connections

    @boneConnections.setter
    def boneConnections(self, value):
        if self._bone_connections != value:
            self._bone_connections = value
            self.boneConnectionsChanged.emit()
            self.updateData()

    def is_point_visible(self, p):
        return p[0] != 0 or p[1] != 0 or p[2] != 0

    def updateData(self):
        self.clear()

        if not self._pose or not self._bone_connections:
            self.setBounds(QVector3D(0, 0, 0), QVector3D(0, 0, 0))
            return

        vertices = []
        min_bound = [float('inf')] * 3
        max_bound = [float('-inf')] * 3

        for conn in self._bone_connections:
            p1_idx, p2_idx = conn[0], conn[1]

            if p1_idx < len(self._pose) and p2_idx < len(self._pose):
                p1 = self._pose[p1_idx]
                p2 = self._pose[p2_idx]

                if self.is_point_visible(p1) and self.is_point_visible(p2):
                    vertices.extend(p1)
                    vertices.extend(p2)

                    for i in range(3):
                        min_bound[i] = min(min_bound[i], p1[i], p2[i])
                        max_bound[i] = max(max_bound[i], p1[i], p2[i])

        if not vertices:
            self.setBounds(QVector3D(0, 0, 0), QVector3D(0, 0, 0))
            return

        vertices_np = np.array(vertices, dtype=np.float32)
        vertex_data = QByteArray(vertices_np.tobytes())
        self.setVertexData(vertex_data)
        self.setStride(3 * vertices_np.itemsize)

        bounds_min = QVector3D(min_bound[0], min_bound[1], min_bound[2])
        bounds_max = QVector3D(max_bound[0], max_bound[1], max_bound[2])
        self.setBounds(bounds_min, bounds_max)

        self.setPrimitiveType(QQuick3DGeometry.PrimitiveType.Lines)

        self.addAttribute(QQuick3DGeometry.Attribute.PositionSemantic,
                          0,
                          QQuick3DGeometry.Attribute.F32Type)

        indices = np.arange(len(vertices) // 3, dtype=np.uint32)
        index_data = QByteArray(indices.tobytes())
        self.setIndexData(index_data)

        self.addAttribute(QQuick3DGeometry.Attribute.IndexSemantic,
                          0,
                          QQuick3DGeometry.Attribute.U32Type)
