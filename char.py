import collections
import logging
import typing

from actions import *
from buffs import *

AB_ATTACK_LIST_LIMIT = 12
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


class DamagePerRound:
    def __init__(self):
        self.damage_list: typing.List[Damage] = []
        self.max_dpr = 0
        self.max_dpr_ts = 0
        self.last_dpr = 0
        self.last_dpr_ts = 0

    def calculate_dpr(self):
        ts = get_ts()
        self.last_dpr = sum([damage.value for damage in self.damage_list])
        self.last_dpr_ts = ts
        if self.last_dpr > self.max_dpr or ts - self.max_dpr_ts > MAX_DPR_TIMEOUT:
            self.max_dpr = self.last_dpr
            self.max_dpr_ts = ts

    def add_damage(self, damage: Damage) -> None:
        append_fix_time_window(self.damage_list, damage, ROUND_DURATION)
        self.calculate_dpr()


class StatisticStorage:
    def __init__(self):
        self.char_stats = collections.defaultdict(Statistic)
        self.all_chars_stats = Statistic()
        self.caused_dpr = DamagePerRound()

    def reset(self):
        self.__init__()

    def increase(self, char_name: str, stat_name, counter_name, value: int):
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

        self.last_knockdown = Knockdown(SpecialAttack.explicit_create())
        self.stunning_fist_list: typing.List[StunningFirst] = []

        self.last_caused_damage = Damage.explicit_create()
        self.last_received_damage = Damage.explicit_create()
        self.sum_received_damage = 0

        self.death: typing.Optional[Death] = None

        self.stats_storage = StatisticStorage()
        self.hp_list: typing.List[int] = []

        self.timestamp = 0  # last timestamp of action with the char

        self.experience: typing.Optional[Experience] = None

        self.casting_spell: typing.Optional[CastBegin] = None

    def __str__(self):
        return str(self.__dict__)

    def get_target_name(self) -> str:
        if self.ab_attack_list:
            return self.ab_attack_list[-1].target_name
        if self.last_caused_damage:
            return self.last_caused_damage.target_name
        return self.name

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
        return 99

    def get_last_hit_ac_attack_value(self) -> int:
        for attack in reversed(self.ac_attack_list):
            if attack.is_hit() and not attack.is_critical_roll():
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

    def update_timestamp(self) -> Time:
        current_time = get_ts()
        self.timestamp = current_time
        return current_time

    def add_stunning_fist(self, sf: StunningFirst) -> None:
        append_fix_time_window(self.stunning_fist_list, sf, STUNNING_FIST_DURATION)

    def add_caused_damage(self, damage: Damage) -> None:
        self.stats_storage.caused_dpr.add_damage(damage)
        self.last_caused_damage = damage
        self.stats_storage.increase(damage.target_name, 'caused_damage', 'sum', damage.value)
        self.stats_storage.increase(damage.target_name, 'caused_damage', 'count', 1)

    def add_received_damage(self, damage: Damage) -> None:
        if self.death:
            if get_ts() - self.death.timestamp < 700:
                # ignore damage and other actions after death
                # 300 ms between attacks in a series for 2 attacks.
                return
            self.death = None
            self.reset_damage()

        self.sum_received_damage += damage.value
        self.last_received_damage = damage
        self.stats_storage.increase(damage.damager_name, 'received_damage', 'sum', damage.value)
        self.stats_storage.increase(damage.damager_name, 'received_damage', 'count', 1)

    def add_damage_absorption(self, absorption: DamageAbsorption) -> None:
        self.last_received_damage.damage_absorption_list.append(absorption)

    def on_killed(self, death: Death, experience: typing.Optional[Experience]) -> None:
        if not self.experience or not experience or self.experience.value == experience.value:
            hp = self.sum_received_damage
            logging.debug('HP: {}'.format(hp))
            append_fix_size(self.hp_list, hp, HP_LIST_LIMIT)
        elif self.experience.value != experience.value:
            logging.debug('UNIQUE CHAR DETECTED: {}(HP {})'.format(self.name, self.sum_received_damage))
        if experience:
            self.experience = experience
        self.death = death

    def get_avg_hp(self) -> int:
        avg_hp = 0
        if self.hp_list:
            avg_hp = sum(self.hp_list) / len(self.hp_list)
        return int(avg_hp)

    def get_cur_hp(self) -> int:
        cur_hp = self.get_avg_hp() - self.sum_received_damage
        return cur_hp

    def reset_damage(self) -> None:
        logging.debug('RESET DAMAGE FOR {}'.format(self.name))
        self.sum_received_damage = 0

    def get_experience_value(self) -> int:
        if self.experience:
            return self.experience.value
        return 0

    def cast_begin(self, cast: CastBegin) -> None:
        self.casting_spell = cast

    def cast_end(self, cast: CastEnd) -> None:
        if self.casting_spell and self.casting_spell.spell_name == cast.spell_name:
            self.casting_spell = None

    def cast_interruption(self, cast: CastInterruption) -> None:
        self.casting_spell = None


class Player(Character):
    def __init__(self):
        super(Player, self).__init__()

        self.stealth_cooldown = StealthCooldown.explicit_create(0)
        self.initiative_roll: typing.Optional[InitiativeRoll] = None

        self.last_heal = Heal.explicit_create()
        self.buff_dict: typing.Dict[str, typing.Optional[Buff]] = {}

    def cast_end(self, cast: CastEnd) -> None:
        super(Player, self).cast_end(cast)

        buff = Buff.create_from_cast(cast)
        if buff:
            self.buff_dict[buff.buff_name] = buff

    def resting(self):
        self.reset_damage()
        self.clear_buffs()

    def item_usage(self, item_name: str):
        buff = Buff.create_from_usage(item_name)
        if buff:
            self.buff_dict[buff.buff_name] = buff

    def debuff(self, debuff: Debuff):
        buff = self.buff_dict.get(debuff.buff_name)
        # ignore redebuff message
        if not buff or abs(debuff.timestamp - buff.timestamp) > 1000:
            self.buff_dict[debuff.buff_name] = None

    def clear_buffs(self):
        for name in self.buff_dict.keys():
            self.buff_dict[name] = None

    def on_killed(self, death: Death, experience: Experience) -> None:
        self.death = death
        self.clear_buffs()
        # next add_heal gets full hp - 1

    def add_heal(self, heal: Heal) -> None:
        self.last_heal = heal
        if self.death:
            self.death = None
            hp = heal.value + 1
            logging.debug('PLAYER HP: {}'.format(hp))
            self.hp_list = [hp]
            self.reset_damage()
        else:
            self.sum_received_damage -= heal.value

    def on_fortitude_save(self, throw: SavingThrow) -> None:
        if throw.type != 'Fortitude Save':
            return

        for sf in self.stunning_fist_list:
            if sf.s_attack.target_name == throw.target_name and sf.s_attack.is_success() and sf.throw is None:
                sf.throw = throw
                break

    def start_fight(self, attack: Attack) -> None:
        # uses to indicate start fight after stealth mode on next attack to start stealth cooldown
        if not HIPS:
            return

        if self.initiative_roll:
            self.initiative_roll = None
            self.stealth_cooldown = StealthCooldown.explicit_create(STEALTH_MODE_CD)
            return

        sm_cooldown = self.stealth_cooldown.get_duration()
        is_sneak = SNEAK_ATTACK in attack.specials
        last_attack = self.get_last_ab_attack()
        if last_attack:
            time_since_last_attack = attack.timestamp - last_attack.timestamp
            logging.debug('Start fight: {} {} {}'.format(sm_cooldown, is_sneak, time_since_last_attack))
            if sm_cooldown == 0 and time_since_last_attack > 2500 and is_sneak:
                # maybe it is the first attack on stealth mode
                self.stealth_cooldown = StealthCooldown.explicit_create(STEALTH_MODE_CD)
                return
