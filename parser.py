import collections
from tabulate import tabulate
import pandas
import tabulate

from char import *


def print_progress_bar(name: str, value: int, max_value: int, line_len: int, bar_sym: str) -> str:
    if value >= 0:
        header = '{}: {:>5d} '.format(name, value)
        bar_len = int((line_len - len(header)) * value / max_value)
        text = '\n{}{}'.format(header, bar_sym * bar_len)
        return text
    return ''


def create_progress_bars(char: Character, line_size: int) -> str:
    text = ''

    # Knockdown cooldown
    last_kd = char.last_knockdown
    if last_kd:
        value = KNOCKDOWN_PVE_CD - (get_ts() - last_kd.timestamp)
        text += print_progress_bar('KD', value, KNOCKDOWN_PVE_CD, line_size, '=')

    # Stuning fist duration
    last_sf = char.last_stunning_fist
    if last_sf and last_sf.throw and last_sf.throw.result == FAILURE:
        value = STUNNING_FIST_DURATION - (get_ts() - last_sf.s_attack.timestamp)
        text += print_progress_bar('SF', value, STUNNING_FIST_DURATION, line_size, '*')

    last_sm = char.stealth_mode
    if last_sm:
        value = last_sm.cooldown - 1000 - (get_ts() - last_sm.timestamp)  # 1000 - поправка на сервер
        text += print_progress_bar('SM', value, STEALTH_MODE_CD, line_size, '+')

    return text


def print_special_char(char: Character) -> list:
    text = []
    if char.last_knockdown:
        text.append('KD: {:d}({})'.format(char.last_knockdown.value, char.last_knockdown.result))

    if char.last_stunning_fist:
        dc = char.last_stunning_fist.throw.dc if char.last_stunning_fist.throw else 0
        text.append('SF: {:d}({})'.format(dc, char.last_stunning_fist.s_attack.result))
    return text


def print_char_without_name(char: Character) -> list:
    # ab_list = [str(ab) for ab in sorted(set(char.ab_list), reverse=True)][:1]

    cd = char.get_caused_damage()
    rd = char.get_received_damage()
    max_ab = sorted(char.ab_list, reverse=True)[0] if char.ab_list else 0
    return [
        'AC: {:d}/{:d}({:d})'.format(char.ac[0], char.ac[1], char.get_last_ac_attack_value()),
        'AB: {:d}({:d})'.format(max_ab, char.get_last_ab_attack_base()),
        'FT: {:d}({:d})'.format(char.fortitude, char.last_fortitude_dc),
        'WL: {:d}({:d})'.format(char.will, char.last_will_dc),
        'CD: {:d}({:d})'.format(cd[0], cd[1]),
        'RD: {:d}({:d}/{:d}/{:d})'.format(rd[0], rd[1], rd[2], rd[3]),
    ]


def print_char(char: Character) -> list:
    return [char.name] + print_char_without_name(char)


class Parser:
    def __init__(self, player_name: str):
        self.characters = collections.defaultdict(Character)
        self.player = self.get_char(player_name)

    def get_char(self, name: str) -> Character:
        char = self.characters[name]
        char.name = name
        char.update_timestamp()
        return char

    def push_line(self, line) -> None:
        logging.debug(line)
        attack = Attack.create(line)
        if attack:
            logging.debug(str(attack))

            attacker = self.get_char(attack.attacker_name)
            attacker.update_ab(attack)

            target = self.get_char(attack.target_name)
            target.update_ac(attack)
            return

        throw = SavingThrow.create(line)
        if throw:
            logging.debug(str(throw))
            target = self.get_char(throw.target_name)
            if FORTITUDE in throw.type:
                target.fortitude = throw.base
                target.last_fortitude_dc = throw.dc
                self.player.on_fortitude_save(throw)

            elif WILL in throw.type:
                target.will = throw.base
                target.last_will_dc = throw.dc
            return

        s_attack = SpecialAttack.create(line)
        if s_attack:
            logging.debug(str(s_attack))
            attacker = self.get_char(s_attack.attacker_name)
            if KNOCKDOWN in s_attack.type:
                attacker.last_knockdown = s_attack
            elif STUNNING_FIST in s_attack.type:
                attacker.last_stunning_fist = StunningFirst(s_attack)
            return

        damage = Damage.create(line)
        if damage:
            logging.debug(str(damage))

            damager = self.get_char(damage.damager_name)
            target = self.get_char(damage.target_name)

            if damager is self.player or target is self.player:
                damager.add_caused_damage(damage)
                target.add_received_damage(damage)
            return

        death = Death.create(line)
        if death:
            logging.debug(str(death))

            target = self.get_char(death.target_name)
            target.on_killed(death)
            self.player.on_killed(death)
            return

        d_reduction = DamageReduction.create(line)
        if d_reduction:
            logging.debug(str(d_reduction))

            target = self.get_char(d_reduction.target_name)
            target.on_damage_reduction(d_reduction)
            return

        d_resistance = DamageResistance.create(line)
        if d_resistance:
            logging.debug(str(d_resistance))

            target = self.get_char(d_resistance.target_name)
            target.on_damage_resistance(d_resistance)
            return

        stealth_mode = StealthMode.create(line)
        if stealth_mode:
            logging.debug(str(stealth_mode))

            self.player.stealth_mode = stealth_mode
            return

    def sort_char(self, char: Character) -> int:
        last_player_contact_ts = 0
        if char.last_ab_attack and char.last_ab_attack.target_name == self.player.name:
            last_player_contact_ts = max(last_player_contact_ts, char.last_ab_attack.timestamp)
        if char.last_ac_attack and char.last_ac_attack.attacker_name == self.player.name:
            last_player_contact_ts = max(last_player_contact_ts, char.last_ac_attack.timestamp)
        return last_player_contact_ts

    def get_stat(self) -> str:
        MAX_PRINT = 3

        chars = [char for char in self.characters.values() if char is not self.player]
        chars.sort(key=lambda x: x.timestamp, reverse=True)
        chars.sort(key=self.sort_char, reverse=True)
        chars = chars[:MAX_PRINT]
        chars.sort(key=lambda x: x.name)

        table = [print_char(char) for char in chars]
        table.append(['{}\n'.format(' | '.join(print_special_char(self.player)))]
                     + print_char_without_name(self.player))

        df = pandas.DataFrame(table)
        text = str(tabulate.tabulate(df, tablefmt='plain', showindex=False))

        line_size = len(text.splitlines()[0])
        text += create_progress_bars(self.player, line_size)

        return text