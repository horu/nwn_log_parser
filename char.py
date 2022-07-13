import collections
import typing

from actions import *

AB_ATTACK_LIST_LIMIT = 10
HP_LIST_LIMIT = 10
AC_ATTACK_LIST_LIMIT = 30
DAMAGE_LIST_LIMIT = 20
MAX_DPR_TIMEOUT = 60000


class ValueStatistic:
    def __init__(self):
        self.sum: int = 0
        self.count: int = 0


class Statistic:
    def __init__(self):
        self.caused_damage = ValueStatistic()
        self.received_damage = ValueStatistic()
        self.hit_ab_attack = ValueStatistic()
        self.hit_ac_attack = ValueStatistic()
        self.death: typing.Optional[Death] = None  # target killed


class DamagePerRound:
    def __init__(self):
        self.damage_list: typing.List[Damage] = []
        self.max_dpr = 0
        self.ts_max_dpr = 0
        self.last_dpr = 0

    def calculate_dpr(self) -> int:
        self.filter_damage_list()
        dpr = sum([damage.value for damage in self.damage_list])
        ts = get_ts()
        if dpr > self.max_dpr or ts - self.ts_max_dpr > MAX_DPR_TIMEOUT:
            self.max_dpr = dpr
            self.ts_max_dpr = ts
        return dpr

    def add_damage(self, damage: Damage) -> None:
        append_fix_time_window(self.damage_list, damage, ROUND_DURATION)
        self.last_dpr = self.calculate_dpr()

    def filter_damage_list(self):
        ts = get_ts()
        self.damage_list = [damage for damage in self.damage_list if ts - damage.timestamp <= ROUND_DURATION]


class StatisticStorage:
    def __init__(self):
        self.char_stats = collections.defaultdict(Statistic)
        self.all_chars_stats = Statistic()
        self.this_char_death: typing.Optional[Death] = None
        self.caused_dpr = DamagePerRound()

    def reset(self):
        self.char_stats = collections.defaultdict(Statistic)
        self.all_chars_stats = Statistic()
        self.this_char_death = None

    def increase(self, char_name: str, stat_name, counter_name, value: int):
        if self.this_char_death:
            if get_ts() - self.this_char_death.timestamp < 1000:
                # ignore damage and other actions after death
                return
            self.reset()

        char_stats = self.char_stats[char_name]
        if char_stats.death:
            if get_ts() - char_stats.death.timestamp < 1000:
                # ignore damage and other actions after death
                return

            self.char_stats[char_name] = Statistic()
            char_stats = self.char_stats[char_name]

        self._increase_stat(char_stats, stat_name, counter_name, value)
        self._increase_stat(self.all_chars_stats, stat_name, counter_name, value)

    @staticmethod
    def _increase_stat(char_stats: Statistic, stat_name, counter_name, value: int):
        stat = getattr(char_stats, stat_name)
        new_value = getattr(stat, counter_name) + value
        setattr(stat, counter_name, new_value)


class Character:
    def __init__(self):
        self.name = ''
        self.ac_attack_list: typing.List[Attack] = []
        self.ab_attack_list: typing.List[Attack] = []  # last attack in and of list 50/45/40/35

        self.fortitude = 0
        self.last_fortitude_dc = 0

        self.will = 0
        self.last_will_dc = 0

        self.last_knockdown: typing.Optional[Knockdown] = None
        self.stunning_fist_list: typing.List[StunningFirst] = []

        self.last_caused_damage: typing.Optional[Damage] = None
        self.last_received_damage: typing.Optional[Damage] = None

        self.stealth_cooldown = StealthCooldown.explicit_create(0)

        self.initiative_roll: typing.Optional[InitiativeRoll] = None

        self.stats_storage = StatisticStorage()
        self.hp_list: typing.List[int] = []

        self.timestamp = 0  # last timestamp of action with the char

    def __str__(self):
        return str(self.__dict__)

    def start_fight(self, attack: Attack) -> None:
        # uses to indicate start fight after stealth mode on next attack to start stealth cooldown
        if self.initiative_roll:
            self.initiative_roll = None
            self.stealth_cooldown = StealthCooldown.explicit_create(STEALTH_MODE_CD)
            return

        sm_cooldown = self.stealth_cooldown.get_duration()
        is_sneak = SNEAK_ATTACK in attack.specials
        last_attack = self.get_last_ab_attack()
        if sm_cooldown == 0 and last_attack and attack.timestamp - last_attack.timestamp > 2000 and is_sneak:
            # maybe it is the first attack on stealth mode
            self.stealth_cooldown = StealthCooldown.explicit_create(STEALTH_MODE_CD)
            return

    # ac
    def add_ac(self, attack: Attack):
        append_fix_size(self.ac_attack_list, attack, AC_ATTACK_LIST_LIMIT)
        if attack.is_hit():
            self.stats_storage.increase(attack.attacker_name, 'hit_ac_attack', 'count', 1)
        self.stats_storage.increase(attack.attacker_name, 'hit_ac_attack', 'sum', 1)

    def get_max_miss_ac(self) -> int:
        miss_attacks = [attack for attack in self.ac_attack_list if attack.is_miss() and not attack.is_critical_roll()]
        if miss_attacks:
            miss_attacks.sort(key=lambda x: x.value)
            return miss_attacks[-1].value
        return 0

    def get_min_hit_ac(self) -> int:
        miss_attacks = [attack for attack in self.ac_attack_list if attack.is_hit() and not attack.is_critical_roll()]
        if miss_attacks:
            miss_attacks.sort(key=lambda x: x.value)
            return miss_attacks[0].value
        return 0

    def get_last_hit_ac_attack_value(self) -> int:
        for attack in reversed(self.ac_attack_list):
            if attack.is_hit():
                return attack.value
        return 0

    # ab
    def add_ab(self, attack: Attack):
        append_fix_size(self.ab_attack_list, attack, AB_ATTACK_LIST_LIMIT)
        self.stats_storage.increase(attack.target_name, 'hit_ab_attack', 'sum', 1)
        if attack.is_hit():
            self.stats_storage.increase(attack.target_name, 'hit_ab_attack', 'count', 1)

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
            ab = sorted(self.ab_attack_list, key=lambda x: x.base, reverse=True)[0]
            return ab.base
        return 0

    def get_min_ab_attack_base(self) -> int:
        if self.ab_attack_list:
            ab = sorted(self.ab_attack_list, key=lambda x: x.base, reverse=False)[0]
            return ab.base
        return 0

    def update_timestamp(self) -> None:
        current_time = get_ts()
        self.timestamp = current_time
        return current_time

    def add_stunning_fist(self, sf: StunningFirst) -> None:
        new_sf_list = [
            sf for sf in self.stunning_fist_list if sf.s_attack.is_success() and (sf.throw is None or sf.get_duration())]
        self.stunning_fist_list = new_sf_list
        self.stunning_fist_list.append(sf)

    def add_caused_damage(self, damage: Damage) -> None:
        self.stats_storage.caused_dpr.add_damage(damage)
        self.last_caused_damage = damage
        self.stats_storage.increase(damage.target_name, 'caused_damage', 'sum', damage.value)
        self.stats_storage.increase(damage.target_name, 'caused_damage', 'count', 1)

    def add_received_damage(self, damage: Damage) -> None:
        self.last_received_damage = damage
        self.stats_storage.increase(damage.damager_name, 'received_damage', 'sum', damage.value)
        self.stats_storage.increase(damage.damager_name, 'received_damage', 'count', 1)

    def add_damage_absorption(self, absorption: DamageAbsorption) -> None:
        last_rd = self.last_received_damage
        if last_rd:
            last_rd.damage_absorption_list.append(absorption)

    def on_killed(self, death: Death) -> None:
        if death.target_name == self.name:
            hp = self.stats_storage.all_chars_stats.received_damage.sum
            append_fix_size(self.hp_list, hp, HP_LIST_LIMIT)
            self.stats_storage.this_char_death = death
        else:
            killed_stat = self.stats_storage.char_stats[death.target_name]
            killed_stat.death = death

    def on_fortitude_save(self, throw: SavingThrow) -> None:
        for sf in self.stunning_fist_list:
            if sf.s_attack.target_name == throw.target_name and sf.throw is None:
                sf.throw = throw

    def get_avg_hp(self) -> int:
        avg_hp = 0
        if self.hp_list:
            avg_hp = sum(self.hp_list) / len(self.hp_list)
        return int(avg_hp)

