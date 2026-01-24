"""Skeleton provider for live ZED body tracking data."""

from PySide6.QtCore import QObject, Property, Signal, Slot, QMutex, QMutexLocker


class ZedSkeletonProvider(QObject):
    """Provides skeleton data to QML from live ZED tracking."""

    skeletonsChanged = Signal()
    boneConnectionsChanged = Signal()
    frameCountChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._skeletons = []
        self._bone_connections = []
        self._frame_count = 0
        self._mutex = QMutex()

    def setSkeletons(self, skeletons_list: list):
        """Thread-safe update of skeleton data."""
        with QMutexLocker(self._mutex):
            self._skeletons = skeletons_list
            self._frame_count += 1
        self.skeletonsChanged.emit()
        self.frameCountChanged.emit()

    def setBoneConnections(self, bones: list):
        """Thread-safe update of bone connections."""
        with QMutexLocker(self._mutex):
            self._bone_connections = list(bones)
        self.boneConnectionsChanged.emit()

    @Property("QVariantList", notify=skeletonsChanged)
    def skeletons(self):
        with QMutexLocker(self._mutex):
            return self._skeletons

    @Property("QVariantList", notify=boneConnectionsChanged)
    def boneConnections(self):
        with QMutexLocker(self._mutex):
            return self._bone_connections

    @Property(int, notify=frameCountChanged)
    def frameCount(self):
        with QMutexLocker(self._mutex):
            return self._frame_count
