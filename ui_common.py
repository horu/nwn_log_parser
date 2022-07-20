import logging

from PyQt5.QtCore import QTimer, QDateTime, QPoint
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont, QMouseEvent

from log_reader import *
from parser import *
from printer import *


def create_form() -> QFormLayout:
    form = QFormLayout()
    form.setHorizontalSpacing(0)
    form.setVerticalSpacing(0)
    form.setRowWrapPolicy(QFormLayout.DontWrapRows)
    return form


DAMAGE_PRINT_LIMIT = 1000


def convert_long_int(value: int) -> str:
    if abs(value) > DAMAGE_PRINT_LIMIT:
        return '{:.1f}'.format(value / DAMAGE_PRINT_LIMIT)
    return str(value)


def create_label(value: str = '', color: str = 'white') -> QLabel:
    label = QLabel(value)
    label.setFont(QFont('Monospace', 10))
    label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
    label.setStyleSheet('background-color: rgba(0,0,0,0%); color: {}'.format(color))
    return label
