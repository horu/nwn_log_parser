import collections
import typing

from actions import *

ATTACK_LIST_LIMIT = 10


class Character:
    def __init__(self):
        self.name = ''
        self.ac = [0, 99]  # min/max passible ac
        self.last_hit_ac_attack: typing.Optional[Attack] = None  # last success attack to char
        self.ac_attack_list: typing.List[Attack] = []  # last attack in and of list 50/45/40/35

        self.ab_attack_list: typing.List[Attack] = []  # last attack in and of list 50/45/40/35

        self.fortitude = 0
        self.last_fortitude_dc = 0

        self.will = 0
        self.last_will_dc = 0

        self.last_knockdown: typing.Optional[SpecialAttack] = None
        self.stunning_fist_list: typing.List[StunningFirst] = []

        self.caused_damage = collections.defaultdict(int)  # {name: damage}
        self.received_damage = collections.defaultdict(int)  # {name: damage}

        self.last_caused_damage: typing.Optional[Damage] = None
        self.last_received_damage: typing.Optional[Damage] = None

        self.stealth_cooldown: typing.Optional[StealthCooldown] = None

        self.initiative_roll: typing.Optional[InitiativeRoll] = None

        self.timestamp = 0  # last timestamp of action with the char

    def __str__(self):
        return str(self.__dict__)

    def start_fight(self):
        # uses to indicate start fight after stealth mode on next attack to start stealth cooldown
        if self.initiative_roll:
            self.initiative_roll = None
            self.stealth_cooldown = StealthCooldown.explicit_create(STEALTH_MODE_CD)

    def add_ac(self, attack):
        append_fix_size(self.ac_attack_list, attack, ATTACK_LIST_LIMIT)

        if attack.result == MISS:
            self.ac[0] = max(self.ac[0], attack.value + 1)
        elif attack.is_hit():
            self.last_hit_ac_attack = attack
            if attack.roll != 1 and attack.roll != 20:
                self.ac[1] = min(self.ac[1], attack.value)

    def add_ab(self, attack):
        append_fix_size(self.ab_attack_list, attack, ATTACK_LIST_LIMIT)

    def update_timestamp(self):
        current_time = get_ts()
        self.timestamp = current_time
        return current_time

    def add_stunning_fist(self, sf: StunningFirst):
        new_sf_list = [sf for sf in self.stunning_fist_list if sf.throw is None or sf.duration()]
        self.stunning_fist_list = new_sf_list
        self.stunning_fist_list.append(sf)

    def add_caused_damage(self, damage: Damage):
        # append_fix_size(self.caused_damage_list, damage, 30)
        # self.caused_damage += damage.value
        self.caused_damage[damage.target_name] += damage.value
        if self.caused_damage[damage.target_name] >= DAMAGE_LIMIT:
            self.caused_damage[damage.target_name] -= DAMAGE_LIMIT
        self.last_caused_damage = damage

    def add_received_damage(self, damage: Damage):
        # append_fix_size(self.received_damage_list, damage, 30)
        # self.received_damage += damage.value
        self.received_damage[damage.damager_name] += damage.value
        if self.received_damage[damage.target_name] >= DAMAGE_LIMIT:
            self.received_damage[damage.target_name] -= DAMAGE_LIMIT
        self.last_received_damage = damage

    def add_damage_absorption(self, absorption: DamageAbsorption):
        last_rd = self.last_received_damage
        if last_rd:
            last_rd.damage_absorption_list.append(absorption)

    def on_killed(self, death: Death):
        if death.target_name in self.caused_damage:
            del self.caused_damage[death.target_name]
        if death.killer_name in self.received_damage:
            del self.received_damage[death.killer_name]

    def on_fortitude_save(self, throw: SavingThrow):
        for sf in self.stunning_fist_list:
            if sf.s_attack.target_name == throw.target_name and sf.throw is None:
                sf.throw = throw

    def get_last_hit_ac_attack_value(self) -> int:
        if self.last_hit_ac_attack:
            return self.last_hit_ac_attack.value
        return 0

    def get_last_ab_attack(self) -> typing.Optional[Attack]:
        if self.ab_attack_list:
            return self.ab_attack_list[-1]
        return None

    def get_last_ab_attack_base(self) -> int:
        last_ab = self.get_last_ab_attack()
        if last_ab:
            return last_ab.base
        return 0

    def get_max_ab_attack_base(self) -> int:
        if self.ab_attack_list:
            max_ab = sorted(self.ab_attack_list, key=lambda x: x.base, reverse=True)[0]
            return max_ab.base
        return 0

    def get_min_ab_attack_base(self) -> int:
        if self.ab_attack_list:
            max_ab = sorted(self.ab_attack_list, key=lambda x: x.base, reverse=False)[0]
            return max_ab.base
        return 0
