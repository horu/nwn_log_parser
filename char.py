import collections

from actions import *


class Character:
    def __init__(self):
        self.name = ''
        self.ac = [0, 256]  # min/max passible ac
        self.last_ac_attack = None  # last success attack to char

        self.ab_list = []  # 50/45/40/35
        self.last_ab_attack = None  # last attack

        self.fortitude = 0
        self.last_fortitude_dc = 0

        self.will = 0
        self.last_will_dc = 0

        self.last_knockdown = None
        self.last_stunning_fist = None

        # self.caused_damage_list = []
        # self.received_damage_list = []
        self.caused_damage = collections.defaultdict(int)  # {name: damage}
        self.received_damage = collections.defaultdict(int)  # {name: damage}
        # self.caused_damage = 0
        self.last_caused_damage = None

        # self.received_damage = 0
        self.last_received_damage = None

        self.timestamp = 0  # last timestamp of action with the char

    def update_ac(self, attack):
        if attack.roll == 1 or attack.roll == 20:
            return

        if attack.result == MISS:
            self.ac[0] = max(self.ac[0], attack.value + 1)
        elif attack.result == HIT or attack.result == CRITICAL_HIT:
            self.last_ac_attack = attack
            self.ac[1] = min(self.ac[1], attack.value)

    def update_ab(self, attack):
        self.last_ab_attack = attack
        append_fix_size(self.ab_list, attack.base, 10)

    def update_timestamp(self):
        current_time = get_ts()
        self.timestamp = current_time
        return current_time

    def add_caused_damage(self, damage: Damage):
        # append_fix_size(self.caused_damage_list, damage, 30)
        # self.caused_damage += damage.value
        self.caused_damage[damage.target_name] += damage.value
        if self.caused_damage[damage.target_name] >= DAMAGE_LIMIT:
            self.caused_damage[damage.target_name] -= DAMAGE_LIMIT
        self.last_caused_damage = damage

    def add_received_damage(self, damage: Damage):
        # append_fix_size(self.received_damage_list, damage, 30)
        self.received_damage[damage.damager_name] += damage.value
        if self.received_damage[damage.target_name] >= DAMAGE_LIMIT:
            self.received_damage[damage.target_name] -= DAMAGE_LIMIT
        # self.received_damage += damage.value
        self.last_received_damage = damage

    def on_damage_reduction(self, reduction: DamageReduction):
        if self.last_received_damage and self.last_received_damage.target_name == reduction.target_name:
            self.last_received_damage.reduction = reduction

    def on_damage_resistance(self, resistance: DamageResistance):
        if self.last_received_damage and self.last_received_damage.target_name == resistance.target_name:
            self.last_received_damage.resistance = resistance

    def on_killed(self, death: Death):
        if death.target_name in self.caused_damage:
            del self.caused_damage[death.target_name]
        if death.killer_name in self.received_damage:
            del self.received_damage[death.killer_name]

    def on_fortitude_save(self, throw: SavingThrow):
        if self.last_stunning_fist and self.last_stunning_fist.s_attack.target_name == throw.target_name:
            self.last_stunning_fist.throw = throw

    def __str__(self):
        return str(self.to_print())

    def to_player_print(self):
        text = []
        if self.last_knockdown:
            knockdown_pve_cd = KNOCKDOWN_PVE_CD - (get_ts() - self.last_knockdown.timestamp)
            knockdown_pvp_cd = KNOCKDOWN_PVP_CD - (get_ts() - self.last_knockdown.timestamp)
            text.append('KD: {:d}({}) {}({})'.format(
                self.last_knockdown.value,
                self.last_knockdown.result,
                knockdown_pve_cd if knockdown_pve_cd >= 0 else 0,
                knockdown_pvp_cd if knockdown_pvp_cd >= 0 else 0))

        if self.last_stunning_fist:
            duration = 0
            dc = 0
            if self.last_stunning_fist.throw:
                if self.last_stunning_fist.throw.result == FAILURE:
                    duration = STUNNING_FIST_DURATION - (get_ts() - self.last_stunning_fist.s_attack.timestamp)
                dc = self.last_stunning_fist.throw.dc
            text.append('SF: {:d}({}) {}'.format(
                dc,
                self.last_stunning_fist.s_attack.result,
                duration if duration >= 0 else 0))
        return text

    def to_print_without_name(self):
        ab_list = [str(ab) for ab in sorted(set(self.ab_list), reverse=True)][:3]
        cd = self.get_caused_damage()
        rd = self.get_received_damage()
        return [
            'AC: {:d}/{:d}({:d})'.format(self.ac[0], self.ac[1], self.get_last_ac_attack_value()),
            'AB: {}({:d})'.format('/'.join(ab_list), self.get_last_ab_attack_base()),
            'FT: {:d}({:d})'.format(self.fortitude, self.last_fortitude_dc),
            'WL: {:d}({:d})'.format(self.will, self.last_will_dc),
            'CD: {:d}({:d})'.format(cd[0], cd[1]),
            'RD: {:d}({:d}/{:d}/{:d})'.format(rd[0], rd[1], rd[2], rd[3]),
        ]

    def to_print(self):
        return [self.name] + self.to_print_without_name()

    def get_last_ac_attack_value(self):
        if self.last_ac_attack:
            return self.last_ac_attack.value
        return 0

    def get_last_ab_attack_base(self):
        if self.last_ab_attack:
            return self.last_ab_attack.base
        return 0

    def get_received_damage(self):
        if self.last_received_damage:
            return (
                self.received_damage[self.last_received_damage.damager_name],
                self.last_received_damage.value,
                self.last_received_damage.reduction.value if self.last_received_damage.reduction else 0,
                self.last_received_damage.resistance.value if self.last_received_damage.resistance else 0,
            )
        return 0, 0, 0, 0

    def get_caused_damage(self):
        if self.last_caused_damage:
            return self.caused_damage[self.last_caused_damage.target_name], self.last_caused_damage.value
        return 0, 0
