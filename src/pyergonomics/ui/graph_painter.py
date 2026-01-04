from PySide6.QtCore import Property, Signal, QPointF, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QPolygonF
from PySide6.QtQuick import QQuickPaintedItem

class GraphPainter(QQuickPaintedItem):
    viewPositionChanged = Signal()
    pixelsPerFrameChanged = Signal()
    currentFrameChanged = Signal()
    metricsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._view_position = 0.0
        self._pixels_per_frame = 10.0
        self._current_frame = 0
        self._metrics = {}
        
        # Colors for the different metrics
        self.colors = {
            "trunk_bending": QColor("#1b9e77"),
            "trunk_side_bending": QColor("#d95f02"),
            "trunk_twist": QColor("#7570b3")
        }
        
        # Optimize painting
        self.setRenderTarget(QQuickPaintedItem.FramebufferObject)

    @Property(float, notify=viewPositionChanged)
    def viewPosition(self):
        return self._view_position

    @viewPosition.setter
    def viewPosition(self, value):
        if self._view_position != value:
            self._view_position = value
            self.viewPositionChanged.emit()
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

    @Property("QVariantMap", notify=metricsChanged)
    def metrics(self):
        return self._metrics

    @metrics.setter
    def metrics(self, value):
        if self._metrics != value:
            self._metrics = value
            self.metricsChanged.emit()
            self.update()

    def paint(self, painter):
        if self.pixelsPerFrame <= 0:
            return
        
        width = self.width()
        height = self.height()
        
        # Y axis range: 0 to 180 degrees
        y_min = 0
        y_max = 180
        y_range = y_max - y_min
        if y_range == 0: y_range = 1
        
        # Helper to map frame, value to screen x, y
        def map_point(frame, value):
            x = (frame - self.viewPosition) * self.pixelsPerFrame
            # Flip Y (0 at bottom)
            y = height - ((value - y_min) / y_range * height)
            return QPointF(x, y)

        # Draw metrics
        if self._metrics:
            painter.setRenderHint(QPainter.Antialiasing)
            
            visible_start_frame = self.viewPosition
            visible_end_frame = self.viewPosition + width / self.pixelsPerFrame
            
            # Buffer to ensure lines entering/leaving screen are drawn
            buffer_frames = 100 
            
            for key, points in self._metrics.items():
                if key not in self.colors:
                    continue
                
                if not points:
                    continue

                pen = QPen(self.colors[key])
                pen.setWidth(2)
                painter.setPen(pen)
                
                # Filter points to visible range
                screen_points = []
                
                # Assuming points are sorted by frame (x)
                for p in points:
                    frame = p.x()
                    if frame < visible_start_frame - buffer_frames:
                        continue
                    if frame > visible_end_frame + buffer_frames:
                        # Add one last point off-screen to complete the line segment
                        screen_points.append(map_point(frame, p.y()))
                        break
                        
                    screen_points.append(map_point(frame, p.y()))
                
                if len(screen_points) > 1:
                    painter.drawPolyline(screen_points)

        # Draw playhead
        playhead_x = (self.currentFrame - self.viewPosition) * self.pixelsPerFrame
        if -2 <= playhead_x <= width + 2:
            pen = QPen(QColor("white"))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(QPointF(playhead_x, 0), QPointF(playhead_x, height))
