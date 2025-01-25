import sys
import os
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QGridLayout
)
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QColor

# Fix Wayland display issue
os.environ["QT_QPA_PLATFORM"] = "xcb"

COLORS = [
    ('#000000', 'void'),
    ('#9d9d9d', 'grey'),
    ('#ffffff', 'white'),
    ('#be2633', 'red'),
    ('#e06f8b', 'meat'),
    ('#493c2b', 'dark_brown'),
    ('#a46422', 'brown'),
    ('#eb8925', 'orange'),
    ('#f7e26b', 'yellow'),
    ('#2f484e', 'dark_green'),
    ('#44891a', 'green'),
    ('#a3ce27', 'slime_green'),
    ('#1b2632', 'night_blue'),
    ('#005789', 'sea_blue'),
    ('#31a2f2', 'sky_blue'),
    ('#b2dcef', 'cloud_blue')
]

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VectorShop")
        self._setup_ui()

    def _setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Color palette
        self.canvas = DrawingCanvas()
        self._create_color_palette(layout)
        
        # Canvas and output
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.undo_btn = QPushButton("Undo")
        self.undo_btn.clicked.connect(self._undo)
        export_btn = QPushButton("Export Data")
        export_btn.clicked.connect(self._export_data)
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_canvas)
        
        control_layout.addWidget(self.undo_btn)
        control_layout.addWidget(export_btn)
        control_layout.addWidget(clear_btn)
        
        layout.addWidget(self.canvas)
        layout.addWidget(self.output_box)
        layout.addLayout(control_layout)

    def _create_color_palette(self, parent_layout):
        palette = QWidget()
        grid = QGridLayout(palette)
        grid.setSpacing(2)
        
        for i, (color_hex, color_name) in enumerate(COLORS):
            btn = ColorButton(color_hex)
            # Left click for line color
            btn.clicked.connect(lambda _, idx=i: self._set_line_color(idx))
            # Right click for background color
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda _, idx=i: self._set_bg_color(idx))
            grid.addWidget(btn, i//8, i%8)
        
        parent_layout.addWidget(palette)

    def _set_line_color(self, color_index):
        self.canvas.current_color_index = color_index
        self.canvas.update()

    def _set_bg_color(self, color_index):
        self.canvas.bg_color = QColor(COLORS[color_index][0])
        self.canvas.update()

    def _undo(self):
        if self.canvas.history:
            self.canvas.groups = self.canvas.history.pop()
            self.canvas.update()

    def _export_data(self):
        output = [f"db {COLORS[self.canvas.current_color_index][1]}"]
        
        for group in self.canvas.groups:
            if len(group) < 2:
                continue
                
            line_count = len(group) - 1
            output.append(f"db {line_count}")
            coords = ",".join([f"{p.x()},{p.y()}" for p in group])
            output.append(f"db {coords}")
        
        output.append("db 0")
        self.output_box.setPlainText("\n".join(output))

    def _clear_canvas(self):
        self.canvas.history.append(list(self.canvas.groups))
        self.canvas.groups = []
        self.canvas.current_group = None
        self.canvas.is_drawing = False
        self.canvas.update()
        self.output_box.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())