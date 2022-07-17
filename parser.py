from char import *

EXPERIENCE_TIMEOUT = 2000


class Parser:
    def __init__(self):
        self.characters = collections.defaultdict(Character)
        self.player = Player()

        self.experience_list: typing.List[Experience] = []
        self.round_ts = 0

    def get_char(self, name: str) -> Character:
        char = self.characters[name]
        char.name = name
        char.update_timestamp()
        return char

    def push_line(self, line) -> None:
        logging.debug('LINE: {}'.format(line[0:-1]))
        ts = get_ts()
        if ts - self.round_ts >= ROUND_DURATION:
            # every round teak
            self.round_ts = ts
            # if no heal for 2 rounds then full hp
            # DELETE THIS SHIT.
            # To fix bug with real hp
            if ts - self.player.last_heal.timestamp > ROUND_DURATION * 2 and self.player.sum_received_damage:
                self.player.reset_damage()

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
            experience = self.experience_list.pop(0) if self.experience_list else None
            target.on_killed(action, experience)
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
                user.reset_damage()
            return
        
        action: Heal = Heal.create(line)
        if action:
            self._detect_player(action.target_name)
            self.player.add_heal(action)
            return

        action: Experience = Experience.create(line)
        if action:
            append_fix_time_window(self.experience_list, action, EXPERIENCE_TIMEOUT)
            return

        action: Resting = Resting.create(line)
        if action:
            self.player.reset_damage()
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