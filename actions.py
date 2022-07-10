import re
import logging
from common import *


class Action:
    def __init__(self):
        self.timestamp = get_ts()

    def __str__(self):
        return str(self.__dict__)


class Attack(Action):
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] (.+) attacks ([^:]+) \: \*(.+)\* \: \(([0-9]+) \+ ([0-9]+) \= ([0-9]+)'
        m = re.match(p, string)
        if m:
            g = m.groups()
            logging.debug('{}'.format(g))
            return Attack(g)

        return None

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
        m = re.match(p, string)
        if m:
            g = m.groups()
            logging.debug('{}'.format(g))
            return SpecialAttack(g)

        return None

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
        m = re.match(p, string)
        if m:
            g = m.groups()
            logging.debug('{}'.format(g))
            return SavingThrow(g)

        return None

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
        m = re.match(p, string)
        if m:
            g = m.groups()
            logging.debug('{}'.format(g))
            return Damage(g)

        return None

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
        m = re.match(p, string)
        if m:
            g = m.groups()
            logging.debug('{}'.format(g))
            return Death(g)

        return None

    def __init__(self, g):
        super().__init__()
        self.killer_name = g[0]
        self.target_name = g[1]


class DamageReduction(Action):
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) \: Damage Reduction absorbs ([0-9]+) damage'
        m = re.match(p, string)
        if m:
            g = m.groups()
            logging.debug('{}'.format(g))
            return DamageReduction(g)

        return None

    def __init__(self, g):
        super().__init__()
        self.target_name = g[0]
        self.value = int(g[1])


class DamageResistance(Action):
    @staticmethod
    def create(string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] ([^:]+) \: Damage Resistance absorbs ([0-9]+) damage'
        m = re.match(p, string)
        if m:
            g = m.groups()
            logging.debug('{}'.format(g))
            return DamageResistance(g)

        return None

    def __init__(self, g):
        super().__init__()
        self.target_name = g[0]
        self.value = int(g[1])