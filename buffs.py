from actions import *


class Buff:
    @classmethod
    def create_from_usage(cls, item_name: str):
        durations = {
            CASTER_LEVEL * TURN_DURATION: [
                ROD_OF_FAST_CAST
            ],
        }
        for duration, names in durations.items():
            if item_name in names:
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
            36000: [
                'Greater Sanctuary',
            ],
        }
        for duration, names in durations.items():
            if cast.spell_name in names:
                return Buff(cast.spell_name, duration)
        return None

    def __init__(
            self,
            buff_name: str,
            duration: int,  # ms
    ):
        self.timestamp = get_ts()
        self.buff_name = buff_name
        self.duration = duration
