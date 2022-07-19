import pandas
import tabulate

from parser import *
from ui import *


CHARS_COUNT_WIDE_MODE = 30
CHARS_TO_PRINT_TIMEOUT = 5000
DAMAGE_PRINT_LIMIT = 1000
LOW_HP_NOTIFY_LIMIT = 0.3


def convert_damage(value: int) -> str:
    if abs(value) > DAMAGE_PRINT_LIMIT:
        return '{:.1f}'.format(value / DAMAGE_PRINT_LIMIT)
    return str(value)


def print_wide_char(char: Character) -> list:
    storage = char.stats_storage

    max_ac = char.get_max_miss_ac()
    min_ac = char.get_min_hit_ac()

    stats = char.stats_storage.char_stats
    sum_rd = stats[char.last_received_damage.damager_name].received_damage.sum
    last_rd = char.last_received_damage.value
    last_ad = sum([ad.value for ad in char.last_received_damage.damage_absorption_list])

    sum_cd = stats[char.last_caused_damage.target_name].caused_damage.sum
    last_cd = char.last_caused_damage.value

    all_stats = storage.all_chars_stats
    hit_ab_attack = all_stats.hit_ab_attack
    per_ab = hit_ab_attack.count / hit_ab_attack.sum if hit_ab_attack.sum else 0

    caused_damage = all_stats.caused_damage
    avg_caused_damage = caused_damage.sum / caused_damage.count if caused_damage.count else 0

    result = [
        char.name,
        'HP: {}/{}'.format(convert_damage(char.get_cur_hp()), convert_damage(char.get_avg_hp())),
        'AC: {:d}/{:d}({:d})'.format(max_ac, min_ac, char.get_last_hit_ac_attack_value()),
        'AB: {:d}({:d})'.format(char.get_max_ab_attack_base(), char.get_last_ab_attack_base()),
        'FT: {:d}({:d})'.format(char.fortitude, char.last_fortitude_dc),
        'WL: {:d}({:d})'.format(char.will, char.last_will_dc),
        'RD: {}({}/{})'.format(convert_damage(sum_rd), convert_damage(last_rd), last_ad),
        'CD: {}({})'.format(convert_damage(sum_cd), convert_damage(last_cd)),
        'DPR: {}({})'.format(
            convert_damage(storage.caused_dpr.max_dpr), convert_damage(storage.caused_dpr.last_dpr)),
        'PER AB: {:d}%'.format(int(per_ab * 100)),
        'AVG CD: {:d}'.format(int(avg_caused_damage)),
    ]

    last_kd = char.last_knockdown
    last_sf = char.stunning_fist_list[-1] if char.stunning_fist_list else None

    if not last_sf or last_kd.timestamp > last_sf.timestamp:
        result.append('KD: {:d}({})'.format(last_kd.s_attack.value, last_kd.s_attack.result))
    elif last_sf:
        dc = last_sf.throw.dc if last_sf.throw else 0
        result.append('SF: {:d}({:d}/{})'.format(last_sf.s_attack.value, dc, last_sf.s_attack.result))

    return result


class WidePrinter:
    def __init__(self):
        self.chars_to_print: typing.List[Character] = []
        self.chars_to_print_ts = 0

    def print_wide(self, parser: Parser) -> str:
        player = parser.player
        chars = [char for char in parser.characters.values()]

        ts = get_ts()
        if ts - self.chars_to_print_ts > CHARS_TO_PRINT_TIMEOUT:
            chars_without_player = [char for char in chars if char is not player]
            chars_without_player.sort(key=lambda x: x.timestamp, reverse=True)

            self.chars_to_print = chars_without_player[:CHARS_COUNT_WIDE_MODE]
            self.chars_to_print.sort(key=lambda x: x.name)
            self.chars_to_print_ts = ts

        table = [print_wide_char(char) for char in self.chars_to_print]

        df = pandas.DataFrame(table)
        text = str(tabulate.tabulate(df, tablefmt='plain', showindex=False))

        line_size = len(text.splitlines()[0])
        text = '{}\n'.format('#' * line_size) + text
        text += '\n{}'.format('#' * line_size)

        return text


class Printer:
    def __init__(self, ui: UserInterface):
        self.ui = ui
        self.wide_mode = False
        self.wide_printer = WidePrinter()

    def update_target_hp_bar(self, target: Character) -> None:
        max_hp = max(1, target.get_avg_hp())
        cur_hp = target.get_cur_hp()
        min_hp = min(cur_hp, 0)
        # self.ui.upgrade_hp_progress_bar(ProgressBarType.TARGET_HP, target.name, max_hp - cur_hp, 0, max_hp)
        self.ui.upgrade_hp_progress_bar(ProgressBarType.TARGET_HP, target.name, cur_hp, min_hp, max_hp)

    def update_player_hp_bar(self, player: Character) -> None:
        max_hp = max(1, player.get_avg_hp())
        cur_hp = player.get_cur_hp()
        min_hp = min(cur_hp, 0)
        if cur_hp and cur_hp / max_hp < LOW_HP_NOTIFY_LIMIT:
            self.ui.notify_low_hp(True)
        else:
            self.ui.notify_low_hp(False)

        # self.ui.upgrade_hp_progress_bar(ProgressBarType.PLAYER_HP, player.name, max_hp - cur_hp, 0, max_hp)
        self.ui.upgrade_hp_progress_bar(ProgressBarType.PLAYER_HP, player.name, cur_hp, min_hp, max_hp)

    def update_dpr_bar(self, char: Character) -> None:
        # Damage per round
        caused_dpr = char.stats_storage.caused_dpr
        dpr = caused_dpr.last_dpr
        if caused_dpr.max_dpr and dpr:
            ts = get_ts()
            duration_without_attack = ts - caused_dpr.ts_last_dpr
            if duration_without_attack <= ROUND_DURATION:
                dpr = int(dpr * (ROUND_DURATION - duration_without_attack) / ROUND_DURATION)
                if dpr:
                    self.ui.upgrade_progress_bar(ProgressBarType.DAMAGE_PER_ROUND, dpr, 0, caused_dpr.max_dpr)
                    return
        self.ui.set_complete_progress_bar(ProgressBarType.DAMAGE_PER_ROUND)

    def update_knockdown_bar(self, char: Character) -> None:
        # Knockdown cooldown
        last_kd = char.last_knockdown
        value = last_kd.get_cooldown()
        if value:
            if last_kd.s_attack.is_success():
                self.ui.upgrade_progress_bar(ProgressBarType.KNOCKDOWN, value)
            else:
                self.ui.upgrade_progress_bar(ProgressBarType.KNOCKDOWN_MISS, value)
            return
        self.ui.set_complete_progress_bar(ProgressBarType.KNOCKDOWN)
        self.ui.set_complete_progress_bar(ProgressBarType.KNOCKDOWN_MISS)

    def update_stunning_fist_bar(self, char: Character) -> None:
        # Stunning fist duration
        for sf in reversed(char.stunning_fist_list):
            value = sf.get_duration()
            if value:
                self.ui.upgrade_progress_bar(ProgressBarType.STUNNING_FIST, value)
                return
        self.ui.set_complete_progress_bar(ProgressBarType.STUNNING_FIST)

    def update_stealth_mode_cd_bar(self, player: Player) -> None:
        # Stealth mode cooldown
        value = player.stealth_cooldown.get_duration()
        if value:
            self.ui.upgrade_progress_bar(ProgressBarType.STEALTH_MODE_CD, value)
            return
        self.ui.set_complete_progress_bar(ProgressBarType.STEALTH_MODE_CD)

    def update_attack_base_bar(self, char: Character) -> None:
        # Attacks min/max
        ab_attack_list = char.ab_attack_list
        if ab_attack_list:
            last_ab = char.get_last_ab_attack()
            if get_ts() - last_ab.timestamp <= 6000:
                max_ab = char.get_max_ab_attack_base()
                min_ab = char.get_min_ab_attack_base()
                self.ui.upgrade_progress_bar(ProgressBarType.ATTACK_BASE, last_ab.base, min_ab, max_ab)
                return
        self.ui.set_complete_progress_bar(ProgressBarType.ATTACK_BASE)

    def update_casting_bar(self, char: Character) -> None:
        casting = char.casting_spell
        if casting:
            channeling = CAST_TIME - (get_ts() - casting.timestamp)
            if channeling >= 0:
                self.ui.upgrade_casting_progress_bar(casting.spell_name, channeling)
                return
        self.ui.set_complete_progress_bar(ProgressBarType.CASTING_SPELL)

    def update_buffs_bar(self, player: Player) -> None:
        buffs = player.buff_dict
        for name, buff in buffs.items():
            if buff:
                duration = buff.duration - (get_ts() - buff.timestamp)
                if duration >= 0:
                    self.ui.upgrade_buff_progress_bar(name, duration, 0, buff.duration, Visible.VISIBLE)
                    continue
            self.ui.upgrade_buff_progress_bar(name, 0, 0, 1, Visible.INVISIBLE)

    def change_print_mode(self):
        self.wide_mode = not self.wide_mode
        self.wide_printer.chars_to_print_ts = 0

    def update_char_stat(self, stat: CharacterStat, char: Character) -> None:
        sum_rd = char.stats_storage.char_stats[char.last_received_damage.damager_name].received_damage.sum
        last_rd = char.last_received_damage.value
        last_ad = sum([ad.value for ad in char.last_received_damage.damage_absorption_list])

        stat.set_ac(char.get_max_miss_ac(), char.get_min_hit_ac(), char.get_last_hit_ac_attack_value())
        stat.set_ab(char.get_max_ab_attack_base(), char.get_last_ab_attack_base())
        stat.set_saving_throw(FORTITUDE, char.fortitude, char.last_fortitude_dc)
        stat.set_saving_throw(WILL, char.will, char.last_will_dc)
        stat.set_received_damage(sum_rd, last_rd, last_ad)
        stat.set_experience(char.get_experience_value())

        last_kd = char.last_knockdown
        last_sf = char.stunning_fist_list[-1] if char.stunning_fist_list else None
        if not last_sf or last_kd.timestamp > last_sf.timestamp:
            dc = last_kd.s_attack.value
            stat.set_special_attack(SHORT_KNOCKDOWN, last_kd.s_attack.value, dc, last_kd.s_attack.result)
        elif last_sf:
            dc = last_sf.throw.dc if last_sf.throw else 0
            stat.set_special_attack(SHORT_STUNNING_FIST, last_sf.s_attack.value, dc, last_sf.s_attack.result)

    def print(self, parser: Parser) -> None:
        if self.wide_mode:
            # old mode
            text = self.wide_printer.print_wide(parser)
            self.ui.set_main_label_text(text, True)
            return
        # gui mode
        self.ui.set_main_label_text('', False)

        player = parser.player
        chars = [char for char in parser.characters.values()]

        target = chars[0]
        last_player_ab = player.get_last_ab_attack()
        if last_player_ab:
            target = [char for char in chars if char.name == last_player_ab.target_name][0]

        self.update_target_hp_bar(target)
        self.update_char_stat(self.ui.target_stat, target)
        self.update_char_stat(self.ui.player_stat, player)

        self.update_player_hp_bar(player)
        self.update_dpr_bar(player)
        self.update_knockdown_bar(player)
        self.update_stunning_fist_bar(player)
        self.update_stealth_mode_cd_bar(player)
        self.update_attack_base_bar(player)
        self.update_casting_bar(player)
        self.update_buffs_bar(player)
