import logging
import typing
import collections
from enum import Enum

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *

from char import *


class ProgressBarType(Enum):
    HP = 1
    DAMAGE_PER_ROUND = 2
    KNOCKDOWN = 3
    KNOCKDOWN_MISS = 4
    STUNNING_FIST = 5
    STEALTH_MODE_CD = 6
    ATTACK_BASE = 7


class UserInterface:
    def __init__(self, form: QFormLayout):
        self.form = form

        self.main_label = QLabel("")
        self.main_label.setFont(QFont('Monospace', 10))
        self.main_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.main_label.setStyleSheet('background-color: rgba(0,0,0,0%); color: white')
        self.form.addRow(self.main_label)

        self.progress_bar_dict: typing.Dict[ProgressBarType, QProgressBar] = {
            ProgressBarType.DAMAGE_PER_ROUND: self.create_progress_bar(
                '%v Damage per round', 0, 0, 0,
                UserInterface._get_style('#99ff7b06'),
                False),
            ProgressBarType.KNOCKDOWN: self.create_progress_bar(
                '%v ms Knockdown', 0, 0, KNOCKDOWN_PVE_CD,
                UserInterface._get_style('#99bd00ff'),
                False),
            ProgressBarType.KNOCKDOWN_MISS: self.create_progress_bar(
                '%v ms Knockdown', 0, 0, KNOCKDOWN_PVE_CD,
                UserInterface._get_style('#99bd00ff', additional_chunk='width: 10px; margin: 0.5px;'),
                False),
            ProgressBarType.STUNNING_FIST: self.create_progress_bar(
                '%v ms Stunning fist', 0, 0, STUNNING_FIST_DURATION,
                UserInterface._get_style('#99ffffff'),
                False),
            ProgressBarType.STEALTH_MODE_CD: self.create_progress_bar(
                '%v ms Stealth mode cooldown', 0, 0, STEALTH_MODE_CD,
                UserInterface._get_style('#ff3472ff'),
                False),
            ProgressBarType.ATTACK_BASE: self.create_progress_bar(
                '%v Attack base', 0, 0, 0,
                UserInterface._get_style('#9917b402'),
                False),
        }

    def set_main_lavel_text(self, text: str) -> None:
        self.main_label.setText(text)

    @staticmethod
    def _get_style(color: str, additional_chunk: str = '') -> str:
        style = "QProgressBar{{" \
                "background-color: rgba(0,0,0,0%); " \
                "min-height: 14px; " \
                "max-height: 14px; " \
                "border-radius: 5px;"\
                "text-align: center; " \
                "}}"\
                "QProgressBar::chunk{{ " \
                "background-color: {}; " \
                "color: white;" \
                "{}" \
                "}}".format(color, additional_chunk)
        return style

    def create_progress_bar(
            self,
            title_format: str,
            cur_value: int,
            min_value: int,
            max_value: int,
            style: str,
            visible: bool,
    ) -> QProgressBar:
        pb = QProgressBar()
        pb.setFormat(title_format)
        pb.setValue(cur_value)
        pb.setMinimum(min_value)
        pb.setMaximum(max_value)
        pb.setFont(QFont('Monospace', 10))
        pb.setStyleSheet(style)
        pb.setVisible(visible)
        self.form.addRow(pb)
        return pb

    def upgrade_progress_bar(
            self,
            bar_type: ProgressBarType,
            cur_value: int = 0,
            min_value: typing.Optional[int] = None,
            max_value: typing.Optional[int] = None,
            visible: bool = True,
    ) -> None:
        pb = self.progress_bar_dict[bar_type]
        pb.setValue(cur_value)
        if min_value is not None:
            pb.setMinimum(min_value)
        if max_value is not None:
            pb.setMaximum(max_value)
        pb.setVisible(visible)