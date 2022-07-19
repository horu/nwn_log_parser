import re
import logging

import typing

from common import *


class Action:
    @classmethod
    def base_create(cls, string, pattern, action_type):
        m = re.match(pattern, string)
        if m:
            g = m.groups()
            # logging.debug('{}'.format(g))
            action = action_type(g)
            logging.debug(str(action))
            return action

        return None

    def __init__(self):
        self.timestamp = get_ts()

    def __str__(self):
        return '{}: {}'.format(self.__class__.__name__, str(self.__dict__))


def append_fix_time_window(actions_list: typing.List[Action], action: Action, window_duration) -> None:
    actions_list.append(action)
    window_end = 0
    ts = get_ts()
    for i, action in enumerate(actions_list):
        if ts - action.timestamp <= window_duration:
            window_end = i
            break
    # logging.debug('Remove actions: {}'.format([str(action) for action in actions_list[0:window_end]]))
    del actions_list[0:window_end]


class Attack(Action):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] (.+) attacks ([^:]+) \: \*(.+)\* \: \(([0-9]+) \+ ([0-9]+) \= ([0-9]+)'
        return Action.base_create(string, p, cls)

    @classmethod
    def explicit_create(cls):
        return cls(['', '', '', '0', '0', '0'])

    def __init__(self, g):
        super().__init__()
        s = g[0].split(' : ')
        self.attacker_name = s[-1]
        s.pop()
        self.specials = s  # Sneak Attack, Off hand, ...
        self.target_name = g[1]
        self.result = g[2]
        self.roll = int(g[3])
        self.base = int(g[4])
        self.value = int(g[5])
        assert self.roll + self.base == self.value

    # attack is hit to target for any type
    def is_hit(self):
        return self.result == HIT or self.result == CRITICAL_HIT or self.result == RESISTED or self.result == FAILED

    def is_miss(self):
        return self.result == MISS

    def is_critical_roll(self):
        return self.roll == 1 or self.roll == 20


class SpecialAttack(Attack):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] (.+) attempts ([^:]+) on ([^:]+) \: \*(.+)\* \: \(([0-9]+) \+ ([0-9]+) \= ([0-9]+)'
        return Action.base_create(string, p, cls)

    @classmethod
    def explicit_create(cls):
        return cls(['', '', '', '', '0', '0', '0'])

    def __init__(self, g):
        g_list = list(g)
        self.type = g_list[1]
        del g_list[1]
        super().__init__(g_list)

    # special attack is hit to target and success
    def is_success(self):
        return self.result == HIT or self.result == CRITICAL_HIT


"""
[CHAT WINDOW TEXT] [Wed Jul 13 23:52:00] TEST m f s attempts Improved Knockdown on NORTHERN ORC KING : *resisted* : (2 + 44 = 46)
[CHAT WINDOW TEXT] [Fri Jul  8 20:13:36] Sneak Attack : Dunya Kulakova attempts Improved Knockdown on 60 AC DUMMY : *miss* : (4 + 45 = 49)
"""


class Knockdown(Action):
    def __init__(self, s_attack: SpecialAttack):
        super().__init__()
        self.s_attack = s_attack

    def get_cooldown(self):
        value = KNOCKDOWN_PVE_CD - (get_ts() - self.s_attack.timestamp)
        if value > 0:
            return value
        return 0

"""
[CHAT WINDOW TEXT] [Fri Jul  8 20:25:39] Dunya Kulakova attempts Stunning Fist on TRAINER : *failed* : (15 + 41 = 56)
[CHAT WINDOW TEXT] [Fri Jul  8 20:26:20] Sneak Attack : Dunya Kulakova attempts Stunning Fist on Chaotic Evil : *hit* : (6 + 41 = 47)
"""


class StunningFirst(Action):
    def __init__(self, s_attack: SpecialAttack):
        super().__init__()
        self.s_attack = s_attack
        self.throw = None

    def get_duration(self) -> int:  # ms
        if self.throw and self.throw.result == FAILURE:
            duration = STUNNING_FIST_DURATION - (get_ts() - self.s_attack.timestamp)
            if duration > 0:
                return duration
        return 0


class SavingThrow(Action):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) \: ([^:]+) \: \*(.+)\* \: \(([0-9]+) \+ ([0-9]+) \= ([0-9]+) vs. DC: ([0-9]+)\)'
        return Action.base_create(string, p, cls)

    def __init__(self, g):
        super().__init__()
        self.target_name = g[0]
        self.type = g[1]
        self.result = g[2]
        self.roll = int(g[3])
        self.base = int(g[4])
        self.value = int(g[5])
        self.dc = int(g[6])
        assert self.roll + self.base == self.value


class Damage(Action):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) damages ([^:]+)\: ([0-9]+)'
        return Action.base_create(string, p, cls)

    @classmethod
    def explicit_create(cls):
        return cls(['', '', '0'])

    def __init__(self, g):
        super().__init__()
        self.damager_name = g[0]
        self.target_name = g[1]
        self.value = int(g[2])
        self.damage_absorption_list: typing.List[DamageAbsorption] = []


class Death(Action):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) killed ([^:^\n]+)'
        return Action.base_create(string, p, cls)

    def __init__(self, g):
        super().__init__()
        self.killer_name = g[0]
        self.target_name = g[1]


class DamageAbsorption(Action):
    def __init__(self, g):
        super().__init__()
        self.target_name = g[0]
        self.value = int(g[1])


class DamageReduction(DamageAbsorption):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) \: Damage Reduction absorbs ([0-9]+) damage'
        return Action.base_create(string, p, cls)

    def __init__(self, g):
        super().__init__(g)


class DamageResistance(DamageAbsorption):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) \: Damage Resistance absorbs ([0-9]+) damage'
        return Action.base_create(string, p, cls)

    def __init__(self, g):
        super().__init__(g)


"""
[CHAT WINDOW TEXT] [Wed Jul 13 15:23:02] Epic Giant Demon : Damage Immunity absorbs 19 point(s) of Physical
"""


class DamageImmunity(DamageAbsorption):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) \: Damage Immunity absorbs ([0-9]+) point'
        return Action.base_create(string, p, cls)

    def __init__(self, g):
        super().__init__(g)


"""
[CHAT WINDOW TEXT] [Mon Jul 11 17:52:32] Wait 10 seconds for hiding
"""


class StealthCooldown(Action):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] Wait ([0-9]+) seconds for hiding'
        return Action.base_create(string, p, cls)

    @classmethod
    def explicit_create(cls, cooldown: int):  # ms
        sc = cls(['0'])
        sc._cooldown = cooldown
        return sc

    def get_duration(self) -> int:  # ms
        duration = self._cooldown - 1000 - (get_ts() - self.timestamp)  # 1000 - server fix
        if duration > 0:
            return duration
        return 0

    def __init__(self, g):
        super().__init__()
        self._cooldown = int(g[0]) * 1000  # ms


"""
[CHAT WINDOW TEXT] [Wed Jul 13 00:35:34] Dunya Kulakova : Initiative Roll : 20 : (9 + 11 = 20)
"""


class InitiativeRoll(Action):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) \: Initiative Roll :'
        return Action.base_create(string, p, cls)

    def __init__(self, g):
        super().__init__()
        self.roller_name = g[0]


"""
[CHAT WINDOW TEXT] [Thu Jul 14 19:29:38] Moore Guardian uses Potion of Heal
"""


class Usage(Action):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) uses (.+)'
        return Action.base_create(string, p, cls)

    def __init__(self, g):
        super().__init__()
        self.user_name = g[0]
        self.item = g[1]


"""
[CHAT WINDOW TEXT] [Thu Jul 14 19:29:37] Dunya Kulakova : Healed 2 hit points.
"""


class Heal(Action):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) \: Healed ([0-9]+) hit points.'
        return Action.base_create(string, p, cls)

    @classmethod
    def explicit_create(cls):
        return cls(['', '0'])

    def __init__(self, g):
        super().__init__()
        self.target_name = g[0]
        self.value = int(g[1])


"""
[CHAT WINDOW TEXT] [Thu Jul 14 23:24:05] Experience Points Gained:  535
"""


class Experience(Action):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] Experience Points Gained\:[ ]+([0-9]+)'
        return Action.base_create(string, p, cls)

    @classmethod
    def explicit_create(cls):
        return cls(['0'])

    def __init__(self, g):
        super().__init__()
        self.value = int(g[0])


"""
[CHAT WINDOW TEXT] [Sat Jul 16 02:40:56] Done resting.
"""


class Resting(Action):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] Done resting.'
        return Action.base_create(string, p, cls)

    def __init__(self, g):
        super().__init__()


"""
[CHAT WINDOW TEXT] [Tue Jul 19 12:33:11] TEST casting Mage Armor
"""


class CastBegin(Action):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) casting ([^\n]+)'
        return Action.base_create(string, p, cls)

    def __init__(self, g):
        super().__init__()
        self.caster_name = g[0]
        self.spell_name = g[1]


"""
[CHAT WINDOW TEXT] [Tue Jul 19 12:33:11] TEST casts Mage Armor
"""


class CastEnd(Action):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) casts ([^\n]+)'
        return Action.base_create(string, p, cls)

    def __init__(self, g):
        super().__init__()
        self.caster_name = g[0]
        self.spell_name = g[1]


"""
[CHAT WINDOW TEXT] [Tue Jul 19 12:43:07] TEST m r sf : Spell Interrupted
"""


class CastInterruption(Action):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) \: Spell Interrupted'
        return Action.base_create(string, p, cls)

    def __init__(self, g):
        super().__init__()
        self.caster_name = g[0]
