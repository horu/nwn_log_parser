from ui_common import *
from common import *


class Param:
    def __init__(self, title: str, color: str):
        self.form = create_form()
        self.title = create_label(title, color)
        self.value = create_label(color=color)
        self.form.addRow(self.title, self.value)


class CharacterStat:
    def __init__(self):
        self.box = QHBoxLayout()
        self.ac = self._add_param('AC:', '#ffffff')
        self.ab = self._add_param('AB:', '#01fe01')

        self.saving_throw_dict: typing.Dict[str, Param] = {}
        self.saving_throw_dict[FORTITUDE] = self._add_param('F:', '#65c9fb')
        self.saving_throw_dict[WILL] = self._add_param('W:', '#cc99cc')

        self.received_damage = self._add_param('RD:', '#e35d02')
        self.special_attack = self._add_param('SA:', '#b0b0b0')
        self.concealment = self._add_param('C:', '#31f9ff')
        self.experience = self._add_param('E:', '#ffff01')

    def _add_param(self, title: str, color: str = 'white') -> Param:
        param = Param(title, color)
        self.box.addLayout(param.form)
        self.box.addSpacing(10)
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
        self.special_attack.value.setText('{:>2} {:>2}({:>2}/{:>4})'.format(name, ab, dc, result[:4]))

    def set_concealment(self, concealment: int) -> None:
        self.concealment.value.setText('{:>2}'.format(concealment))

    def set_experience(self, experience: int) -> None:
        self.experience.value.setText('{:>3}'.format(convert_long_int(experience)))