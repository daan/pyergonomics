import math

from PySide6.QtCore import Property, Signal, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtQuick import QQuickPaintedItem


class AxisPainter(QQuickPaintedItem):
    viewPositionChanged = Signal()
    visibleWidthChanged = Signal()
    totalFramesChanged = Signal()
    pixelsPerFrameChanged = Signal()
    fontChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._view_position = 0.0
        self._visible_width = 0.0
        self._total_frames = 3600
        self._pixels_per_frame = 2.0
        self._font = QFont("sans-serif", 10)

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

    @Property(QFont, notify=fontChanged)
    def font(self):
        return self._font

    @font.setter
    def font(self, value):
        if self._font != value:
            self._font = value
            self.fontChanged.emit()
            self.update()

    def paint(self, painter):
        painter.fillRect(self.boundingRect(), QColor("black"))

        if self.pixelsPerFrame <= 0:
            return

        # Draw valid frame range background
        start_x = (0 - self.viewPosition) * self.pixelsPerFrame
        width = self.totalFrames * self.pixelsPerFrame
        painter.fillRect(start_x, 0, width, self.height(), QColor("#444444"))

        painter.setFont(self._font)

        if self.visibleWidth <= 0:
            return

        start_frame = self.viewPosition
        end_frame = self.viewPosition + self.visibleWidth / self.pixelsPerFrame
        visible_duration_frames = end_frame - start_frame
        if visible_duration_frames <= 0:
            return

        # --- Tick interval logic ---
        target_tick_spacing_px = 100
        target_tick_interval_frames = target_tick_spacing_px / self.pixelsPerFrame
        if target_tick_interval_frames <= 0:
            return

        power = 10.0 ** math.floor(math.log10(target_tick_interval_frames))
        multipliers = [1, 2, 5, 10, 25, 50, 100, 250, 500, 1000]
        errors = [abs(m * power - target_tick_interval_frames) for m in multipliers]
        best_multiplier = multipliers[errors.index(min(errors))]
        major_interval = best_multiplier * power
        minor_interval = major_interval / 10.0

        if minor_interval < 1:
            minor_interval = 0

        # --- Drawing loop ---
        pen = QPen()

        # Minor ticks first
        if minor_interval > 0:
            pen.setColor(QColor("#666666"))
            painter.setPen(pen)
            first_minor_tick = math.floor(start_frame / minor_interval) * minor_interval
            f = first_minor_tick
            while f < end_frame:
                if f >= start_frame:
                    x = (f - self.viewPosition) * self.pixelsPerFrame
                    painter.drawLine(
                        QPointF(x, self.height() * 0.5), QPointF(x, self.height())
                    )
                f += minor_interval

        # Major ticks and labels on top
        if major_interval > 0:
            pen.setColor(QColor("grey"))
            painter.setPen(pen)
            first_major_tick = math.floor(start_frame / major_interval) * major_interval
            f = first_major_tick
            while f < end_frame:
                if f >= start_frame:
                    x = (f - self.viewPosition) * self.pixelsPerFrame
                    painter.drawLine(QPointF(x, 0), QPointF(x, self.height()))

                    painter.setPen(QColor("white"))
                    label = str(int(round(f)))
                    font_metrics = painter.fontMetrics()
                    label_width = font_metrics.horizontalAdvance(label)
                    text_y = (
                        self.height() - font_metrics.height()
                    ) / 2 + font_metrics.ascent()
                    painter.drawText(int(x - label_width / 2), int(text_y), label)
                    painter.setPen(pen)  # Restore pen for grey ticks
                f += major_interval
