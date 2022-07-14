import logging

from PyQt5.QtCore import QTimer, QDateTime, QPoint
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtGui import QFont, QMouseEvent

from log_reader import *
from parser import *


class Window(QMainWindow):
    """Main Window."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.setWindowTitle("Python Menus & Toolbars")
        self.move(420, 0)
        self.setWindowOpacity(0.9)

        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.centralWidget = QLabel("")
        self.centralWidget.setFont(QFont('Monospace', 10))
        self.centralWidget.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.centralWidget.setStyleSheet("background-color: black; color: white")
        self.setCentralWidget(self.centralWidget)

        # position for move window
        self.drag_position = QPoint()

    def set_text(self, text):
        self.centralWidget.setText(text)


class Backend:
    def __init__(self, window: Window, log_reader: LogReader, parser: Parser):
        self.window = window
        self.log_reader = log_reader
        self.reset_geometry()

        self.timer_action = QTimer()
        self.timer_action.timeout.connect(self.read_log)
        self.timer_action.start(100)

        self.timer_reset_geometry = QTimer()
        self.timer_reset_geometry.timeout.connect(self.reset_geometry)
        self.timer_reset_geometry.start(1000)

        self.window.centralWidget.mousePressEvent = self.on_press_event
        self.window.centralWidget.mouseDoubleClickEvent = self.on_double_click_event
        self.window.centralWidget.mouseMoveEvent = self.on_move_event

        self.parser = parser

    def on_double_click_event(self, event: QMouseEvent):
        button = event.button()
        if button == Qt.MouseButton.LeftButton:
            self.window.showMinimized()
        event.accept()

    def on_press_event(self, event: QMouseEvent):
        self.window.drag_position = event.globalPos()

        button = event.button()
        if button == Qt.MouseButton.RightButton:
            self.parser.change_print_mode()
        elif button == Qt.MouseButton.MidButton:
            self.parser.reset_statistic()
        event.accept()

    def on_move_event(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            self.window.move(self.window.pos() + event.globalPos() - self.window.drag_position)
            self.window.drag_position = event.globalPos()
            event.accept()

    def read_log(self):
        for line in self.log_reader.read_lines():
            self.parser.push_line(line)

        self.print()

    def print(self):
        text = self.parser.print()
        self.window.set_text(text)

    def reset_geometry(self):
        self.window.resize(400, 40)
