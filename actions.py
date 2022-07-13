import re
import logging

import typing

from common import *


class Action:
    @staticmethod
    def base_create(string, pattern, action_type):
        m = re.match(pattern, string)
        if m:
            g = m.groups()
            logging.debug('{}'.format(g))
            action = action_type(g)
            logging.debug(str(action))
            return action

        return None

    def __init__(self):
        self.timestamp = get_ts()

    def __str__(self):
        return str(self.__dict__)


class Attack(Action):
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] (.+) attacks ([^:]+) \: \*(.+)\* \: \(([0-9]+) \+ ([0-9]+) \= ([0-9]+)'
        return Action.base_create(string, p, Attack)

    def __init__(self, g):
        super().__init__()
        s = g[0].split(' : ')
        self.attacker_name = s[-1]
        s.pop()
        self.specials = s
        self.target_name = g[1]
        self.result = g[2]
        self.roll = int(g[3])
        self.base = int(g[4])
        self.value = int(g[5])
        assert self.roll + self.base == self.value

    def is_hit(self):
        return self.result == HIT or self.result == CRITICAL_HIT


class SpecialAttack(Attack):
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] (.+) attempts ([^:]+) on ([^:]+) \: \*(.+)\* \: \(([0-9]+) \+ ([0-9]+) \= ([0-9]+)'
        return Action.base_create(string, p, SpecialAttack)

    def __init__(self, g):
        g_list = list(g)
        self.type = g_list[1]
        del g_list[1]
        super().__init__(g_list)


class StunningFirst(Action):
    def __init__(self, s_attack: SpecialAttack):
        super().__init__()
        self.s_attack = s_attack
        self.throw = None

    def duration(self) -> int:  # ms
        if self.throw and self.throw.result == FAILURE:
            duration = STUNNING_FIST_DURATION - (get_ts() - self.s_attack.timestamp)
            if duration > 0:
                return duration
        return 0


class SavingThrow(Action):
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) \: ([^:]+) \: \*(.+)\* \: \(([0-9]+) \+ ([0-9]+) \= ([0-9]+) vs. DC: ([0-9]+)\)'
        return Action.base_create(string, p, SavingThrow)

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
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) damages ([^:]+)\: ([0-9]+)'
        return Action.base_create(string, p, Damage)

    def __init__(self, g):
        super().__init__()
        self.damager_name = g[0]
        self.target_name = g[1]
        self.value = int(g[2])
        self.damage_absorption_list: typing.List[DamageAbsorption] = []


class Death(Action):
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) killed ([^:^\n]+)'
        return Action.base_create(string, p, Death)

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
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) \: Damage Reduction absorbs ([0-9]+) damage'
        return Action.base_create(string, p, DamageReduction)

    def __init__(self, g):
        super().__init__(g)


class DamageResistance(DamageAbsorption):
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) \: Damage Resistance absorbs ([0-9]+) damage'
        return Action.base_create(string, p, DamageResistance)

    def __init__(self, g):
        super().__init__(g)


"""
[CHAT WINDOW TEXT] [Wed Jul 13 15:23:02] Epic Giant Demon : Damage Immunity absorbs 19 point(s) of Physical
"""


class DamageImmunity(DamageAbsorption):
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) \: Damage Immunity absorbs ([0-9]+) point'
        return Action.base_create(string, p, DamageImmunity)

    def __init__(self, g):
        super().__init__(g)


"""
[CHAT WINDOW TEXT] [Mon Jul 11 17:52:32] Wait 10 seconds for hiding
"""


class StealthCooldown(Action):
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] Wait ([0-9]+) seconds for hiding'
        return Action.base_create(string, p, StealthCooldown)

    @staticmethod
    def explicit_create(cooldown: int):
        return StealthCooldown([cooldown / 1000])

    def __init__(self, g):
        super().__init__()
        self.cooldown = int(g[0]) * 1000  # ms


"""
[CHAT WINDOW TEXT] [Wed Jul 13 00:35:34] Dunya Kulakova : Initiative Roll : 20 : (9 + 11 = 20)
"""


class InitiativeRoll(Action):
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) \: Initiative Roll :'
        return Action.base_create(string, p, InitiativeRoll)

    def __init__(self, g):
        super().__init__()
        self.roller_name = g[0]

