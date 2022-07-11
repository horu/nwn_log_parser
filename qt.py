import fcntl
import subprocess
from PyQt5.QtCore import QTimer, QDateTime
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtGui import QFont

import select

from parser import *


FILE_NAMES = [
    'nwclientLog1.txt',
    'nwclientLog2.txt',
    'nwclientLog3.txt',
    'nwclientLog4.txt',
]

class Window(QMainWindow):
    """Main Window."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.setWindowTitle("Python Menus & Toolbars")
        #self.resize(400, 100)
      #  self.setGeometry(420, 0, 400, 70)
      #  self.setWindowOpacity(0.6)

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint) # without window
        self.press = False

        self.centralWidget = QLabel("")
        self.centralWidget.setFont(QFont('Monospace', 10))
        self.centralWidget.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.centralWidget.setStyleSheet("background-color: black; color: white")
        self.setCentralWidget(self.centralWidget)

    def setText(self, text):
        self.centralWidget.setText(text)


class Backend:
    def __init__(self, window, directory):
        self.window = window

        self.processes = []
        for file_name in FILE_NAMES:
            # non block
            p = subprocess.Popen(['tail', '-f', directory + file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            fd = p.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            self.processes.append(p)

        self.timer = QTimer()
        self.timer.timeout.connect(self.action)
        self.timer.start(100)

        self.parser = Parser(PLAYER_NAME)

    def action(self):
        for p in self.processes:
            for line in p.stdout.readlines():
                decoded = line.decode()
                self.parser.push_line(decoded)

        text = self.parser.get_stat()
        self.window.setGeometry(420, 0, 400, 70)
        self.window.setText(text)