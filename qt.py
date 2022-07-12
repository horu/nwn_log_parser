from PyQt5.QtCore import QTimer, QDateTime
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtGui import QFont, QMouseEvent

from parser import *


class Window(QMainWindow):
    """Main Window."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.setWindowTitle("Python Menus & Toolbars")
        #self.resize(400, 100)
      #  self.setGeometry(420, 0, 400, 70)
        self.setWindowOpacity(0.75)

        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.centralWidget = QLabel("")
        self.centralWidget.setFont(QFont('Monospace', 10))
        self.centralWidget.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.centralWidget.setStyleSheet("background-color: black; color: white")
        self.setCentralWidget(self.centralWidget)

    def set_text(self, text):
        self.centralWidget.setText(text)


class Backend:
    def __init__(self, window: Window, log_reader, parser: Parser):
        self.window = window
        self.log_reader = log_reader
        self.reset_geometry()

        self.timer_action = QTimer()
        self.timer_action.timeout.connect(self.read_log)
        self.timer_action.start(100)

        self.timer_reset_geometry = QTimer()
        self.timer_reset_geometry.timeout.connect(self.reset_geometry)
        self.timer_reset_geometry.start(1000)

        self.window.centralWidget.mousePressEvent = self.on_mouse_event

        self.parser = parser

    def on_mouse_event(self, event: QMouseEvent):
        button = event.button()
        if button == Qt.MouseButton.LeftButton:
            self.parser.change_char_list()
        elif button == Qt.MouseButton.RightButton:
            self.window.showMinimized()

    def read_log(self):
        for line in self.log_reader.read_lines():
            self.parser.push_line(line)

        text = self.parser.get_stat()
        self.window.set_text(text)

    def reset_geometry(self):
        self.window.setGeometry(420, 0, 400, 40)
