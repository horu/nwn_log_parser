from char import *

EXPERIENCE_TIMEOUT = 2000


class Parser:
    def __init__(self):
        self.characters = collections.defaultdict(Character)
        self.player = Player()

        self.experience_list: typing.List[Experience] = []

    def get_char(self, name: str) -> Character:
        char = self.characters[name]
        char.name = name
        char.update_timestamp()
        return char

    def push_line(self, line) -> None:
        logging.debug('LINE: {}'.format(line[0:-1]))
        action: Attack = Attack.create(line)
        if action:
            if action.attacker_name == self.player.name:
                self.player.start_fight(action)

            attacker = self.get_char(action.attacker_name)
            attacker.add_ab(action)

            target = self.get_char(action.target_name)
            target.add_ac(action)
            return

        action: SavingThrow = SavingThrow.create(line)
        if action:
            target = self.get_char(action.target_name)
            if FORTITUDE in action.type:
                target.fortitude = action.base
                target.last_fortitude_dc = action.dc
                # try to check features the player raised
                self.player.on_fortitude_save(action)

            elif WILL in action.type:
                target.will = action.base
                target.last_will_dc = action.dc
            return

        action: SpecialAttack = SpecialAttack.create(line)
        if action:
            if action.attacker_name == self.player.name:
                self.player.start_fight(action)

            attacker = self.get_char(action.attacker_name)
            if KNOCKDOWN in action.type:
                attacker.last_knockdown = Knockdown(action)
            elif STUNNING_FIST in action.type:
                attacker.add_stunning_fist(StunningFirst(action))

            target = self.get_char(action.target_name)
            target.add_ac(action)
            return

        action: Damage = Damage.create(line)
        if action:
            damager = self.get_char(action.damager_name)
            target = self.get_char(action.target_name)

            # for player only
            # if damager is self.player or target is self.player:
            damager.add_caused_damage(action)
            target.add_received_damage(action)
            return

        action: Death = Death.create(line)
        if action:
            target = self.get_char(action.target_name)
            target.on_killed(action)
            if self.experience_list:
                target.experience = self.experience_list.pop(0)
            return

        action: DamageReduction = DamageReduction.create(line)
        if action:
            target = self.get_char(action.target_name)
            target.add_damage_absorption(action)
            return

        action: DamageResistance = DamageResistance.create(line)
        if action:
            target = self.get_char(action.target_name)
            target.add_damage_absorption(action)
            return

        action: DamageImmunity = DamageImmunity.create(line)
        if action:
            target = self.get_char(action.target_name)
            target.add_damage_absorption(action)
            return

        action: StealthCooldown = StealthCooldown.create(line)
        if action:
            self.player.stealth_cooldown = action
            return

        action: InitiativeRoll = InitiativeRoll.create(line)
        if action:
            self._detect_player(action.roller_name)
            self.player.initiative_roll = action
            return

        action: Usage = Usage.create(line)
        if action:
            user = self.get_char(action.user_name)
            if action.item == ITEM_POTION_OF_HEAL and user != self.player:
                # for user we get Heal action
                user.healed_points += user.sum_received_damage
            return
        
        action: Heal = Heal.create(line)
        if action:
            self._detect_player(action.target_name)
            target = self.get_char(action.target_name)
            target.healed_points += action.value
            assert target == self.player
            return

        action: Experience = Experience.create(line)
        if action:
            append_fix_time_window(self.experience_list, action, EXPERIENCE_TIMEOUT)
            return

        action: Resting = Resting.create(line)
        if action:
            self.player.sum_received_damage = 0
            self.player.healed_points = 0
            return

    def _detect_player(self, name: str):
        # find player name by InitiativeRoll and Heal
        if self.player.name != name:
            self.characters.clear()
            self.player = Player()
            self.player.name = name
            self.player.hp_list = [PLAYER_HP]
            self.characters[name] = self.player

    def reset_statistic(self):
        for char in self.characters.values():
            char.stats_storage = StatisticStorage()