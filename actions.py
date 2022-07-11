import re
import logging
from common import *


class Action:
    @staticmethod
    def base_create(string, pattern, action_type):
        m = re.match(pattern, string)
        if m:
            g = m.groups()
            logging.debug('{}'.format(g))
            return action_type(g)

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
        self.reduction = None
        self.resistance = None


class Death(Action):
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) killed ([^:^\n]+)'
        return Action.base_create(string, p, Death)

    def __init__(self, g):
        super().__init__()
        self.killer_name = g[0]
        self.target_name = g[1]


class DamageReduction(Action):
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) \: Damage Reduction absorbs ([0-9]+) damage'
        return Action.base_create(string, p, DamageReduction)

    def __init__(self, g):
        super().__init__()
        self.target_name = g[0]
        self.value = int(g[1])


class DamageResistance(Action):
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) \: Damage Resistance absorbs ([0-9]+) damage'
        return Action.base_create(string, p, DamageResistance)

    def __init__(self, g):
        super().__init__()
        self.target_name = g[0]
        self.value = int(g[1])


"""
[CHAT WINDOW TEXT] [Mon Jul 11 17:52:32] Wait 10 seconds for hiding
"""


class StealthMode(Action):
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] Wait ([0-9]+) seconds for hiding'
        return Action.base_create(string, p, StealthMode)

    def __init__(self, g):
        super().__init__()
        self.cooldown = int(g[0]) * 1000  # ms
