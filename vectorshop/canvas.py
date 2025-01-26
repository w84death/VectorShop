from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QPushButton, QWidget
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen
from .constants import COLORS

class ColorButton(QPushButton):
    def __init__(self, color_hex):
        super().__init__()
        self.color_hex = color_hex
        self.setFixedSize(24, 24)
        self.setStyleSheet(f"""
            background-color: {color_hex};
            border: 1px solid #666;
            margin: 1px;
        """)
        self.setCursor(Qt.PointingHandCursor)

class DrawingCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.groups = []
        self.current_group = None
        self.start_point = QPoint()
        self.current_pos = QPoint()
        self.is_drawing = False
        self.setFixedSize(256, 256)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        
        self.current_color_index = 0
        self.bg_color = QColor(COLORS[2][0])  # Start with white background
        self.history = []

    @property
    def current_line_color(self):
        return QColor(COLORS[self.current_color_index][0])

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self._map_to_canvas(event.pos())
            
            if not self.is_drawing:
                self._start_new_group(pos)
            else:
                self._add_point_to_group(pos, event.modifiers())
                
            self.update()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.is_drawing and self.current_group:
                if event.modifiers() & Qt.ShiftModifier:
                    self.current_group.append(self.current_group[0])
                self._finalize_group()
                self.update()
        super().keyPressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.current_pos = self._map_to_canvas(event.pos())
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(0, 0, 256, 256, self.bg_color)
        
        # Draw all groups with current color
        painter.setPen(QPen(self.current_line_color, 2))
        for group in self.groups:
            self._draw_path(painter, group)
        
        # Draw current group and preview
        if self.is_drawing and self.current_group:
            self._draw_path(painter, self.current_group)
            painter.setPen(QPen(self.current_line_color, 1, Qt.DashLine))
            painter.drawLine(self.current_group[-1], self.current_pos)

    def _map_to_canvas(self, point):
        return QPoint(
            max(0, min(point.x(), 255)),
            max(0, min(point.y(), 255))
        )

    def _start_new_group(self, pos):
        self.history.append(list(self.groups))
        self.start_point = pos
        self.current_pos = pos
        self.is_drawing = True
        self.current_group = [pos]

    def _add_point_to_group(self, pos, modifiers):
        self.current_group.append(pos)
        if not (modifiers & Qt.ShiftModifier):
            self._finalize_group()

    def _finalize_group(self):
        if len(self.current_group) >= 2:
            self.groups.append(self.current_group.copy())
        self.current_group = None
        self.is_drawing = False

    def _draw_path(self, painter, points):
        if len(points) >= 2:
            path = QPainterPath()
            path.moveTo(points[0])
            for point in points[1:]:
                path.lineTo(point)
            painter.drawPath(path)
