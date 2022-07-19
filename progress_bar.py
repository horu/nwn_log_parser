from enum import Enum, auto

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *


def get_progress_bar_style(color: str, additional_chunk: str = '') -> str:
    style = "QProgressBar{{" \
            "background-color: rgba(0,0,0,0%); " \
            "min-height: 14px; " \
            "max-height: 14px; " \
            "border-radius: 5px;" \
            "text-align: center; " \
            "}}" \
            "QProgressBar::chunk{{ " \
            "background-color: {}; " \
            "color: white;" \
            "{}" \
            "}}".format(color, additional_chunk)
    return style


class Visible(Enum):
    VISIBLE = auto()
    INVISIBLE = auto()


def create_progress_bar(
        title_format: str,
        cur_value: int,
        min_value: int,
        max_value: int,
        style: str,
        visible: Visible,
        inverted: bool = False,
) -> QProgressBar:
    pb = QProgressBar()
    pb.setFormat(title_format)
    pb.setValue(cur_value)
    pb.setMinimum(min_value)
    pb.setMaximum(max_value)
    pb.setFont(QFont('Monospace', 10))
    pb.setStyleSheet(style)
    pb.setVisible(visible == Visible.VISIBLE)
    pb.setAlignment(Qt.AlignLeft | Qt.AlignTop)
    pb.setInvertedAppearance(inverted)
    return pb