import typing

from actions import *
from levels import Levels


class Buff:
    @classmethod
    def create_by_full_name(cls, name: SpellName, levels: Levels):
        cleric_levels = levels.get_level('cleric')
        buffs = [
            ('Prayer', 'P', cleric_levels * ROUND_DURATION * 2),
            ('Battletide', 'BT', cleric_levels * ROUND_DURATION * 2),
            ('Divine Power', 'DP', cleric_levels * ROUND_DURATION * 2),
            ('Divine Favor', 'DF', TURN_DURATION * 2),
            ('Greater Sanctuary', 'GS', 36000),
            (ROD_OF_FAST_CAST, 'FC', cleric_levels * TURN_DURATION),
            ('Bless', 'B', cleric_levels * TURN_DURATION),
            ('Aid', 'A', cleric_levels * TURN_DURATION),
            # do not show this buffs
            (SPELL_ENDURANCE, '', cleric_levels * HOUR_DURATION),

            # items
            ('''spell sequencer''', 'FW', 10 * HOUR_DURATION),
            ('''Shar's Belt of Priestly Might and Warding''', 'MC', 5 * HOUR_DURATION),
            ('''Belt of Brute Strength''', 'BS', 10 * HOUR_DURATION),
            ('''Sorcerer's Cloak''', 'II', 7 * TURN_DURATION),
        ]

        for spell_name, buff_name, duration in buffs:
            if spell_name == name:
                return Buff(spell_name, buff_name, duration)
        return None

    def __init__(self, spell_name: SpellName, buff_name: str, duration: int):
        self.timestamp = get_ts()
        self.spell_name = spell_name
        self.buff_name = buff_name
        self.duration = duration
        logging.debug("CREATE BUFF: {}({}): {} ms".format(self.spell_name, self.buff_name, self.duration))

    def debuff(self) -> None:
        logging.debug("DEBUFF: {}({}): {} ms".format(self.spell_name, self.buff_name, self.duration))
        self.timestamp = 0

    def is_active(self) -> bool:
        return self.timestamp != 0

    def __str__(self):
        return str(self.__dict__)


class BuffList:
    def __init__(self):
        self.buffs: typing.Dict[SpellName, Buff] = {}

    def add_buff(self, spell_name: SpellName, levels: Levels) -> None:
        buff = Buff.create_by_full_name(spell_name, levels)
        if buff:
            self.buffs[spell_name] = buff

    def is_buff_exists(self, spell_name: SpellName) -> bool:
        buff = self.get_buff(spell_name)
        return buff is not None and buff.is_active()

    def get_buffs(self) -> typing.List[Buff]:
        return list(self.buffs.values())

    def get_buff(self, spell_name: SpellName) -> typing.Optional[Buff]:
        return self.buffs.get(spell_name, None)

