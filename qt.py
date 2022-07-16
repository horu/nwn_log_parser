import logging

from PyQt5.QtCore import QTimer, QDateTime, QPoint
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont, QMouseEvent

from log_reader import *
from parser import *
from printer import *


TRANSPARENCY = 0.5


class Window(QMainWindow):
    """Main Window."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.setWindowTitle("Nwn log parser")
        self.move(600, 37)
        self.setWindowOpacity(1)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.form = QFormLayout()
        self.form.setHorizontalSpacing(0)
        self.form.setVerticalSpacing(0)
        self.form.setRowWrapPolicy(QFormLayout.DontWrapRows)

        self.group_box = QWidget()
        self.group_box.setStyleSheet('background-color: rgba(0,0,0,{}%); color: white'.format(int(TRANSPARENCY * 100)))
        self.group_box.setLayout(self.form)

        self.setCentralWidget(self.group_box)

        # position for move window
        self.drag_position = QPoint()


class Backend:
    def __init__(self, window: Window, log_reader: LogReader, parser: Parser, printer: Printer):
        self.window = window
        self.log_reader = log_reader
        self.reset_geometry()

        self.timer_action = QTimer()
        self.timer_action.timeout.connect(self.read_log)
        self.timer_action.start(100)

        # self.timer_reset_geometry = QTimer()
        # self.timer_reset_geometry.timeout.connect(self.reset_geometry)
        # self.timer_reset_geometry.start(1000)

        self.window.centralWidget().mousePressEvent = self.on_press_event
        self.window.centralWidget().mouseDoubleClickEvent = self.on_double_click_event
        self.window.centralWidget().mouseMoveEvent = self.on_move_event

        self.parser = parser
        self.printer = printer

    def on_double_click_event(self, event: QMouseEvent):
        button = event.button()
        if button == Qt.MouseButton.LeftButton:
            self.window.showMinimized()
        event.accept()

    def on_press_event(self, event: QMouseEvent):
        self.window.drag_position = event.globalPos()

        button = event.button()
        if button == Qt.MouseButton.RightButton:
            self.printer.change_print_mode()
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
        self.printer.print(self.parser)
        self.reset_geometry()

    def reset_geometry(self):
        self.window.resize(400, 40)
