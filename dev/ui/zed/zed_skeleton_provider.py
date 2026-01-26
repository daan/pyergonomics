"""Skeleton provider for live ZED body tracking data."""

import cv2
import numpy as np
from PySide6.QtCore import QObject, Property, Signal, Slot, QMutex, QMutexLocker, QSize
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider


class ZedFrameProvider(QQuickImageProvider):
    """Provides live ZED video frames to QML."""

    def __init__(self):
        super().__init__(QQuickImageProvider.Image)
        self._frame = None
        self._mutex = QMutex()

    def setFrame(self, bgra_array: np.ndarray):
        """Thread-safe frame update from tracker."""
        with QMutexLocker(self._mutex):
            h, w = bgra_array.shape[:2]
            rgb = cv2.cvtColor(bgra_array, cv2.COLOR_BGRA2RGB)
            self._frame = QImage(
                rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888
            ).copy()

    def requestImage(self, id: str, size: QSize, requestedSize: QSize):
        """Called by QML to get current frame."""
        with QMutexLocker(self._mutex):
            if self._frame:
                size.setWidth(self._frame.width())
                size.setHeight(self._frame.height())
                return self._frame
            return QImage()


class ZedSkeletonProvider(QObject):
    """Provides skeleton data to QML from live ZED tracking."""

    skeletonsChanged = Signal()
    boneConnectionsChanged = Signal()
    frameCountChanged = Signal()
    cameraInfoChanged = Signal()
    pausedChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._skeletons = []
        self._bone_connections = []
        self._frame_count = 0
        self._paused = False
        self._camera_fov = 60.0
        self._camera_aspect = 16.0 / 9.0
        self._camera_position = [0.0, 0.0, 1.0]  # Default 1m height
        # Full camera intrinsics for projection matrix
        self._fx = 500.0
        self._fy = 500.0
        self._cx = 640.0
        self._cy = 360.0
        self._image_width = 1280
        self._image_height = 720
        # Floor transform rotation as quaternion [w, x, y, z]
        self._floor_rotation = [1.0, 0.0, 0.0, 0.0]  # Identity
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

    def setCameraInfo(self, fov: float, aspect: float, position: list):
        """Set camera FOV, aspect, and position."""
        with QMutexLocker(self._mutex):
            self._camera_fov = fov
            self._camera_aspect = aspect
            self._camera_position = position
        self.cameraInfoChanged.emit()

    def setCameraIntrinsics(
        self, fx: float, fy: float, cx: float, cy: float, width: int, height: int
    ):
        """Set full camera intrinsics for projection matrix."""
        with QMutexLocker(self._mutex):
            self._fx = fx
            self._fy = fy
            self._cx = cx
            self._cy = cy
            self._image_width = width
            self._image_height = height
            self._camera_aspect = width / height
        self.cameraInfoChanged.emit()

    def setFloorRotation(self, quaternion: list):
        """Set floor transform rotation as quaternion [w, x, y, z]."""
        with QMutexLocker(self._mutex):
            self._floor_rotation = quaternion
        self.cameraInfoChanged.emit()

    @Property(float, notify=cameraInfoChanged)
    def cameraFov(self):
        with QMutexLocker(self._mutex):
            return self._camera_fov

    @Property(float, notify=cameraInfoChanged)
    def cameraAspect(self):
        with QMutexLocker(self._mutex):
            return self._camera_aspect

    @Property("QVariantList", notify=cameraInfoChanged)
    def cameraPosition(self):
        with QMutexLocker(self._mutex):
            return self._camera_position

    @Property(float, notify=cameraInfoChanged)
    def fx(self):
        with QMutexLocker(self._mutex):
            return self._fx

    @Property(float, notify=cameraInfoChanged)
    def fy(self):
        with QMutexLocker(self._mutex):
            return self._fy

    @Property(float, notify=cameraInfoChanged)
    def cx(self):
        with QMutexLocker(self._mutex):
            return self._cx

    @Property(float, notify=cameraInfoChanged)
    def cy(self):
        with QMutexLocker(self._mutex):
            return self._cy

    @Property(int, notify=cameraInfoChanged)
    def imageWidth(self):
        with QMutexLocker(self._mutex):
            return self._image_width

    @Property(int, notify=cameraInfoChanged)
    def imageHeight(self):
        with QMutexLocker(self._mutex):
            return self._image_height

    @Property("QVariantList", notify=cameraInfoChanged)
    def floorRotation(self):
        """Floor transform rotation as quaternion [w, x, y, z]."""
        with QMutexLocker(self._mutex):
            return self._floor_rotation

    @Property(bool, notify=pausedChanged)
    def paused(self):
        with QMutexLocker(self._mutex):
            return self._paused

    def setPaused(self, paused: bool):
        with QMutexLocker(self._mutex):
            self._paused = paused
        self.pausedChanged.emit()

    @Slot()
    def togglePause(self):
        with QMutexLocker(self._mutex):
            self._paused = not self._paused
        self.pausedChanged.emit()
