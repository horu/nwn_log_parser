import logging

from PyQt5.QtGui import QFont, QMouseEvent

from data_saver import DataSaver
from log_reader import *
from parser import *
from printer import *
from ui import *


class Backend:
    def __init__(self, window: Window, log_reader: LogReader, parser: Parser, printer: Printer):
        self.window = window
        self.log_reader = log_reader
        self.reset_geometry()

        self.read_log_timer = QTimer()
        self.read_log_timer.timeout.connect(self.read_log)
        self.read_log_timer.start(10)

        self.data_save_timer = QTimer()
        self.data_save_timer.timeout.connect(self.save_data)
        self.data_save_timer.start(6000)

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

    def save_data(self):
        data_saver = DataSaver(DATA_FILE_PATH)
        data_saver.save(self.parser)

    def read_log(self):
        for line in self.log_reader.read_lines():
            self.parser.push_line(line)

        self.print()

    def print(self):
        self.printer.print(self.parser)
        self.reset_geometry()

    def reset_geometry(self):
        self.window.resize(400, 40)
