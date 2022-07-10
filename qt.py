import fcntl
import subprocess
from PyQt5.QtCore import QTimer, QDateTime
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtGui import QFont

import select

from parser import *


class Window(QMainWindow):
    """Main Window."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.setWindowTitle("Python Menus & Toolbars")
        #self.resize(400, 100)
        self.setGeometry(420, 40, 400, 70)
        self.setWindowOpacity(0.6)

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
    def __init__(self, label, filename):
        self.label = label

        self.f = subprocess.Popen(['tail', '-f', filename], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        fd = self.f.stdout.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        self.timer = QTimer()
        self.timer.timeout.connect(self.action)
        self.timer.start(100)

        self.parser = Parser(PLAYER_NAME)

    def action(self):
        line = self.f.stdout.readline().decode()
        if line:
            self.parser.push_line(line)

        text = self.parser.get_stat()
        self.label.setText(text)