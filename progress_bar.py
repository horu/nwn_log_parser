from enum import Enum, auto

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *

from common import *


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
    pb.setVisible(True)
    pb.setAlignment(Qt.AlignLeft | Qt.AlignTop)
    pb.setInvertedAppearance(inverted)
    return pb


class HpBar:
    def __init__(self, color: str):
        self.pb = create_progress_bar(
            '%v/1', 0, 0, 1,
            get_progress_bar_style(color),
            Visible.VISIBLE,
        )

    def upgrade(self, name: str, cur_value: int, min_value: int, max_value: int) -> None:
        self.pb.setFormat('%v/{} {}'.format(max_value, name[:30]))
        self.pb.setValue(cur_value)
        self.pb.setMinimum(min_value)
        self.pb.setMaximum(max_value)


class PlayerHpBar(HpBar):
    def __init__(self):
        super(PlayerHpBar, self).__init__('#ffff0000')


class TargetHpBar(HpBar):
    def __init__(self):
        super(TargetHpBar, self).__init__('#ffff910c')


class Timer:
    def __init__(self, tick_ms: int, timeout: int):
        self._timer = QTimer()
        self._timer.timeout.connect(self._action)
        self._timer.setInterval(tick_ms)
        self._timer.start()

        self._start_timestamp = get_ts()
        self._timeout = timeout

    def _action(self):
        ts = get_ts()
        if ts - self._start_timestamp > self._timeout:
            self._timer.stop()
            self.end()
        else:
            self.tick(ts)

    def update_timestamp(self):
        if not self._timer.isActive():
            self._timer.start()
        self._start_timestamp = get_ts()
        self._action()

    def get_start_timestamp(self):
        return self._start_timestamp

    def end(self):
        pass

    def tick(self, ts: int):
        pass


class TemporaryProgressBar(Timer):
    def __init__(self, tick_ms: int, timeout: int, *args, **kwargs):
        super(TemporaryProgressBar, self).__init__(tick_ms, timeout)
        self.pb = create_progress_bar(*args, **kwargs)

    def update_timestamp(self):
        super().update_timestamp()
        self.pb.setVisible(True)

    def end(self):
        self.pb.setVisible(False)

    def tick(self, ts: int):
        value = ts - self._start_timestamp
        self.pb.setValue(value)


class KnockdownBar(TemporaryProgressBar):
    def __init__(self):
        super(KnockdownBar, self).__init__(
            10, KNOCKDOWN_PVE_CD,
            '%v ms Knockdown', 0, 0, KNOCKDOWN_PVE_CD,
            get_progress_bar_style('#99bd00ff'),
            Visible.INVISIBLE,
        )


class KnockdownMissBar(TemporaryProgressBar):
    def __init__(self):
        super(KnockdownMissBar, self).__init__(
            10, KNOCKDOWN_PVE_CD,
            '%v ms Knockdown', 0, 0, KNOCKDOWN_PVE_CD,
            get_progress_bar_style('#99bd00ff', additional_chunk='width: 10px; margin: 0.5px;'),
            Visible.INVISIBLE,
        )


class StunningFistBar(TemporaryProgressBar):
    def __init__(self):
        super(StunningFistBar, self).__init__(
            10, KNOCKDOWN_PVE_CD,
            '%v ms Stunning fist', 0, 0, STUNNING_FIST_DURATION,
            get_progress_bar_style('#99ffffff'),
            Visible.INVISIBLE,
        )


class StealthCooldown(TemporaryProgressBar):
    def __init__(self):
        super(StealthCooldown, self).__init__(
            10, KNOCKDOWN_PVE_CD,
            '%v ms Stealth cooldown', 0, 0, STEALTH_MODE_CD,
            get_progress_bar_style('#ff3472ff'),
            Visible.INVISIBLE,
        )


class Casting(TemporaryProgressBar):
    def __init__(self):
        super(Casting, self).__init__(
            10, KNOCKDOWN_PVE_CD,
            '%v ms', 0, 0, CAST_TIME,
            get_progress_bar_style('#990017ff'),
            Visible.INVISIBLE,
        )

    def update(self, spell_name: str):
        self.pb.setFormat('%v ms {}'.format(spell_name))
        self.update_timestamp()


class AttackDpsBar(Timer):
    def __init__(self):
        super(AttackDpsBar, self).__init__(10, ROUND_DURATION)
        self.box = QHBoxLayout()

        self.dpr = 0
        self.dps_pb = create_progress_bar(
            '%v Damage per round', 0, 0, 1,
            get_progress_bar_style('#99ff7b06'),
            Visible.INVISIBLE,
        )
        self.box.addWidget(self.dps_pb)

        self.attack_pb = create_progress_bar(
            '%v Attack base', 0, 0, 1,
            get_progress_bar_style('#9917b402'),
            Visible.INVISIBLE,
            inverted=True,
        )
        self.box.addWidget(self.attack_pb)

    def update_dps(self, dpr: int, max_dpr: int):
        self.dpr = dpr
        self.dps_pb.setMaximum(max_dpr)
        self._update()

    def update_attack(self, attack: int, min_attack: int, max_attack: int):
        self.attack_pb.setValue(attack)
        self.attack_pb.setMinimum(min_attack)
        self.attack_pb.setMaximum(max_attack)
        self._update()

    def _update(self):
        self.update_timestamp()
        self.dps_pb.setVisible(True)
        self.attack_pb.setVisible(True)

    def tick(self, ts: int):
        duration_without_attack = ts - self.get_start_timestamp()
        dpr = int(self.dpr * (ROUND_DURATION - duration_without_attack) / ROUND_DURATION)
        if dpr >= 0:
            self.dps_pb.setValue(dpr)

    def end(self):
        self.dps_pb.setVisible(False)
        self.attack_pb.setVisible(False)

