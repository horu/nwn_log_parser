import collections
from tabulate import tabulate
import pandas
import tabulate

from printer import *

CHARS_TO_PRINT_LIMIT_NORM = 2
CHARS_TO_PRINT_LIMIT_MAX = 30
CHARS_TO_PRINT_TIMEOUT = 3000


class Parser:
    def __init__(self, player_name: str):
        self.characters = collections.defaultdict(Character)
        self.player = self.get_char(player_name)
        self.chars_to_print: typing.List[Character] = []
        self.chars_to_print_ts = 0
        self.chars_to_print_limit = CHARS_TO_PRINT_LIMIT_NORM

    def get_char(self, name: str) -> Character:
        char = self.characters[name]
        char.name = name
        char.update_timestamp()
        return char

    def push_line(self, line) -> None:
        logging.debug(line)
        attack = Attack.create(line)
        if attack:
            attacker = self.get_char(attack.attacker_name)
            attacker.update_ab(attack)
            attacker.start_fight()

            target = self.get_char(attack.target_name)
            target.update_ac(attack)
            return

        throw = SavingThrow.create(line)
        if throw:
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
            attacker = self.get_char(s_attack.attacker_name)
            attacker.start_fight()
            if KNOCKDOWN in s_attack.type:
                attacker.last_knockdown = s_attack
            elif STUNNING_FIST in s_attack.type:
                attacker.add_stunning_fist(StunningFirst(s_attack))
            return

        damage = Damage.create(line)
        if damage:
            damager = self.get_char(damage.damager_name)
            target = self.get_char(damage.target_name)

            if damager is self.player or target is self.player:
                damager.add_caused_damage(damage)
                target.add_received_damage(damage)
            return

        death = Death.create(line)
        if death:
            target = self.get_char(death.target_name)
            target.on_killed(death)
            self.player.on_killed(death)
            return

        d_reduction = DamageReduction.create(line)
        if d_reduction:
            target = self.get_char(d_reduction.target_name)
            target.on_damage_reduction(d_reduction)
            return

        d_resistance = DamageResistance.create(line)
        if d_resistance:
            target = self.get_char(d_resistance.target_name)
            target.on_damage_resistance(d_resistance)
            return

        stealth_cooldown = StealthCooldown.create(line)
        if stealth_cooldown:
            self.player.stealth_cooldown = stealth_cooldown
            return

        initiative_roll = InitiativeRoll.create(line)
        if initiative_roll:
            roller = self.get_char(initiative_roll.roller_name)
            roller.initiative_roll = initiative_roll
            return

    def sort_char(self, char: Character) -> int:
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

    def change_char_list(self):
        if self.chars_to_print_limit == CHARS_TO_PRINT_LIMIT_NORM:
            self.chars_to_print_limit = CHARS_TO_PRINT_LIMIT_MAX
        else:
            self.chars_to_print_limit = CHARS_TO_PRINT_LIMIT_NORM
        self.chars_to_print_ts = 0

    def get_stat(self) -> str:
        ts = get_ts()
        if ts - self.chars_to_print_ts > CHARS_TO_PRINT_TIMEOUT:
            chars = [char for char in self.characters.values() if char is not self.player]
            chars.sort(key=lambda x: x.timestamp, reverse=True)
            chars.sort(key=self.sort_char, reverse=True)
            self.chars_to_print = chars[:self.chars_to_print_limit]
            self.chars_to_print.sort(key=lambda x: x.name)
            self.chars_to_print_ts = ts

        table = [print_char(char) for char in self.chars_to_print]
        table.append(['{}\n'.format(' | '.join(print_special_char(self.player)))]
                     + print_char_without_name(self.player))

        df = pandas.DataFrame(table)
        text = str(tabulate.tabulate(df, tablefmt='plain', showindex=False))

        line_size = len(text.splitlines()[0])
        text += create_progress_bars(self.player, line_size)

        if self.chars_to_print_limit > CHARS_TO_PRINT_LIMIT_NORM:
            text = '{}\n'.format('#' * line_size) + text
            text += '\n{}'.format('#' * line_size)

        return text