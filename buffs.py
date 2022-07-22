from actions import *
from levels import Levels


class BuffName:
    def __init__(self, full_name: str, short_name: str):
        self.full = full_name
        self.short = short_name


class Buff:
    @classmethod
    def create_by_full_name(cls, name: str, levels: Levels):
        cleric_levels = levels.get_level('cleric')
        buffs = [
            (BuffName('Prayer', 'P'), cleric_levels * ROUND_DURATION * 2),
            (BuffName('Battletide', 'BT'), cleric_levels * ROUND_DURATION * 2),
            (BuffName('Divine Power', 'DP'), cleric_levels * ROUND_DURATION * 2),
            (BuffName('Divine Favor', 'DF'), TURN_DURATION * 2),
            (BuffName('Greater Sanctuary', 'GS'), 36000),
            (BuffName(ROD_OF_FAST_CAST, 'FC'), cleric_levels * TURN_DURATION),
            (BuffName('Bless', 'B'), cleric_levels * TURN_DURATION),
            (BuffName('Aid', 'A'), cleric_levels * TURN_DURATION),
        ]

        for buff_name, duration in buffs:
            if buff_name.full == name:
                return Buff(buff_name, duration)
        return None

    def __init__(self, buff_name: BuffName, duration: int):
        self.timestamp = get_ts()
        self.buff_name = buff_name
        self.duration = duration
        logging.debug("CREATE BUFF: {}({}): {} ms".format(self.buff_name.full, self.buff_name.short, self.duration))
