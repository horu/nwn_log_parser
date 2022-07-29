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

    def __init__(self, ts: typing.Optional[int] = None):
        if ts is not None:
            self.timestamp = ts
        else:
            self.timestamp = get_ts()

    def __str__(self):
        return '{}: {}'.format(self.__class__.__name__, str(self.__dict__))

    def get_type(self):
        return self.__class__


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

        # *target concealed: 70%*
        m = re.match(r'target concealed: ([0-9]+)\%', self.result)
        self.concealment = int(m.groups()[0]) if m else 0

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
        p = r'\[CHAT WINDOW TEXT\] \[.+\] (.+) attempts (.+) on ([^:]+) \: \*(.+)\* \: \(([0-9]+) \+ ([0-9]+) \= ([0-9]+)'
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
    @classmethod
    def create(cls, s_attack: SpecialAttack):
        if KNOCKDOWN in s_attack.type:
            return Knockdown(s_attack)
        return None

    def __init__(self, s_attack: SpecialAttack):
        super().__init__()
        self.s_attack = s_attack


"""
[CHAT WINDOW TEXT] [Fri Jul  8 20:25:39] Dunya Kulakova attempts Stunning Fist on TRAINER : *failed* : (15 + 41 = 56)
[CHAT WINDOW TEXT] [Fri Jul  8 20:26:20] Sneak Attack : Dunya Kulakova attempts Stunning Fist on Chaotic Evil : *hit* : (6 + 41 = 47)
"""


class StunningFirst(Action):
    @classmethod
    def create(cls, s_attack: SpecialAttack):
        if STUNNING_FIST in s_attack.type:
            return StunningFirst(s_attack)
        return None

    def __init__(self, s_attack: SpecialAttack):
        super().__init__()
        self.s_attack = s_attack
        self.throw = None

    def is_success(self) -> bool:  # ms
        return self.throw and self.throw.result == FAILURE


"""
[CHAT WINDOW TEXT] [Fri Jul 29 17:27:04] TEST m a attempts Called Shot: Leg on TEST m f s : *hit* : (14 + 61 = 75)
[CHAT WINDOW TEXT] [Fri Jul 29 17:28:39] TEST m a attempts Called Shot: Arm on TEST m f s : *critical hit* : (20 + 61 = 81 : Threat Roll: 19 + 61 = 80)
"""


class CalledShot(Action):
    @classmethod
    def create(cls, s_attack: SpecialAttack):
        if CALLED_SHOT in s_attack.type:
            m = re.match(r'Called Shot: ([LegArm]{3})', s_attack.type)
            assert m is not None
            g = m.groups()
            return CalledShot(s_attack, g[0])

        return None

    def __init__(self, s_attack: SpecialAttack, limb: str):
        super().__init__()
        self.s_attack = s_attack
        self.limb = limb


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

    def get_absorption_sum(self):
        absorb = sum([ad.value for ad in self.damage_absorption_list])
        return absorb


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
        sc.cooldown = cooldown
        return sc

    def __init__(self, g):
        super().__init__()
        self.cooldown = int(g[0]) * 1000  # ms


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
XP DEBT: Decreased by 450 XP
"""


class ExperienceDebtDecrease(Action):
    @classmethod
    def create(cls, string):
        p = r'XP DEBT: Decreased by ([0-9]+) XP'
        return Action.base_create(string, p, cls)

    @classmethod
    def explicit_create(cls):
        return cls(['0'])

    def __init__(self, g):
        super().__init__()
        self.value = int(g[0])


"""
[CHAT WINDOW TEXT] [Thu Jul 14 23:24:05] Experience Points Gained:  535
"""


class Experience(Action):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] Experience Points Gained\:[ ]+([0-9]+)'
        return Action.base_create(string, p, cls)

    @classmethod
    def explicit_create(cls, debt: typing.Optional[ExperienceDebtDecrease] = None, value: typing.Optional[int] = None):
        if debt:
            return cls([str(debt.value)])
        elif value is not None:
            return cls([str(value)])
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


"""
Attempting to fast cast 17 spells.
"""


class RodOfFastCast(Action):
    @classmethod
    def create(cls, string):
        p = r'Attempting to fast cast ([0-9]+) spells.'
        return Action.base_create(string, p, cls)

    def __init__(self, g):
        super().__init__()
        self.cast_count = int(g[0])


"""
[CHAT WINDOW TEXT] [Wed Jul 20 22:55:50] Casting spell Bless at postion 15 on item with metamagic: None
"""


class FastCastEnd(Action):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] Casting spell ([^:]+) at postion'
        return Action.base_create(string, p, cls)

    def __init__(self, g):
        super().__init__()
        self.spell_name = g[0]


"""
[CHAT WINDOW TEXT] [Tue Jul 19 14:40:28] * Divine Favor wore off *
"""


class Debuff(Action):
    @classmethod
    def create(cls, string):
        p = r'\[CHAT WINDOW TEXT\] \[.+\] \* ([^:^*]+) wore off \*'
        return Action.base_create(string, p, cls)

    def __init__(self, g):
        super().__init__()
        self.spell_name = g[0]


"""
UNIQUE CREATURE KILL!
"""


class UniqueDeath(Action):
    @classmethod
    def create(cls, string):
        p = r'UNIQUE CREATURE KILL'
        return Action.base_create(string, p, cls)

    def __init__(self, g):
        super().__init__()