import pandas
import tabulate

from parser import *
from ui import UserInterface
from ui_char import CharacterStat


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
        self.ui.target_hp_bar.upgrade(target.name, cur_hp, min_hp, max_hp)

    def update_player_hp_bar(self, player: Character) -> None:
        max_hp = max(1, player.get_avg_hp())
        cur_hp = player.get_cur_hp()
        min_hp = min(cur_hp, 0)
        if cur_hp and cur_hp / max_hp < LOW_HP_NOTIFY_LIMIT:
            self.ui.notify_low_hp(True)
        else:
            self.ui.notify_low_hp(False)

        self.ui.player_hp_bar.upgrade(player.name, cur_hp, min_hp, max_hp)

    def update_dpr_bar(self, char: Character) -> None:
        # Damage per round
        caused_dpr = char.stats_storage.caused_dpr
        self.ui.attack_damage_bar.update_dps(caused_dpr.last_dpr, caused_dpr.max_dpr, caused_dpr.last_dpr_ts)

    def update_attack_base_bar(self, char: Character) -> None:
        # Attacks min/max
        last_ab = char.get_last_ab_attack()
        if last_ab:
            max_ab = char.get_max_ab_attack_base()
            min_ab = char.get_min_ab_attack_base()
            self.ui.attack_damage_bar.update_attack(last_ab.base, min_ab, max_ab, last_ab.timestamp)

    def update_knockdown_bar(self, char: Character) -> None:
        # Knockdown cooldown
        last_kd = char.last_knockdown
        if last_kd.s_attack.is_success():
            self.ui.knockdown_bar.update_timestamp(last_kd.timestamp)
            self.ui.knockdown_miss_bar.update_timestamp(0)
        else:
            self.ui.knockdown_bar.update_timestamp(0)
            self.ui.knockdown_miss_bar.update_timestamp(last_kd.timestamp)
        return

    def update_stunning_fist_bar(self, char: Character) -> None:
        # Stunning fist duration
        for sf in reversed(char.stunning_fist_list):
            if sf.is_success():
                self.ui.stunning_fist_bar.update_timestamp(sf.timestamp)
                break

    def update_stealth_mode_cd_bar(self, player: Player) -> None:
        # Stealth mode cooldown
        sm_cd = player.stealth_cooldown
        self.ui.stealth_cooldown_bar.update(sm_cd.cooldown, sm_cd.timestamp)

    def update_casting_bar(self, char: Character) -> None:
        casting = char.casting_spell
        if casting:
            self.ui.casting_bar.update(casting.spell_name, casting.timestamp)
        else:
            self.ui.casting_bar.update('', 0)

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
        for char in chars:
            if char.name == player.get_target_name():
                target = char
                break

        self.update_player_hp_bar(player)
        self.update_char_stat(self.ui.player_stat, player)
        self.update_target_hp_bar(target)
        self.update_char_stat(self.ui.target_stat, target)

        for action in parser.pop_actions():
            action_type = action.get_type()
            if action_type == Damage:
                self.update_dpr_bar(player)
            elif action_type == Attack:
                self.update_attack_base_bar(player)
                self.update_stealth_mode_cd_bar(player)
            elif action_type == SpecialAttack:
                self.update_knockdown_bar(player)
                self.update_stealth_mode_cd_bar(player)
            elif action_type == SavingThrow:
                self.update_stunning_fist_bar(player)
            elif action_type == StealthCooldown:
                self.update_stealth_mode_cd_bar(player)
            elif action_type == CastBegin or action_type == CastEnd or action_type == CastInterruption:
                self.update_casting_bar(player)
