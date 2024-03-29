import typing

from ui_common import *
from common import *


def get_progress_bar_style(color: str, border_color: str = None, additional_chunk: str = '', ) -> str:
    style = "QProgressBar{{" \
            "background-color: rgba(0,0,0,0%); " \
            "min-height: 14px; " \
            "max-height: 14px; " \
            "border-radius: 0px;" \
            "border: 1px solid {};" \
            "text-align: center; " \
            "}}" \
            "QProgressBar::chunk{{ " \
            "background-color: {}; " \
            "color: white;" \
            "{}" \
            "}}".format(border_color if border_color else color, color, additional_chunk)
    return style


def create_progress_bar(
        style: str,
        title_format: typing.Optional[str] = '%v',
        cur_value: typing.Optional[int] = 0,
        min_value: typing.Optional[int] = 0,
        max_value: typing.Optional[int] = 1,
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
        self.pb = create_progress_bar(get_progress_bar_style(color))

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
    def __init__(self, tick_ms: Time, timeout: Time):
        self._timer = QTimer()
        self._timer.timeout.connect(self._action)
        self._timer.setInterval(tick_ms)
        self._timer.start()

        self._start_timestamp = get_ts()
        self._timeout = timeout

    def _check_continue(self, now: Time) -> bool:
        return now - self._start_timestamp <= self._timeout

    def _action(self):
        now = get_ts()
        if self._check_continue(now):
            self.tick(now)
        else:
            self._timer.stop()
            self.end()

    def update_timestamp(self, ts: Time) -> bool:
        self._start_timestamp = ts
        now = get_ts()
        if self._check_continue(now):
            if not self._timer.isActive():
                self._timer.start()
            return True
        return False

    def get_timeout(self):
        return self._timeout

    def get_start_timestamp(self):
        return self._start_timestamp

    def end(self):
        pass

    def tick(self, now: Time):
        pass


class TemporaryProgressBar(Timer):
    def __init__(self, name: str, tick_ms: Time, timeout: Time, *args, **kwargs):
        super(TemporaryProgressBar, self).__init__(tick_ms, timeout)
        self.pb = create_progress_bar(*args, **kwargs)
        self.name = name

    def update_timestamp(self, ts: Time):
        if super(TemporaryProgressBar, self).update_timestamp(ts):
            self.pb.setVisible(True)

    def end(self):
        self.pb.setVisible(False)

    def update_label(self) -> None:
        duration = self.pb.value()

        minutes = int(duration / 60000)
        seconds = int(duration % 60000 / 1000)
        milliseconds = int(duration % 1000 / 100)

        minutes_str = ''
        seconds_str = str(seconds)
        milliseconds_str = '.{:0>1d}'.format(milliseconds)
        if minutes:
            minutes_str = '{}:'.format(minutes)
            seconds_str = '{:0>2d}'.format(seconds)
            milliseconds_str = ''

        label = '{}{}{} {}'.format(minutes_str, seconds_str, milliseconds_str, self.name)
        self.pb.setFormat(label)

    def tick(self, now: Time):
        value = self.get_timeout() - (now - self._start_timestamp)
        self.pb.setValue(value)
        self.update_label()

    def hide(self):
        self.update_timestamp(0)


class KnockdownBar(TemporaryProgressBar):
    def __init__(self):
        super(KnockdownBar, self).__init__(
            'Knockdown',
            10, KNOCKDOWN_PVE_CD,
            get_progress_bar_style('#99bd00ff'),
            '%v ms Knockdown',
            max_value=KNOCKDOWN_PVE_CD,
        )


class KnockdownMissBar(TemporaryProgressBar):
    def __init__(self):
        super(KnockdownMissBar, self).__init__(
            'Knockdown',
            10, KNOCKDOWN_PVE_CD,
            get_progress_bar_style('#99bd00ff', additional_chunk='width: 10px; margin: 0.5px;'),
            max_value=KNOCKDOWN_PVE_CD,
        )


class StunningFistBar(TemporaryProgressBar):
    def __init__(self):
        super(StunningFistBar, self).__init__(
            'Stunning fist',
            10, STUNNING_FIST_DURATION,
            get_progress_bar_style('#99ffffff'),
            max_value=STUNNING_FIST_DURATION,
        )


class StealthCooldownBar(TemporaryProgressBar):
    def __init__(self):
        super(StealthCooldownBar, self).__init__(
            'Stealth cooldown',
            10, STEALTH_MODE_CD,
            get_progress_bar_style('#ff3472ff'),
            max_value=STEALTH_MODE_CD,
        )

    def update(self, cooldown: Time, event_ts: Time):
        start_time = event_ts - (STEALTH_MODE_CD - cooldown + 1000)
        self.update_timestamp(start_time)


class CastingBar(TemporaryProgressBar):
    def __init__(self):
        super(CastingBar, self).__init__(
            'Spell',
            10, CAST_TIME,
            get_progress_bar_style('#990017ff'),
            max_value=CAST_TIME,
        )

    def update(self, spell_name: str, event_ts: Time):
        self.name = spell_name
        self.update_timestamp(event_ts)


class CalledShotBar(TemporaryProgressBar):
    def __init__(self, limb, ):
        color = '#99bd00ff'
        if limb == ARM:
            color = '#99ffffff'

        super(CalledShotBar, self).__init__(
            'CalledShot',
            10, CALLED_SHOT_DURATION,
            get_progress_bar_style(color),
            max_value=CALLED_SHOT_DURATION,
        )

        self.timestamps: typing.List[Time] = []
        self.limb = limb
        self._update_label()

    def _update_label(self):
        count = len(self.timestamps)
        self.name = 'CalledShot: {} X {}'.format(self.limb, count)

    def update(self, ts: Time):
        if ts not in self.timestamps:
            self.timestamps.append(ts)
        self.timestamps.sort()

        self._update_label()
        self.update_timestamp(self.timestamps[-1])

    def tick(self, now: Time):
        super(CalledShotBar, self).tick(now)

        for i, ts in enumerate(self.timestamps):
            if now - ts > CALLED_SHOT_DURATION:
                del self.timestamps[i]
                self._update_label()
                break

    def hide(self):
        self.timestamps.clear()
        super(CalledShotBar, self).hide()


class CalledShotArmBar(CalledShotBar):
    def __init__(self):
        super(CalledShotArmBar, self).__init__(ARM)


class CalledShotLegBar(CalledShotBar):
    def __init__(self):
        super(CalledShotLegBar, self).__init__(LEG)


class AttackDpsBar(Timer):
    def __init__(self):
        super(AttackDpsBar, self).__init__(10, ROUND_DURATION)
        self.box = QHBoxLayout()

        self.dpr = 0
        self.last_dpr_ts = 0
        self.dps_pb = create_progress_bar(get_progress_bar_style('#99ca4b0c'), '%v Damage per round')
        self.box.addWidget(self.dps_pb)

        self.attack_pb = create_progress_bar(get_progress_bar_style('#99d59e5b'), '%v Attack base', inverted=True)
        self.box.addWidget(self.attack_pb)

    def update_dps(self, dpr: int, max_dpr: int, last_dpr_ts: Time):
        self.dpr = dpr
        self.last_dpr_ts = last_dpr_ts
        self.dps_pb.setMaximum(max(max_dpr, 1))
        self._update(last_dpr_ts)

    def update_attack(self, attack: int, min_attack: int, max_attack: int, last_attack_ts: Time):
        self.attack_pb.setValue(attack)
        self.attack_pb.setMinimum(min_attack)
        self.attack_pb.setMaximum(max_attack)
        self._update(last_attack_ts)

    def _update(self, last_action_ts: Time):
        if self.get_start_timestamp() < last_action_ts and self.update_timestamp(last_action_ts):
            self.dps_pb.setVisible(True)
            self.attack_pb.setVisible(True)

    def tick(self, now: Time):
        duration_without_attack = now - self.last_dpr_ts
        dpr = int(self.dpr * (ROUND_DURATION - duration_without_attack) / ROUND_DURATION)
        if dpr >= 0:
            self.dps_pb.setValue(dpr)

    def end(self):
        self.dps_pb.setVisible(False)
        self.attack_pb.setVisible(False)


class BuffBar(TemporaryProgressBar):
    def __init__(self, name: str, duration: Time):
        super(BuffBar, self).__init__(
            name,
            10, duration,
            get_progress_bar_style('#9938bf43', border_color='#99d59e5b'),
            cur_value=duration,
            max_value=duration,
        )


class BuffsBox:
    def __init__(self):
        self.box = QHBoxLayout()
        self.buffs: typing.Dict[str, BuffBar] = {}


class BuffsBar:
    def __init__(self):
        self.form = create_form()
        self.buff_boxes: typing.List[BuffsBox] = []

    def _get_buff(self, buff_name: str, duration: Time):
        for box in self.buff_boxes:
            if buff_name in box.buffs.keys():
                return box.buffs[buff_name]

        buff = BuffBar(buff_name, duration)
        box_to_insert = None
        for box in self.buff_boxes:
            if len(box.buffs) < 6:
                box_to_insert = box
                break

        if not box_to_insert:
            box_to_insert = BuffsBox()
            self.buff_boxes.append(box_to_insert)
            self.form.addRow(box_to_insert.box)

        box_to_insert.box.addWidget(buff.pb)
        box_to_insert.buffs[buff_name] = buff

        return buff

    def update(self, buff_name: str, duration: Time, start_time: Time):
        buff_bar = self._get_buff(buff_name, duration)
        buff_bar.update_timestamp(start_time)

    def hide(self, buff_name: str):
        for box in self.buff_boxes:
            for name, buff in box.buffs.items():
                if name == buff_name:
                    buff.hide()
                    box.box.removeWidget(buff.pb)
                    del box.buffs[name]
                    break


