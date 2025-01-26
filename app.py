import sys
import os
from PyQt5.QtWidgets import QApplication
from vectorshop import MainWindow

# Fix Wayland display issue
os.environ["QT_QPA_PLATFORM"] = "xcb"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
