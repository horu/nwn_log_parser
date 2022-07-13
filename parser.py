import collections
from tabulate import tabulate
import pandas
import tabulate

from printer import *

CHARS_TO_PRINT_LIMIT_NORM = 2
CHARS_TO_PRINT_LIMIT_MAX = 30
CHARS_TO_PRINT_TIMEOUT = 3000


class Parser:
    def __init__(self):
        self.characters = collections.defaultdict(Character)
        self.player = Character()
        self.printer = Printer()

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
            attacker.start_fight(attack)
            attacker.add_ab(attack)

            target = self.get_char(attack.target_name)
            target.add_ac(attack)
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
            attacker.start_fight(s_attack)
            if KNOCKDOWN in s_attack.type:
                attacker.last_knockdown = s_attack
            elif STUNNING_FIST in s_attack.type:
                attacker.add_stunning_fist(StunningFirst(s_attack))
            return

        damage = Damage.create(line)
        if damage:
            damager = self.get_char(damage.damager_name)
            target = self.get_char(damage.target_name)

            # for player only
            # if damager is self.player or target is self.player:
            damager.add_caused_damage(damage)
            target.add_received_damage(damage)
            return

        death = Death.create(line)
        if death:
            target = self.get_char(death.target_name)
            if target is not self.player:
                target.on_killed(death)
                self.player.on_killed(death)
            return

        d_reduction = DamageReduction.create(line)
        if d_reduction:
            target = self.get_char(d_reduction.target_name)
            target.add_damage_absorption(d_reduction)
            return

        d_resistance = DamageResistance.create(line)
        if d_resistance:
            target = self.get_char(d_resistance.target_name)
            target.add_damage_absorption(d_resistance)
            return

        d_immunity = DamageImmunity.create(line)
        if d_immunity:
            target = self.get_char(d_immunity.target_name)
            target.add_damage_absorption(d_immunity)
            return

        stealth_cooldown = StealthCooldown.create(line)
        if stealth_cooldown:
            self.player.stealth_cooldown = stealth_cooldown
            return

        initiative_roll = InitiativeRoll.create(line)
        if initiative_roll:
            roller = self.get_char(initiative_roll.roller_name)
            roller.initiative_roll = initiative_roll
            # find player name by Initiative Roll
            self.player = roller
            return

    def reset_statistic(self):
        for char in self.characters.values():
            char.stats_storage = StatisticStorage()

    def change_print_mode(self):
        self.printer.change_print_mode()

    def print(self) -> str:
        chars = [char for char in self.characters.values()]
        text = self.printer.print(self.player, chars)
        return text