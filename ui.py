import logging
import typing
import collections
from enum import Enum, auto

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *

from common import *


class ProgressBarType(Enum):
    PLAYER_HP = auto()
    TARGET_HP = auto()
    DAMAGE_PER_ROUND = auto()
    KNOCKDOWN = auto()
    KNOCKDOWN_MISS = auto()
    STUNNING_FIST = auto()
    STEALTH_MODE_CD = auto()
    ATTACK_BASE = auto()


class Visible(Enum):
    VISIBLE = auto()
    INVISIBLE = auto()


class Orientation(Enum):
    VERTICAL = auto()
    HORIZONTAL = auto()


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


def create_form() -> QFormLayout:
    form = QFormLayout()
    form.setHorizontalSpacing(0)
    form.setVerticalSpacing(0)
    form.setRowWrapPolicy(QFormLayout.DontWrapRows)
    return form


class Param:
    def __init__(self, title: str, color: str):
        self.form = create_form()
        self.title = create_label(title, color)
        self.value = create_label(color=color)
        self.form.addRow(self.title, self.value)


class CharacterStat:
    def __init__(self):
        self.h_box = QHBoxLayout()
        self.ac = self._add_param('AC:', '#ffffff')
        self.ab = self._add_param('AB:', '#01fe01')

        self.saving_throw_dict: typing.Dict[str, Param] = {}
        self.saving_throw_dict[FORTITUDE] = self._add_param('F:', '#65c9fb')
        self.saving_throw_dict[WILL] = self._add_param('W:', '#cc99cc')

        self.received_damage = self._add_param('RD:', '#e35d02')
        self.special_attack = self._add_param('SA:', '#b0b0b0')
        self.experience = self._add_param('E:', '#ffff01')

    def _add_param(self, title: str, color: str = 'white') -> Param:
        param = Param(title, color)
        self.h_box.addLayout(param.form)
        self.h_box.addSpacing(10)
        return param

    def set_ac(self, min_ac: int, max_ac: int, last_ac_hit: int) -> None:
        self.ac.value.setText('{:>2}/{:>2}({:>2})'.format(min_ac, max_ac, last_ac_hit))

    def set_ab(self, ab: int, last_ab: int) -> None:
        self.ab.value.setText('{:>2}({:>2})'.format(ab, last_ab))

    def set_saving_throw(self, name: str, value: int, last_dc: int) -> None:
        self.saving_throw_dict[name].value.setText('{:>2}({:>2})'.format(value, last_dc))

    def set_received_damage(self, damage: int, last_damage: int, damage_absorb: int) -> None:
        self.received_damage.value.setText('{:>4}({:>3}/{:>3})'.format(
            convert_long_int(damage), convert_long_int(last_damage), convert_long_int(damage_absorb)))

    def set_special_attack(self, name: str, ab: int, dc: int, result: str) -> None:
        self.special_attack.value.setText('{:>2} {:>2}({:>2}/{:>3})'.format(name, ab, dc, result[:4]))

    def set_experience(self, experience: int) -> None:
        self.experience.value.setText('{:>3}'.format(convert_long_int(experience)))


class UserInterface:
    def __init__(self, widget: QWidget):
        self.progress_bar_dict: typing.Dict[ProgressBarType, QProgressBar] = {}

        self.main_form = create_form()
        widget.setLayout(self.main_form)

        self.main_form.addRow(self.create_progress_bar(
            ProgressBarType.PLAYER_HP,
            '%v/0 RD', 0, 0, 1,
            UserInterface._get_style('#ffff0000'),
            Visible.VISIBLE,
        ))

        self.player_stat = CharacterStat()
        self.main_form.addRow(self.player_stat.h_box)

        self.main_form.addRow(self.create_progress_bar(
            ProgressBarType.TARGET_HP,
            '%v/0 TARGET RD', 0, 0, 1,
            UserInterface._get_style('#ffff910c'),
            Visible.VISIBLE,
        ))

        self.target_stat = CharacterStat()
        self.main_form.addRow(self.target_stat.h_box)

        self.main_form.addRow(self.create_progress_bar(
            ProgressBarType.KNOCKDOWN,
            '%v ms Knockdown', 0, 0, KNOCKDOWN_PVE_CD,
            UserInterface._get_style('#99bd00ff'),
            Visible.INVISIBLE,
        ))
        self.main_form.addRow(self.create_progress_bar(
            ProgressBarType.KNOCKDOWN_MISS,
            '%v ms Knockdown', 0, 0, KNOCKDOWN_PVE_CD,
            UserInterface._get_style('#99bd00ff', additional_chunk='width: 10px; margin: 0.5px;'),
            Visible.INVISIBLE,
        ))
        self.main_form.addRow(self.create_progress_bar(
            ProgressBarType.STUNNING_FIST,
            '%v ms Stunning fist', 0, 0, STUNNING_FIST_DURATION,
            UserInterface._get_style('#99ffffff'),
            Visible.INVISIBLE,
        ))
        self.main_form.addRow(self.create_progress_bar(
            ProgressBarType.STEALTH_MODE_CD,
            '%v ms Stealth mode cooldown', 0, 0, STEALTH_MODE_CD,
            UserInterface._get_style('#ff3472ff'),
            Visible.INVISIBLE,
        ))

        self.attack_damage_bar = QHBoxLayout()
        self.main_form.addRow(self.attack_damage_bar)

        self.attack_damage_bar.addWidget(self.create_progress_bar(
            ProgressBarType.ATTACK_BASE,
            '%v Attack base', 0, 0, 0,
            UserInterface._get_style('#9917b402'),
            Visible.INVISIBLE,
        ))

        self.attack_damage_bar.addWidget(self.create_progress_bar(
            ProgressBarType.DAMAGE_PER_ROUND,
            '%v Damage per round', 0, 0, 0,
            UserInterface._get_style('#99ff7b06'),
            Visible.INVISIBLE,
            inverted=True,
        ))

        self.low_hp_label = QLabel("LOW HP")
        self.low_hp_label.setFont(QFont('Monospace', 32))
        self.low_hp_label.setAlignment(Qt.AlignCenter)
        self.low_hp_label.setStyleSheet('background-color: rgba(0,0,0,0%); color: red')
        self.low_hp_label.setVisible(False)
        self.main_form.addRow(self.low_hp_label)

        self.main_label = QLabel("")
        self.main_label.setFont(QFont('Monospace', 10))
        self.main_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.main_label.setStyleSheet('background-color: rgba(0,0,0,0%); color: white')
        self.main_label.setVisible(False)
        self.main_form.addRow(self.main_label)

    def set_main_label_text(self, text: str, visible: bool) -> None:
        self.main_label.setVisible(visible)
        self.main_label.setText(text)

    def notify_low_hp(self, visible: bool):
        self.low_hp_label.setVisible(visible)

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
            type: ProgressBarType,
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
        self.progress_bar_dict[type] = pb
        return pb

    def upgrade_player_hp_progress_bar(
            self,
            cur_value: int,
            min_value: typing.Optional[int],
            max_value: typing.Optional[int],
    ) -> None:
        pb = self.progress_bar_dict[ProgressBarType.PLAYER_HP]
        pb.setFormat('%v/{} RD'.format(max_value))
        pb.setValue(cur_value)
        pb.setMinimum(min_value)
        pb.setMaximum(max_value)

    def upgrade_target_hp_progress_bar(
            self,
            target_name: str,
            cur_value: int,
            min_value: typing.Optional[int],
            max_value: typing.Optional[int],
    ) -> None:
        pb = self.progress_bar_dict[ProgressBarType.TARGET_HP]
        pb.setFormat('%v/{} {}'.format(max_value, target_name[:30]))
        pb.setValue(cur_value)
        pb.setMinimum(min_value)
        pb.setMaximum(max_value)

    def upgrade_progress_bar(
            self,
            bar_type: ProgressBarType,
            cur_value: int,
            min_value: typing.Optional[int] = None,
            max_value: typing.Optional[int] = None,
            visible: Visible = Visible.VISIBLE,
    ) -> None:
        pb = self.progress_bar_dict[bar_type]
        pb.setValue(cur_value)
        if min_value is not None:
            pb.setMinimum(min_value)
        if max_value is not None:
            pb.setMaximum(max_value)
        pb.setVisible(visible == Visible.VISIBLE)

    def set_visible_progress_bar(self, bar_type: ProgressBarType, visible: Visible) -> None:
        pb = self.progress_bar_dict[bar_type]
        pb.setVisible(visible == Visible.VISIBLE)
