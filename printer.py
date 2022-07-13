import typing
import collections
from tabulate import tabulate
import pandas
import tabulate

from char import *


CHARS_TO_PRINT_LIMIT_NORM = 2
CHARS_TO_PRINT_LIMIT_MAX = 30
CHARS_TO_PRINT_TIMEOUT = 3000


def print_progress_bar(name: str, value: int, min_value: int, max_value: int, line_len: int, bar_symbol: str) -> str:
    if value >= min_value and (max_value - min_value) > 0:
        header = '{}: {:>5d} '.format(name, value)
        bar_len = int((line_len - len(header)) * (value - min_value) / (max_value - min_value))
        text = '\n{}{}'.format(header, bar_symbol * bar_len)
        return text
    return ''


def create_progress_bars(char: Character, line_size: int) -> str:
    text = ''

    # Knockdown cooldown
    last_kd = char.last_knockdown
    if last_kd:
        value = KNOCKDOWN_PVE_CD - (get_ts() - last_kd.timestamp)
        bar_symbol = '-'
        if last_kd.is_hit():
            bar_symbol = '+'
        text += print_progress_bar('KD', value, 0, KNOCKDOWN_PVE_CD, line_size, bar_symbol)

    # Stunning fist duration
    for sf in reversed(char.stunning_fist_list):
        value = sf.duration()
        if value:
            text += print_progress_bar('SF', value, 0, STUNNING_FIST_DURATION, line_size, '*')
            break

    # Stealth mode cooldown
    last_sm = char.stealth_cooldown
    if last_sm:
        value = last_sm.cooldown - 1000 - (get_ts() - last_sm.timestamp)  # 1000 - server fix
        text += print_progress_bar('SM', value, 0, STEALTH_MODE_CD, line_size, '=')

    # Attacks min/max
    ab_attack_list = char.ab_attack_list
    if ab_attack_list and (get_ts() - ab_attack_list[-1].timestamp) <= 6000:
        max_ab = char.get_max_ab_attack_base()
        min_ab = char.get_min_ab_attack_base()
        last_ab = char.get_last_ab_attack_base()
        text += print_progress_bar('AB', last_ab, min_ab, max_ab, line_size, '|')

    return text


def print_special_char(char: Character) -> list:
    text = []
    if char.last_knockdown:
        text.append('KD: {:d}({})'.format(char.last_knockdown.value, char.last_knockdown.result))

    if char.stunning_fist_list:
        last_sf = char.stunning_fist_list[-1]
        dc = last_sf.throw.dc if last_sf.throw else 0
        text.append('SF: {:d}({})'.format(dc, last_sf.s_attack.result))
    return text


def print_char_without_name(char: Character) -> list:
    cd = char.get_caused_damage()
    rd = char.get_received_damage()
    return [
        'AC: {:d}/{:d}({:d})'.format(char.ac[0], char.ac[1], char.get_last_hit_ac_attack_value()),
        'AB: {:d}({:d})'.format(char.get_max_ab_attack_base(), char.get_last_ab_attack_base()),
        'FT: {:d}({:d})'.format(char.fortitude, char.last_fortitude_dc),
        'WL: {:d}({:d})'.format(char.will, char.last_will_dc),
        'CD: {:d}({:d})'.format(cd[0], cd[1]),
        'RD: {:d}({:d}/{:d}/{:d})'.format(rd[0], rd[1], rd[2], rd[3]),
    ]


def print_char(char: Character) -> list:
    return [char.name] + print_char_without_name(char)


class CharSorter:
    def __init__(self, player: Character):
        self.player = player

    def sort(self, chars: typing.List[Character]) -> typing.List[Character]:
        chars.sort(key=lambda x: x.timestamp, reverse=True)
        chars.sort(key=self.sort_by_player_contact_ts, reverse=True)
        return chars

    def sort_by_player_contact_ts(self, char: Character) -> int:
        last_player_contact_ts = 0

        for attack in self.player.ab_attack_list:
            if char.name == attack.target_name:
                last_player_contact_ts = max(last_player_contact_ts, attack.timestamp)

        for attack in self.player.ac_attack_list:
            if char.name == attack.attacker_name:
                last_player_contact_ts = max(last_player_contact_ts, attack.timestamp)

        action = self.player.last_hit_ac_attack
        if action and char.name == action.attacker_name:
            last_player_contact_ts = max(last_player_contact_ts, action.timestamp)

        action = self.player.last_received_damage
        if action and action.damager_name == char.name:
            last_player_contact_ts = max(last_player_contact_ts, action.timestamp)

        action = self.player.last_caused_damage
        if action and action.target_name == char.name:
            last_player_contact_ts = max(last_player_contact_ts, action.timestamp)

        return last_player_contact_ts


class Printer:
    def __init__(self):
        self.chars_to_print: typing.List[Character] = []
        self.chars_to_print_ts = 0
        self.chars_to_print_limit = CHARS_TO_PRINT_LIMIT_NORM

    def change_char_list(self):
        if self.chars_to_print_limit == CHARS_TO_PRINT_LIMIT_NORM:
            self.chars_to_print_limit = CHARS_TO_PRINT_LIMIT_MAX
        else:
            self.chars_to_print_limit = CHARS_TO_PRINT_LIMIT_NORM
        self.chars_to_print_ts = 0

    def print(self, player: Character, chars: typing.List[Character]) -> str:
        ts = get_ts()
        if ts - self.chars_to_print_ts > CHARS_TO_PRINT_TIMEOUT:
            chars_without_player = [char for char in chars if char is not player]
            sorter = CharSorter(player)
            sorted_chars = sorter.sort(chars_without_player)

            self.chars_to_print = sorted_chars[:self.chars_to_print_limit]
            self.chars_to_print.sort(key=lambda x: x.name)
            self.chars_to_print_ts = ts

        table = [print_char(char) for char in self.chars_to_print]
        table.append(['{}\n'.format(' | '.join(print_special_char(player)))]
                     + print_char_without_name(player))

        df = pandas.DataFrame(table)
        text = str(tabulate.tabulate(df, tablefmt='plain', showindex=False))

        line_size = len(text.splitlines()[0])
        text += create_progress_bars(player, line_size)

        if self.chars_to_print_limit > CHARS_TO_PRINT_LIMIT_NORM:
            text = '{}\n'.format('#' * line_size) + text
            text += '\n{}'.format('#' * line_size)

        return text