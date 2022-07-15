import logging
import typing
import collections
from tabulate import tabulate
import pandas
import tabulate

from char import *


CHARS_COUNT_WIDE_MODE = 30
CHARS_TO_PRINT_TIMEOUT = 5000
DAMAGE_PRINT_LIMIT = 1000


def convert_damage(value: int) -> str:
    if abs(value) > DAMAGE_PRINT_LIMIT:
        return '{:.1f}'.format(value / DAMAGE_PRINT_LIMIT)
    return str(value)


def print_progress_bar(name: str, value: int, min_value: int, max_value: int, line_len: int, bar_symbol: str) -> str:
    if value >= min_value and (max_value - min_value) > 0:
        header = '{:>3}: {:>5d} {}'.format(name, value, bar_symbol)
        bar_len = int((line_len - len(header)) * (value - min_value) / (max_value - min_value))
        text = '\n{}{}'.format(header, bar_symbol * bar_len)
        return text
    return ''


def create_progress_bars(char: Character, line_size: int) -> str:
    text = ''

    # Damage per round
    caused_dpr = char.stats_storage.caused_dpr
    dpr = caused_dpr.last_dpr
    if caused_dpr.max_dpr and dpr:
        ts = get_ts()
        duration_without_attack = ts - caused_dpr.ts_last_dpr
        if duration_without_attack <= ROUND_DURATION:
            dpr = int(dpr * (ROUND_DURATION - duration_without_attack) / ROUND_DURATION)
            if dpr:
                text += print_progress_bar('DPR', dpr, 0, caused_dpr.max_dpr, line_size, '\u2591')

    # Knockdown cooldown
    last_kd = char.last_knockdown
    value = last_kd.get_cooldown()
    if value:
        bar_symbol = '\u2596'
        if last_kd.s_attack.is_success():
            bar_symbol = '\u259e'
        text += print_progress_bar('KD', value, 0, KNOCKDOWN_PVE_CD, line_size, bar_symbol)

    # Stunning fist duration
    for sf in reversed(char.stunning_fist_list):
        value = sf.get_duration()
        if value:
            text += print_progress_bar('SF', value, 0, STUNNING_FIST_DURATION, line_size, '\u2588')  # full bar
            break

    # Stealth mode cooldown
    value = char.stealth_cooldown.get_duration()
    if value:
        text += print_progress_bar('SMC', value, 0, STEALTH_MODE_CD, line_size, '\u2592')

    # Attacks min/max
    ab_attack_list = char.ab_attack_list
    if ab_attack_list:
        last_ab = char.get_last_ab_attack()
        if get_ts() - last_ab.timestamp <= 6000:
            max_ab = char.get_max_ab_attack_base()
            min_ab = char.get_min_ab_attack_base()
            text += print_progress_bar('AB', last_ab.base, min_ab, max_ab, line_size, '\u2584')

    return text


def print_special_char(char: Character) -> list:
    text = []

    last_kd = char.last_knockdown
    last_sf = char.stunning_fist_list[-1] if char.stunning_fist_list else None

    if not last_sf or last_kd.timestamp > last_sf.timestamp:
        text.append('KD: {:d}({})'.format(last_kd.s_attack.value, last_kd.s_attack.result))
    elif last_sf:
        dc = last_sf.throw.dc if last_sf.throw else 0
        text.append('SF: {:d}({:d}/{})'.format(last_sf.s_attack.value, dc, last_sf.s_attack.result))
    return text


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
                break

        # for attack in self.player.ac_attack_list:
        #     if char.name == attack.attacker_name:
        #         last_player_contact_ts = max(last_player_contact_ts, attack.timestamp)
        #
        # action = self.player.last_hit_ac_attack
        # if action and char.name == action.attacker_name:
        #     last_player_contact_ts = max(last_player_contact_ts, action.timestamp)
        #
        # action = self.player.last_received_damage
        # if action and action.damager_name == char.name:
        #     last_player_contact_ts = max(last_player_contact_ts, action.timestamp)
        #
        # action = self.player.last_caused_damage
        # if action and action.target_name == char.name:
        #     last_player_contact_ts = max(last_player_contact_ts, action.timestamp)

        return last_player_contact_ts


class Printer:
    def __init__(self):
        self.chars_to_print: typing.List[Character] = []
        self.chars_to_print_ts = 0
        self.wide_mode = False

    def change_print_mode(self):
        self.wide_mode = not self.wide_mode

    def print_char_wide_stat(self, char: Character) -> list:
        storage = char.stats_storage
        all_stats = storage.all_chars_stats

        stats = storage.char_stats
        sum_cd = stats[char.last_caused_damage.target_name].caused_damage.sum
        last_cd = char.last_caused_damage.value

        hit_ab_attack = all_stats.hit_ab_attack
        per_ab = hit_ab_attack.count / hit_ab_attack.sum if hit_ab_attack.sum else 0

        caused_damage = all_stats.caused_damage
        avg_caused_damage = caused_damage.sum / caused_damage.count if caused_damage.count else 0

        return [
            'CD: {}({})'.format(convert_damage(sum_cd), convert_damage(last_cd)),
            'DPR: {}({})'.format(
                convert_damage(storage.caused_dpr.max_dpr), convert_damage(storage.caused_dpr.last_dpr)),
            'PER AB: {:d}%'.format(int(per_ab * 100)),
            'AVG CD: {:d}'.format(int(avg_caused_damage)),
        ]

    def print_char_without_name(self, char: Character) -> list:
        max_ac = char.get_max_miss_ac()
        min_ac = char.get_min_hit_ac()
        cur_hp = char.get_avg_hp() - char.get_received_damage_sum() + char.stats_storage.healed_points

        stats = char.stats_storage.char_stats
        sum_rd = stats[char.last_received_damage.damager_name].received_damage.sum
        last_rd = char.last_received_damage.value
        last_ad = sum([ad.value for ad in char.last_received_damage.damage_absorption_list])

        result = [
            'HP: {}/{}'.format(convert_damage(cur_hp), convert_damage(char.get_avg_hp())),
            'AC: {:d}/{:d}({:d})'.format(max_ac, min_ac, char.get_last_hit_ac_attack_value()),
            'AB: {:d}({:d})'.format(char.get_max_ab_attack_base(), char.get_last_ab_attack_base()),
            'FT: {:d}({:d})'.format(char.fortitude, char.last_fortitude_dc),
            'WL: {:d}({:d})'.format(char.will, char.last_will_dc),
            'RD: {}({}/{})'.format(convert_damage(sum_rd), convert_damage(last_rd), last_ad),
        ]

        if self.wide_mode:
            result += self.print_char_wide_stat(char)

        return result

    def print_char(self, char: Character) -> list:
        name = char.name
        if char.experience:
            name = '{} ({:d})'.format(name, char.experience.value)
        return [name] + self.print_char_without_name(char)

    def print(self, player: Character, chars: typing.List[Character]) -> str:
        ts = get_ts()
        if self.wide_mode and ts - self.chars_to_print_ts > CHARS_TO_PRINT_TIMEOUT:
            chars_without_player = [char for char in chars if char is not player]
            chars_without_player.sort(key=lambda x: x.timestamp, reverse=True)

            self.chars_to_print = chars_without_player[:CHARS_COUNT_WIDE_MODE]
            self.chars_to_print.sort(key=lambda x: x.name)
            self.chars_to_print_ts = ts
        else:
            last_player_ab = player.get_last_ab_attack()
            if last_player_ab:
                self.chars_to_print = [char for char in chars if char.name == last_player_ab.target_name]
            else:
                self.chars_to_print = chars[0:1]

        table = [self.print_char(char) for char in self.chars_to_print]
        player_special = ['{}\n'.format(' | '.join(print_special_char(player)))]
        table.append(player_special + self.print_char_without_name(player))

        df = pandas.DataFrame(table)
        text = str(tabulate.tabulate(df, tablefmt='plain', showindex=False))

        line_size = len(text.splitlines()[0])
        text += create_progress_bars(player, line_size)

        if self.wide_mode:
            text = '{}\n'.format('#' * line_size) + text
            text += '\n{}'.format('#' * line_size)

        return text