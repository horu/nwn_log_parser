from actions import *


class BuffName:
    def __init__(self, full_name: str, short_name: str):
        self.full = full_name
        self.short = short_name


class CommonBuff:
    @classmethod
    def find_by_full_name(cls, name: str):
        for buff in BUFFS:
            if buff.buff_name.full == name:
                return buff
        return None

    def __init__(self, buff_name: BuffName, duration: int):
        self.buff_name = buff_name
        self.duration = duration


BUFFS = [
    CommonBuff(BuffName('Prayer', 'P'), CASTER_LEVEL * ROUND_DURATION * 2),
    CommonBuff(BuffName('Battletide', 'BT'), CASTER_LEVEL * ROUND_DURATION * 2),
    CommonBuff(BuffName('Divine Power', 'DP'), CASTER_LEVEL * ROUND_DURATION * 2),
    CommonBuff(BuffName('Divine Favor', 'DF'), TURN_DURATION * 2),
    CommonBuff(BuffName('Greater Sanctuary', 'GS'), 36000),
    CommonBuff(BuffName(ROD_OF_FAST_CAST, 'FC'), CASTER_LEVEL * TURN_DURATION),
    CommonBuff(BuffName('Bless', 'B'), CASTER_LEVEL * TURN_DURATION),
    CommonBuff(BuffName('Aid', 'A'), CASTER_LEVEL * TURN_DURATION),
]


class Buff:
    @classmethod
    def create_by_full_name(cls, name: str):
        common_buff = CommonBuff.find_by_full_name(name)
        if common_buff:
            return Buff(common_buff)
        return None

    def __init__(self, common_buff: CommonBuff):
        self.timestamp = get_ts()
        self.buff_name = common_buff.buff_name
        self.duration = common_buff.duration
        logging.debug("CREATE BUFF: {}({}): {} ms".format(self.buff_name.full, self.buff_name.short, self.duration))
