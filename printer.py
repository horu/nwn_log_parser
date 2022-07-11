
from char import *


def print_progress_bar(name: str, value: int, min_value: int, max_value: int, line_len: int, bar_sym: str) -> str:
    if value >= min_value and (max_value - min_value) > 0:
        header = '{}: {:>5d} '.format(name, value)
        bar_len = int((line_len - len(header)) * (value - min_value) / (max_value - min_value))
        text = '\n{}{}'.format(header, bar_sym * bar_len)
        return text
    return ''


def create_progress_bars(char: Character, line_size: int) -> str:
    text = ''

    # Knockdown cooldown
    last_kd = char.last_knockdown
    if last_kd:
        value = KNOCKDOWN_PVE_CD - (get_ts() - last_kd.timestamp)
        text += print_progress_bar('KD', value, 0, KNOCKDOWN_PVE_CD, line_size, '=')

    # Stuning fist duration
    last_sf = char.last_stunning_fist
    if last_sf and last_sf.throw and last_sf.throw.result == FAILURE:
        value = STUNNING_FIST_DURATION - (get_ts() - last_sf.s_attack.timestamp)
        text += print_progress_bar('SF', value, 0, STUNNING_FIST_DURATION, line_size, '*')

    # Stealth mode cooldown
    last_sm = char.stealth_mode
    if last_sm:
        value = last_sm.cooldown - 1000 - (get_ts() - last_sm.timestamp)  # 1000 - поправка на сервер
        text += print_progress_bar('SM', value, 0, STEALTH_MODE_CD, line_size, '+')

    # Attacks min/max
    ab_list = char.ab_list
    if ab_list and (get_ts() - ab_list[-1].timestamp) <= 6000:
        max_ab = char.get_max_ab_attack_base()
        min_ab = char.get_min_ab_attack_base()
        last_ab = char.get_last_ab_attack_base()
        text += print_progress_bar('AB', last_ab, min_ab, max_ab, line_size, '|')

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
    cd = char.get_caused_damage()
    rd = char.get_received_damage()
    return [
        'AC: {:d}/{:d}({:d})'.format(char.ac[0], char.ac[1], char.get_last_ac_attack_value()),
        'AB: {:d}({:d})'.format(char.get_max_ab_attack_base(), char.get_last_ab_attack_base()),
        'FT: {:d}({:d})'.format(char.fortitude, char.last_fortitude_dc),
        'WL: {:d}({:d})'.format(char.will, char.last_will_dc),
        'CD: {:d}({:d})'.format(cd[0], cd[1]),
        'RD: {:d}({:d}/{:d}/{:d})'.format(rd[0], rd[1], rd[2], rd[3]),
    ]

def print_char(char: Character) -> list:
    return [char.name] + print_char_without_name(char)
