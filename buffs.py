from actions import *


class Buff:
    @classmethod
    def create_from_usage(cls, item_name: str):
        durations = {
            CASTER_LEVEL * TURN_DURATION: [
                ROD_OF_FAST_CAST
            ],
        }
        for duration, name in durations:
            if name == item_name:
                return Buff(item_name, duration)
        return None

    @classmethod
    def create_from_cast(cls, cast: CastEnd):
        durations = {
            CASTER_LEVEL * ROUND_DURATION * 2: [
                'Prayer',
                'Battletide',
                'Divine Power',
            ],
            TURN_DURATION * 2: [
                'Divine Favor',
            ],
            40: [
                'Greater Sanctuary',
            ],
        }
        for duration, name in durations:
            if name == cast.spell_name:
                return Buff(name, duration)
        return None

    def __init__(
            self,
            buff_name: str,
            duration: int,  # ms
    ):
        self.timestamp = get_ts()
        self.buff_name = buff_name
        self.duration = duration
