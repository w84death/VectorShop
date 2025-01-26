import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QGridLayout
)
from PyQt5.QtCore import Qt
from .canvas import DrawingCanvas, ColorButton
from .constants import COLORS

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
