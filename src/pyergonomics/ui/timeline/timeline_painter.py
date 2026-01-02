import math

from PySide6.QtCore import Property, Signal, QPointF
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtQuick import QQuickPaintedItem


class TimelinePainter(QQuickPaintedItem):
    viewPositionChanged = Signal()
    visibleWidthChanged = Signal()
    totalFramesChanged = Signal()
    pixelsPerFrameChanged = Signal()
    currentFrameChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._view_position = 0.0
        self._visible_width = 0.0
        self._total_frames = 3600
        self._pixels_per_frame = 2.0
        self._current_frame = 0

    @Property(float, notify=viewPositionChanged)
    def viewPosition(self):
        return self._view_position

    @viewPosition.setter
    def viewPosition(self, value):
        if self._view_position != value:
            self._view_position = value
            self.viewPositionChanged.emit()
            self.update()

    @Property(float, notify=visibleWidthChanged)
    def visibleWidth(self):
        return self._visible_width

    @visibleWidth.setter
    def visibleWidth(self, value):
        if self._visible_width != value:
            self._visible_width = value
            self.visibleWidthChanged.emit()
            self.update()

    @Property(int, notify=totalFramesChanged)
    def totalFrames(self):
        return self._total_frames

    @totalFrames.setter
    def totalFrames(self, value):
        if self._total_frames != value:
            self._total_frames = value
            self.totalFramesChanged.emit()
            self.update()

    @Property(float, notify=pixelsPerFrameChanged)
    def pixelsPerFrame(self):
        return self._pixels_per_frame

    @pixelsPerFrame.setter
    def pixelsPerFrame(self, value):
        if self._pixels_per_frame != value:
            self._pixels_per_frame = value
            self.pixelsPerFrameChanged.emit()
            self.update()

    @Property(int, notify=currentFrameChanged)
    def currentFrame(self):
        return self._current_frame

    @currentFrame.setter
    def currentFrame(self, value):
        if self._current_frame != value:
            self._current_frame = value
            self.currentFrameChanged.emit()
            self.update()

    def paint(self, painter):
        painter.fillRect(self.boundingRect(), QColor("black"))

        if self.pixelsPerFrame <= 0 or self.totalFrames <= 0:
            return

        # Draw valid frame range background
        start_x = (0 - self.viewPosition) * self.pixelsPerFrame
        width = self.totalFrames * self.pixelsPerFrame
        painter.fillRect(start_x, 0, width, self.height(), QColor("#222222"))

        if self.visibleWidth <= 0:
            return

        pen = QPen(QColor("lightblue"))
        pen.setWidth(1)
        painter.setPen(pen)

        start_frame = self.viewPosition
        end_frame = self.viewPosition + self.visibleWidth / self.pixelsPerFrame
        print(
            f"TimelinePainter view: start_frame={start_frame:.2f}, end_frame={end_frame:.2f}"
        )

        if start_frame >= end_frame:
            return

        num_segments = self.visibleWidth / 10 if self.visibleWidth > 0 else 1
        duration_frames = self.totalFrames
        frame_step = (end_frame - start_frame) / num_segments
        if frame_step <= 0:
            return

        points = []
        for i in range(int(num_segments) + 1):
            f = start_frame + (i * frame_step)

            amplitude = f / duration_frames if duration_frames > 0 else 0
            v = amplitude * math.sin(f * 0.1)

            x = (f - self.viewPosition) * self.pixelsPerFrame
            y = (1 - v) * self.height() / 2

            points.append(QPointF(x, y))

        if points:
            painter.drawPolyline(points)

        # Draw playhead line
        if self.currentFrame >= start_frame and self.currentFrame <= end_frame:
            playhead_x = (self.currentFrame - self.viewPosition) * self.pixelsPerFrame
            pen = QPen(QColor("dodgerblue"))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawLine(QPointF(playhead_x, 0), QPointF(playhead_x, self.height()))
